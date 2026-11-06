"""Ash demo API — the product surface used by the World page and the demo.

Endpoints (JSON, CORS open for localhost demo):
    GET  /status
    POST /seal    {"container": "C-001", "owner": "<human id>"}
    POST /unseal  {"container": "C-001", "proof": <IDKit result or "good">}
    GET  /ledger

Run: python3 device/demo_api.py
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from og import MockRouter, Router, RouterDecider  # noqa: E402
from seal_service import Denied, FakeMcu, KeyDestroyed, SealService  # noqa: E402
from world_idkit import StaticWorld, WorldError, WorldIdKit  # noqa: E402


class HttpMcu:
    """Talks to the board's app over `adb forward tcp:8081 tcp:8080`."""

    def __init__(self, base: str = "http://127.0.0.1:8081"):
        self.base = base

    def _post(self, path: str, body: dict) -> dict:
        import urllib.request
        req = urllib.request.Request(self.base + path, data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())

    def _get(self, path: str) -> dict:
        import urllib.request
        with urllib.request.urlopen(self.base + path, timeout=10) as r:
            return json.loads(r.read().decode())

    def status(self) -> dict:
        return json.loads(self._get("/status")["mcu"])

    def arm(self) -> dict:
        return json.loads(self._post("/arm", {})["mcu"])

    def derive(self, nonce_hex: str) -> str:
        return str(self._post("/derive", {"nonce": nonce_hex})["key"])

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
    if os.environ.get("ASH_WORLD", "idkit") == "static":
        print("WARN: World is STATIC ('good')", flush=True)
        return StaticWorld({"good": "human-001"})
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


if os.environ.get("ASH_MCU", "board") == "board":
    print("MCU: board via http://127.0.0.1:8081", flush=True)
    mcu = HttpMcu(os.environ.get("ASH_MCU_URL", "http://127.0.0.1:8081"))
else:
    print("MCU: FakeMcu (no hardware)", flush=True)
    mcu = FakeMcu()
svc = SealService(mcu, make_world(), make_decider(), STORE, mock=os.environ.get("ASH_MOCK", "0") == "1")
if not PAYLOAD.exists():
    PAYLOAD.write_bytes(b"Ash demo payload: settlement agreement, 6 Nov 2026\n")


_nonces: dict[str, str] = {}


def _message(account: str, nonce: str) -> str:
    return f"Ash demo login\naccount: {account}\nnonce: {nonce}"


def _verify_evm(account: str, signature: str, message: str) -> tuple[bool, str]:
    try:
        from eth_account import Account
        from eth_account.messages import encode_defunct
    except Exception as e:  # pragma: no cover
        return False, f"eth_account unavailable: {e}"
    try:
        rec = Account.recover_message(encode_defunct(text=message), signature=signature)
    except Exception as e:
        return False, f"recover failed: {e}"
    return rec.lower() == account.lower(), rec


def _verify_hedera(account: str, signature: str, message: str) -> tuple[bool, str]:
    """Best-effort: fetch the account key from the Mirror Node and check an Ed25519 signature."""
    import urllib.request
    try:
        url = f"https://testnet.mirrornode.hedera.com/api/v1/accounts/{account}"
        with urllib.request.urlopen(url, timeout=8) as r:
            data = json.loads(r.read().decode())
        key = data.get("key", {})
        if key.get("_type") != "ED25519":
            return False, f"key type {key.get('_type')} not supported yet"
        pub = bytes.fromhex(key["key"])
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        from cryptography.exceptions import InvalidSignature
        sig = bytes.fromhex(signature.replace("0x", ""))
        try:
            Ed25519PublicKey.from_public_bytes(pub).verify(sig, message.encode())
            return True, account
        except InvalidSignature:
            return False, "signature does not match"
    except Exception as e:
        return False, f"hedera verify failed: {e}"


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, format, *args):  # noqa: A002
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
        if self.path == "/evidence":
            return self._send(200, {
                "erase_us": 874, "wipe_us": 1321,
                "bridge_p50_ms": 6.19, "bridge_p95_ms": 7.20,
                "tier1_p50_s": 2.05, "tier1_cost_usd_micro": 38, "deadline_ms": 5000,
            })
        if self.path.startswith("/world/config"):
            return self._proxy_get("http://127.0.0.1:7070/api/config")
        if self.path.startswith("/wallet/nonce"):
            from urllib.parse import urlparse, parse_qs
            q = parse_qs(urlparse(self.path).query)
            account = (q.get("account") or [""])[0]
            if not account:
                return self._send(400, {"ok": False, "error": "account required"})
            nonce = os.urandom(8).hex()
            _nonces[account] = nonce
            return self._send(200, {"message": _message(account, nonce), "nonce": nonce})
        if self.path == "/events":
            return self._sse()
        self._send(404, {"error": "not_found"})

    def _proxy_get(self, url):
        import urllib.request
        try:
            with urllib.request.urlopen(url, timeout=5) as r:
                return self._send(200, json.loads(r.read().decode()))
        except Exception as e:
            return self._send(502, {"ok": False, "error": str(e)})

    def _sse(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        last = ""
        try:
            while True:
                st = json.dumps(svc.mcu.status(), default=str)
                text = svc.ledger.read_text() if svc.ledger.exists() else ""
                h = hashlib.sha256(text.encode()).hexdigest()[:12]
                if st != last:
                    last = st
                    self.wfile.write(f"event: status\ndata: {st}\n\n".encode())
                    self.wfile.flush()
                if h != getattr(self, "_lh", ""):
                    self._lh = h
                    self.wfile.write(f"event: ledger\ndata: {json.dumps({'hash': h})}\n\n".encode())
                    self.wfile.flush()
                time.sleep(1)
        except (BrokenPipeError, ConnectionResetError, OSError):
            return

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            return self._send(400, {"error": "bad_json"})

        if self.path in ("/sim", "/reprovision"):
            try:
                return self._send(200, svc.mcu._post(self.path, body))
            except Exception as e:
                return self._send(500, {"ok": False, "error": str(e)})

        if self.path == "/seal":
            try:
                c = body.get("container", "C-001")
                payload = DEMO / f"{c}.bin"
                payload.write_bytes(PAYLOAD.read_bytes())
                rec = svc.seal(c, payload, owner=body.get("owner", ""))
                return self._send(200, {"ok": True, "record": rec})
            except Exception as e:
                return self._send(409, {"ok": False, "error": str(e)})

        if self.path == "/unseal":
            c = body.get("container", "C-001")
            out = DEMO / f"{c}.out"
            try:
                rec = svc.unseal(c, DEMO / f"{c}.bin.ash", body.get("proof", ""), out)
                text = out.read_text(errors="replace")[:200]
                return self._send(200, {"ok": True, "record": rec, "payload": text})
            except (Denied, WorldError, KeyDestroyed) as e:
                return self._send(403, {"ok": False, "error": f"{type(e).__name__}: {e}"})
            except Exception as e:
                return self._send(500, {"ok": False, "error": f"{type(e).__name__}: {e}"})

        if self.path == "/wallet/verify":
            account = body.get("account", "")
            sig = body.get("signature", "")
            chain = body.get("chain", "evm")
            nonce = _nonces.get(account)
            if not nonce:
                return self._send(400, {"ok": False, "error": "no nonce for account"})
            msg = _message(account, nonce)
            if chain == "evm":
                ok, info = _verify_evm(account, sig, msg)
            else:
                ok, info = _verify_hedera(account, sig, msg)
            if not ok:
                return self._send(403, {"ok": False, "error": info})
            _nonces.pop(account, None)
            return self._send(200, {"ok": True, "account": account, "chain": chain})

        if self.path == "/world/rp-signature":
            import urllib.request
            try:
                req = urllib.request.Request("http://127.0.0.1:7070/api/rp-signature", data=b"{}",
                                             headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=10) as r:
                    return self._send(200, json.loads(r.read().decode()))
            except Exception as e:
                return self._send(502, {"ok": False, "error": str(e)})

        self._send(404, {"error": "not_found"})


if __name__ == "__main__":
    port = int(os.environ.get("ASH_API_PORT", "8080"))
    print(f"ash api on 127.0.0.1:{port}  store={STORE}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
