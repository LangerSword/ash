//! The board's only network egress: a tiny allow-listed relay on 127.0.0.1:9001.
//!
//! The board's container cannot do TLS, so its Python app POSTs {url, method,
//! headers, body} here over `adb reverse`, and this process performs the request.
//! Without it every ambiguous event fails closed and wipes, which is correct but
//! makes the product unusable — so the desktop app owns it.

use std::io::Read;
use std::time::Duration;

use crate::config;

const ALLOW: [&str; 3] = [
    "router-api.0g.ai",
    "developer.world.org",
    "testnet.mirrornode.hedera.com",
];

fn host_of(url: &str) -> String {
    url.split("//")
        .nth(1)
        .unwrap_or("")
        .split('/')
        .next()
        .unwrap_or("")
        .split(':')
        .next()
        .unwrap_or("")
        .to_string()
}

fn allowed(host: &str) -> bool {
    ALLOW
        .iter()
        .any(|a| host == *a || host.ends_with(&format!(".{a}")))
}

fn handle(body: &str) -> (u16, String) {
    let env: serde_json::Value = match serde_json::from_str(body) {
        Ok(v) => v,
        Err(_) => return (400, r#"{"error":"bad_json"}"#.to_string()),
    };
    let url = env.get("url").and_then(|v| v.as_str()).unwrap_or("");
    let host = host_of(url);
    if !allowed(&host) {
        return (403, serde_json::json!({ "error": format!("host not allowed: {host}") }).to_string());
    }
    let method = env.get("method").and_then(|v| v.as_str()).unwrap_or("POST");
    let payload = env.get("body").and_then(|v| v.as_str()).unwrap_or("");

    let req = ureq::request(method, url).timeout(Duration::from_secs(30));
    let req = match env.get("headers").and_then(|v| v.as_object()) {
        Some(h) => h.iter().fold(req, |r, (k, v)| r.set(k, v.as_str().unwrap_or(""))),
        None => req,
    };

    let result = if payload.is_empty() {
        req.call()
    } else {
        req.send_string(payload)
    };

    let (status, text) = match result {
        Ok(r) => (r.status(), r.into_string().unwrap_or_default()),
        Err(ureq::Error::Status(code, r)) => (code, r.into_string().unwrap_or_default()),
        Err(e) => return (502, serde_json::json!({ "error": format!("{e}") }).to_string()),
    };
    (200, serde_json::json!({ "status": status, "body": text }).to_string())
}

/// Start the relay if the port is free. Returns whether this process owns it.
pub fn start(port: u16) -> bool {
    let addr = format!("0.0.0.0:{port}");
    let server = match tiny_http::Server::http(&addr) {
        Ok(s) => s,
        Err(e) => {
            config::log_line(&format!("relay: not started on {addr} · {e}"));
            return false;
        }
    };
    config::log_line(&format!("relay: listening on {addr}"));
    std::thread::spawn(move || {
        for mut req in server.incoming_requests() {
            let mut body = String::new();
            let _ = req.as_reader().take(1 << 20).read_to_string(&mut body);
            let (code, reply) = if req.url() == "/healthz" {
                (200, serde_json::json!({ "ok": true, "allow": ALLOW }).to_string())
            } else if req.method().as_str() == "POST" && req.url() == "/relay" {
                handle(&body)
            } else {
                (404, r#"{"error":"not_found"}"#.to_string())
            };
            let header = tiny_http::Header::from_bytes(&b"Content-Type"[..], &b"application/json"[..])
                .expect("static header");
            let _ = req.respond(
                tiny_http::Response::from_string(reply)
                    .with_header(header)
                    .with_status_code(code),
            );
        }
    });
    true
}
