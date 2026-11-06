"""Ash demo API — the product surface used by the World page and the demo.

Endpoints (JSON, CORS open for localhost demo):
    GET  /status
    POST /seal    {"container": "C-001", "owner": "<human id>"}
    POST /unseal  {"container": "C-001", "proof": <IDKit result or "good">}
    GET  /ledger

Run: python3 device/demo_api.py
"""
from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from og import MockRouter, Router, RouterDecider  # noqa: E402
from seal_service import Denied, FakeMcu, KeyDestroyed, SealService  # noqa: E402
from world_idkit import StaticWorld, WorldError, WorldIdKit  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DEMO = ROOT / "demo"
DEMO.mkdir(exist_ok=True)
STORE = DEMO / "store"
PAYLOAD = DEMO / "payload.bin"

env = {}
env_file = ROOT / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
os.environ.update({k: v for k, v in env.items() if k not in os.environ})


def make_world():
    rp = os.environ.get("WORLD_RP_ID", "")
    if rp:
        return WorldIdKit(rp)
    print("WARN: WORLD_RP_ID unset, using StaticWorld (proof 'good')", flush=True)
    return StaticWorld({"good": "human-001"})


def make_decider():
    if os.environ.get("ASH_MOCK", "1") == "1":
        print("WARN: 0G is MOCK in this process (ASH_MOCK=1)", flush=True)
        return RouterDecider(MockRouter())
    return RouterDecider(Router())


svc = SealService(FakeMcu(), make_world(), make_decider(), STORE, mock=os.environ.get("ASH_MOCK", "1") == "1")
if not PAYLOAD.exists():
    PAYLOAD.write_bytes(b"Ash demo payload: settlement agreement, 6 Nov 2026\n")


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, format, *args):  # noqa: A002 - base class signature
        return

    def _send(self, code, payload):
        data = json.dumps(payload, default=str).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self._send(204, {})

    def do_GET(self):
        if self.path == "/status":
            return self._send(200, svc.mcu.status())
        if self.path == "/ledger":
            text = svc.ledger.read_text() if svc.ledger.exists() else ""
            return self._send(200, {"records": [json.loads(x) for x in text.splitlines() if x]})
        self._send(404, {"error": "not_found"})

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            return self._send(400, {"error": "bad_json"})

        if self.path == "/seal":
            try:
                rec = svc.seal(body.get("container", "C-001"), PAYLOAD,
                               owner=body.get("owner", ""))
                return self._send(200, {"ok": True, "record": rec})
            except Exception as e:
                return self._send(409, {"ok": False, "error": str(e)})

        if self.path == "/unseal":
            out = DEMO / "out.bin"
            try:
                rec = svc.unseal(body.get("container", "C-001"),
                                 PAYLOAD.with_suffix(".bin.ash"),
                                 body.get("proof", ""), out)
                text = out.read_text(errors="replace")[:200]
                return self._send(200, {"ok": True, "record": rec, "payload": text})
            except (Denied, WorldError, KeyDestroyed) as e:
                return self._send(403, {"ok": False, "error": f"{type(e).__name__}: {e}"})
            except Exception as e:
                return self._send(500, {"ok": False, "error": f"{type(e).__name__}: {e}"})

        self._send(404, {"error": "not_found"})


if __name__ == "__main__":
    port = int(os.environ.get("ASH_API_PORT", "8080"))
    print(f"ash api on 127.0.0.1:{port}  store={STORE}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
