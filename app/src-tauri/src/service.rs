//! Service supervision: attach to the API already on 8080, or spawn the bundled one.
//! The Python service owns seal/unseal/World/0G; the app never reimplements it.

use serde::Serialize;
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::time::Duration;

use crate::config;

#[derive(Clone, Debug, Serialize)]
pub struct ServiceInfo {
    pub mode: String,
    pub base: String,
    pub detail: String,
    pub mock: bool,
}

impl Default for ServiceInfo {
    fn default() -> Self {
        Self {
            mode: "unavailable".into(),
            base: String::new(),
            detail: "not started".into(),
            mock: false,
        }
    }
}

enum Launch {
    Bin(PathBuf),
    Python { python: PathBuf, script: PathBuf, cwd: PathBuf },
}

pub fn probe(base: &str) -> bool {
    ureq::get(&format!("{base}/status"))
        .timeout(Duration::from_millis(900))
        .call()
        .is_ok()
}

fn evidence(base: &str) -> serde_json::Value {
    ureq::get(&format!("{base}/evidence"))
        .timeout(Duration::from_millis(1500))
        .call()
        .ok()
        .and_then(|r| r.into_string().ok())
        .and_then(|t| serde_json::from_str::<serde_json::Value>(&t).ok())
        .unwrap_or(serde_json::Value::Null)
}

/// Where the service binary lives, for a bundled AppImage or a dev checkout.
fn find_launch(exe_dir: &Path) -> Option<Launch> {
    if let Some(p) = std::env::var_os("ASH_SERVICE_BIN") {
        return Some(Launch::Bin(PathBuf::from(p)));
    }
    let candidates = [
        exe_dir.join("ash-service"),
        exe_dir.join("../lib/ash/ash-service"),
        exe_dir.join("../Resources/ash-service"),
    ];
    for c in candidates {
        if c.is_file() {
            return Some(Launch::Bin(c));
        }
    }
    // dev fallback: <repo>/app/src-tauri/target/debug -> <repo>
    let repo = exe_dir.join("../../../../");
    let script = repo.join("device/demo_api.py");
    let python = repo.join(".venv/bin/python");
    if script.is_file() {
        let python = if python.is_file() {
            python
        } else {
            PathBuf::from("python3")
        };
        return Some(Launch::Python {
            python,
            script,
            cwd: repo,
        });
    }
    None
}

fn free_port() -> u16 {
    std::net::TcpListener::bind(("127.0.0.1", 0))
        .ok()
        .and_then(|l| l.local_addr().ok())
        .map(|a| a.port())
        .unwrap_or(8092)
}

pub fn ensure(board_port: u16, serial: &str, exe_dir: &Path) -> (ServiceInfo, Option<Child>) {
    // 1. an explicit URL wins
    if let Ok(url) = std::env::var("ASH_API_URL") {
        if probe(&url) {
            return (
                ServiceInfo {
                    mode: "attached".into(),
                    base: url.clone(),
                    detail: "ASH_API_URL".into(),
                    mock: is_mock(&url),
                },
                None,
            );
        }
        config::log_line(&format!("service: ASH_API_URL {url} did not answer"));
    }

    // 2. the usual local service, started by the operator
    let local = "http://127.0.0.1:8080";
    if probe(local) {
        config::log_line("service: attached to 127.0.0.1:8080");
        return (
            ServiceInfo {
                mode: "attached".into(),
                base: local.into(),
                detail: "existing local service".into(),
                mock: is_mock(local),
            },
            None,
        );
    }

    // 3. spawn our own
    let Some(launch) = find_launch(exe_dir) else {
        return (
            ServiceInfo {
                mode: "unavailable".into(),
                base: String::new(),
                detail: "no ash-service binary in this bundle".into(),
                mock: false,
            },
            None,
        );
    };

    let port = free_port();
    let base = format!("http://127.0.0.1:{port}");
    let state = config::data_dir().join("state");
    let _ = std::fs::create_dir_all(&state);
    let log = config::state_dir().join("service.log");
    let _ = std::fs::create_dir_all(config::state_dir());
    let stderr = std::fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(&log)
        .ok();

    let mut cmd = match &launch {
        Launch::Bin(p) => {
            let mut c = Command::new(p);
            c.current_dir(config::data_dir());
            c
        }
        Launch::Python { python, script, cwd } => {
            let mut c = Command::new(python);
            c.arg(script).current_dir(cwd);
            c
        }
    };

    cmd.env("ASH_API_PORT", port.to_string())
        .env("ASH_LINK", "0")
        .env("ASH_MCU_URL", format!("http://127.0.0.1:{board_port}"))
        .env("ASH_STATE_DIR", state.to_string_lossy().to_string())
        .stdin(Stdio::null())
        .stdout(Stdio::null());
    if !serial.is_empty() {
        cmd.env("ASH_SERIAL", serial);
    }
    if let Some(f) = stderr {
        cmd.stderr(f);
    }

    match cmd.spawn() {
        Ok(child) => {
            config::log_line(&format!("service: spawned on {base}"));
            for _ in 0..50 {
                if probe(&base) {
                    return (
                        ServiceInfo {
                            mode: "spawned".into(),
                            base: base.clone(),
                            detail: log.display().to_string(),
                            mock: is_mock(&base),
                        },
                        Some(child),
                    );
                }
                std::thread::sleep(Duration::from_millis(200));
            }
            let mut child = child;
            let _ = child.kill();
            (
                ServiceInfo {
                    mode: "unavailable".into(),
                    base: String::new(),
                    detail: format!("service did not answer within 10 s; see {}", log.display()),
                    mock: false,
                },
                None,
            )
        }
        Err(e) => (
            ServiceInfo {
                mode: "unavailable".into(),
                base: String::new(),
                detail: format!("could not start the service: {e}"),
                mock: false,
            },
            None,
        ),
    }
}

fn is_mock(base: &str) -> bool {
    evidence(base)
        .get("mock")
        .and_then(|v| v.as_bool())
        .unwrap_or(false)
}
