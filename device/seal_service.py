"""Ash seal service — the product spine.

Ties the MCU (key custody), the vault (AES-GCM), World (who may open), and the
0G decision (release|deny) into one state machine, with a hash-chained record.

Nothing here talks to the network directly; the interfaces are injected so the
same code runs against fakes in tests, a mock router before the key arrives, and
the real Router/Wold/IdP on the board.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from ash_vault import open_payload, seal_payload

STATE_ARMED = "ARMED"
STATE_UNSEALED = "UNSEALED"
STATE_TAMPERED = "TAMPERED"


class Mcu(Protocol):
    def status(self) -> dict: ...
    def arm(self) -> dict: ...
    def derive(self, nonce_hex: str) -> str: ...


class WorldVerifier(Protocol):
    def verify(self, proof: str) -> str:
        """Return a stable human id (nullifier / sub) or raise Denied."""
        ...


class Decider(Protocol):
    def release(self, seal: dict, human: str) -> tuple[bool, str, dict]: ...


class Denied(Exception):
    pass


class KeyDestroyed(Exception):
    pass


@dataclass
class SealRecord:
    container: str
    created_at: int
    seal_id: str
    payload_sha256: str
    header: dict
    prev: str = ""
    events: list[dict] = field(default_factory=list)

    def digest(self) -> str:
        body = {k: v for k, v in self.__dict__.items() if k != "digest"}
        return hashlib.sha256(
            json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()


class SealService:
    def __init__(self, mcu: Mcu, world: WorldVerifier, decider: Decider,
                 store: Path, mock: bool = False):
        self.mcu = mcu
        self.world = world
        self.decider = decider
        self.store = Path(store)
        self.store.mkdir(parents=True, exist_ok=True)
        self.ledger = self.store / "ledger.jsonl"
        self.mock = mock

    # ---------------------------------------------------------------- records
    def _append(self, record: dict) -> str:
        prev = ""
        if self.ledger.exists():
            lines = self.ledger.read_text().strip().splitlines()
            if lines:
                prev = json.loads(lines[-1])["hash"]
        record["prev"] = prev
        record["mock"] = self.mock
        body = json.dumps(record, sort_keys=True, separators=(",", ":"))
        record["hash"] = hashlib.sha256((prev + body).encode()).hexdigest()
        with self.ledger.open("a") as f:
            f.write(json.dumps(record, sort_keys=True) + "\n")
        return record["hash"]

    def verify_ledger(self) -> tuple[bool, str]:
        prev = ""
        if not self.ledger.exists():
            return True, "empty"
        for i, line in enumerate(self.ledger.read_text().splitlines()):
            rec = json.loads(line)
            claimed = rec.pop("hash")
            body = json.dumps(rec, sort_keys=True, separators=(",", ":"))
            if hashlib.sha256((prev + body).encode()).hexdigest() != claimed:
                return False, f"record {i}"
            prev = claimed
        return True, "ok"

    # ---------------------------------------------------------------- seal
    def seal(self, container: str, payload: Path, note: str = "") -> dict:
        st = self.mcu.status()
        if st.get("state") != 1 or not st.get("master"):
            raise Denied(f"cannot seal in state {st}")
        nonce = hashlib.sha256(f"{container}:{time.time_ns()}".encode()).hexdigest()[:32]
        k = self.mcu.derive(nonce)
        if k.startswith("ERR"):
            raise KeyDestroyed(k)
        dest = payload.with_suffix(payload.suffix + ".ash")
        header = seal_payload(bytes.fromhex(k), payload, dest, container)
        rec = {
            "event": "SEALED",
            "container": container,
            "at": int(time.time()),
            "nonce": nonce,
            "payload_sha256": header["plaintext_sha256"],
            "header": header,
            "note": note,
        }
        rec["hash"] = self._append(rec)
        self._last = rec
        return rec

    # ---------------------------------------------------------------- unseal
    def unseal(self, container: str, container_file: Path, proof: str,
               out: Path) -> dict:
        try:
            human = self.world.verify(proof)
        except Denied as e:
            self._append({"event": "UNSEAL_DENIED", "container": container,
                          "reason": f"world:{e}", "at": int(time.time())})
            raise

        st = self.mcu.status()
        if st.get("state") == 3 or not st.get("master"):
            self._append({"event": "UNSEAL_DENIED", "container": container,
                          "reason": "key_destroyed", "at": int(time.time())})
            raise KeyDestroyed("key destroyed")

        ok, reason, meta = self.decider.release({"container": container}, human)
        if not ok:
            self._append({"event": "UNSEAL_DENIED", "container": container,
                          "reason": f"0g:{reason}", "meta": meta, "at": int(time.time())})
            raise Denied(f"0g deny: {reason}")

        k = self.mcu.derive(self._nonce_for(container))
        if k.startswith("ERR"):
            raise KeyDestroyed(k)
        header = open_payload(bytes.fromhex(k), container_file, out)
        rec = {"event": "UNSEALED", "container": container, "human": human,
               "at": int(time.time()), "0g": meta, "payload_sha256": header["plaintext_sha256"]}
        rec["hash"] = self._append(rec)
        return rec

    def _nonce_for(self, container: str) -> str:
        if not self.ledger.exists():
            raise Denied("no seal")
        for line in reversed(self.ledger.read_text().splitlines()):
            r = json.loads(line)
            if r.get("event") == "SEALED" and r.get("container") == container:
                return r["nonce"]
        raise Denied("no seal for container")

    def tamper(self, container: str, reason: str) -> dict:
        rec = {"event": "TAMPERED", "container": container, "reason": reason,
               "at": int(time.time())}
        rec["hash"] = self._append(rec)
        return rec


# -------------------------------------------------------------------- fakes for tests
class FakeMcu:
    def __init__(self, k: bytes = bytes(range(32))):
        self.k = k
        self.state = 1
        self.nonces: dict[str, str] = {}

    def status(self) -> dict:
        return {"state": self.state, "master": 1 if self.k else 0, "counter": 0, "loop": 0}

    def arm(self) -> dict:
        self.state = 1
        return self.status()

    def derive(self, nonce_hex: str) -> str:
        if self.state == 3 or not self.k:
            return "ERR:not_armed"
        self.nonces[nonce_hex] = nonce_hex
        import hmac
        return hmac.new(self.k, bytes.fromhex(nonce_hex), hashlib.sha256).hexdigest()

    def wipe(self) -> None:
        self.k = b""
        self.state = 3


class FakeWorld:
    def verify(self, proof: str) -> str:
        if proof == "good":
            return "human-001"
        raise Denied("proof rejected")


class FakeDecider:
    def __init__(self, allow: bool = True):
        self.allow = allow

    def release(self, seal: dict, human: str):
        return self.allow, ("ok" if self.allow else "policy"), {"mock": True}
