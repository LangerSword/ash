"""USB relay: the board's container cannot do TLS, so it asks the laptop to fetch.

The board's Python app POSTs {url, method, headers, body} to this service; this
service performs the request and returns {status, body}. Used for 0G decisions
and, historically, for World.

Run: python3 tools/relay.py           # listens on 0.0.0.0:9001
Board side: adb reverse tcp:9001 tcp:9001
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ALLOW = ("router-api.0g.ai", "developer.world.org", "testnet.mirrornode.hedera.com")
TIMEOUT = float(os.environ.get("RELAY_TIMEOUT", "30"))


class Relay(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):  # keep the console quiet
        return

    def _send(self, code: int, payload: dict):
        data = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/healthz":
            return self._send(200, {"ok": True, "allow": list(ALLOW)})
        self._send(404, {"error": "not_found"})

    def do_POST(self):
        if self.path != "/relay":
            return self._send(404, {"error": "not_found"})
        n = int(self.headers.get("Content-Length") or 0)
        try:
            env = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            return self._send(400, {"error": "bad_json"})

        url = str(env.get("url", ""))
        host = url.split("//", 1)[-1].split("/", 1)[0].split(":")[0]
        if not any(host == a or host.endswith("." + a) for a in ALLOW):
            return self._send(403, {"error": f"host not allowed: {host}"})

        method = str(env.get("method", "POST")).upper()
        headers = {k: v for k, v in (env.get("headers") or {}).items()}
        body = env.get("body") or ""
        data = body.encode() if body else None
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                text = r.read().decode("utf-8", "replace")
                status = r.status
        except urllib.error.HTTPError as e:
            text = e.read().decode("utf-8", "replace")
            status = e.code
        except Exception as e:
            return self._send(502, {"error": f"{type(e).__name__}: {e}"})
        self._send(200, {"status": status, "body": text})


if __name__ == "__main__":
    port = int(os.environ.get("RELAY_PORT", "9001"))
    print(f"relay on 0.0.0.0:{port} · allow {', '.join(ALLOW)}", flush=True)
    try:
        ThreadingHTTPServer(("0.0.0.0", port), Relay).serve_forever()
    except KeyboardInterrupt:
        sys.exit(0)
