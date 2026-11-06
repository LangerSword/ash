"""Device link: auto-detect the UNO Q over ADB, keep the API reachable, report health.

The board runs Ash as an App Lab app that serves HTTP on 8080 inside its container,
published on the board's localhost. `adb forward tcp:8081 tcp:8080` makes it reachable
from the laptop. This module owns that lifecycle so the demo survives a replug.
"""
from __future__ import annotations

import json
import subprocess
import threading
import time
import urllib.request

DEFAULT_SERIAL = "3017640407"


class DeviceLink:
    def __init__(self, serial: str = "", local_port: int = 8081, remote_port: int = 8080,
                 poll_s: float = 2.0):
        self.serial = serial
        self.local_port = local_port
        self.remote_port = remote_port
        self.poll_s = poll_s
        self.state = "starting"
        self.detail = ""
        self.serial_seen = ""
        self._stop = False
        self.started = False
        self._thread = threading.Thread(target=self._run, daemon=True)

    # ------------------------------------------------------------------ adb
    def _adb(self, *args: str, timeout: float = 4.0) -> subprocess.CompletedProcess:
        return subprocess.run(["adb", *args], capture_output=True, text=True, timeout=timeout)

    def _devices(self) -> list[tuple[str, str]]:
        out = self._adb("devices").stdout
        rows = []
        for line in out.splitlines()[1:]:
            parts = line.split("\t")
            if len(parts) == 2:
                rows.append((parts[0].strip(), parts[1].strip()))
        return rows

    def _ensure_forward(self) -> None:
        self._adb("forward", f"tcp:{self.local_port}", f"tcp:{self.remote_port}")

    def _probe(self) -> dict | None:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{self.local_port}/status", timeout=2) as r:
                payload = json.loads(r.read().decode())
                return json.loads(payload["mcu"]) if isinstance(payload.get("mcu"), str) else payload
        except Exception:
            return None

    # ------------------------------------------------------------------ loop
    def _run(self) -> None:
        while not self._stop:
            try:
                self._tick()
            except Exception as e:  # never kill the poller
                self.state = "error"
                self.detail = f"{type(e).__name__}: {e}"
            time.sleep(self.poll_s)

    def _tick(self) -> None:
        rows = self._devices()
        if not rows:
            self.state, self.detail, self.serial_seen = "absent", "no adb device", ""
            return
        preferred = [r for r in rows if r[0] == (self.serial or DEFAULT_SERIAL)]
        chosen = preferred[0] if preferred else rows[0]
        serial, status = chosen
        self.serial_seen = serial
        if status != "device":
            self.state, self.detail = "unauthorized", status
            return
        self._ensure_forward()
        mcu = self._probe()
        if mcu is None:
            self.state, self.detail = "forwarded", "api not answering yet"
            return
        self.state, self.detail, self.mcu = "ready", "", mcu

    # ------------------------------------------------------------------ api
    def start(self) -> "DeviceLink":
        self.started = True
        self._thread.start()
        return self

    def stop(self) -> None:
        self._stop = True

    def snapshot(self) -> dict:
        if not self.started:
            return {"state": "external", "serial": "", "api": "", "mcu": None,
                    "detail": "device link is owned by another process",
                    "at": int(time.time())}
        return {
            "state": self.state,
            "serial": self.serial_seen,
            "api": f"http://127.0.0.1:{self.local_port}",
            "detail": self.detail,
            "mcu": getattr(self, "mcu", None),
            "at": int(time.time()),
        }
