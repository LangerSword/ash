import json, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from arduino.app_utils import Bridge

import threading
_BRIDGE_LOCK = threading.Lock()

def call(name, *a):
    try:
        with _BRIDGE_LOCK:
            return str(Bridge.call(name, *a))
    except Exception as e:
        return "ERR:%r" % (e,)


def _pack_frame(frame):
    """104 chars of '0'/'1' (row-major 13x8) -> 26 hex chars, MSB-first."""
    bits = str(frame).strip()
    if len(bits) != 104 or any(c not in "01" for c in bits):
        raise ValueError("each frame must be 104 characters of 0/1")
    out = bytearray(13)
    for i, c in enumerate(bits):
        if c == "1":
            out[i >> 3] |= 1 << (7 - (i & 7))
    return out.hex()

class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def log_message(self, format, *args):
        return
    def _send(self, code, payload):
        data = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
    def do_GET(self):
        if self.path.startswith("/status"):
            return self._send(200, {"mcu": call("status"), "selftest": call("selftest")})
        self._send(404, {"error": "not_found"})
    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        body = json.loads(self.rfile.read(n) or b"{}")
        if self.path == "/flex":
            a = call("sim", 0)
            time.sleep(0.14)
            b = call("sim", 1)
            return self._send(200, {"open": a, "close": b})
        if self.path == "/sim":
            return self._send(200, {"mcu": call("sim", int(body.get("closed", 1)))})
        if self.path == "/reprovision":
            return self._send(200, {"mcu": call("reprovision")})
        if self.path == "/arm":
            return self._send(200, {"mcu": call("arm")})
        if self.path == "/derive":
            return self._send(200, {"key": call("derive", body.get("nonce", "00"))})
        if self.path == "/seal":
            return self._send(200, {"arm": call("arm"), "key": call("derive", body.get("nonce", "00"))})
        if self.path == "/decision":
            return self._send(200, {"mcu": call("decision", body.get("decision", "wipe"))})
        if self.path == "/deadline":
            return self._send(200, {"mcu": call("deadline", int(body.get("ms", 5000)))})
        if self.path == "/frame":
            frames = body.get("frames") or []
            if not isinstance(frames, list) or not frames:
                return self._send(400, {"error": "frames required"})
            if len(frames) > 64:
                return self._send(400, {"error": "max 64 frames"})
            try:
                fps = max(1, min(30, int(body.get("fps", 12))))
                spec = "%d:%s" % (fps, ",".join(_pack_frame(f) for f in frames))
            except (TypeError, ValueError) as e:
                return self._send(400, {"error": str(e)})
            return self._send(200, {"mcu": call("frames", spec),
                                    "frames": len(frames), "fps": fps})
        self._send(404, {"error": "not_found"})

def start(port=8080):
    t = threading.Thread(target=ThreadingHTTPServer(("0.0.0.0", port), H).serve_forever, daemon=True)
    t.start()
