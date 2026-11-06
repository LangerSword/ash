"""Tests for the seal service. Run: python3 device/test_seal_service.py"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from seal_service import (Denied, FakeDecider, FakeMcu, FakeWorld, KeyDestroyed,
                          SealService)


def new(tmp: Path, allow=True):
    mcu = FakeMcu()
    return SealService(mcu, FakeWorld(), FakeDecider(allow), tmp, mock=True), mcu


def case_seal_and_unseal(tmp: Path) -> None:
    svc, _ = new(tmp)
    payload = tmp / "payload.bin"
    payload.write_bytes(b"settlement agreement, confidential")
    rec = svc.seal("C-001", payload)
    assert rec["event"] == "SEALED"
    enc = payload.with_suffix(payload.suffix + ".ash")
    assert enc.exists() and enc.read_bytes()[:4] == b"ASH1"
    assert b"confidential" not in enc.read_bytes()

    out = tmp / "out.bin"
    done = svc.unseal("C-001", enc, "good", out)
    assert done["event"] == "UNSEALED"
    assert out.read_bytes() == payload.read_bytes()
    print("seal + unseal        ok")


def case_wrong_human(tmp: Path) -> None:
    svc, _ = new(tmp)
    payload = tmp / "p.bin"
    payload.write_bytes(b"x")
    svc.seal("C-002", payload)
    enc = payload.with_suffix(payload.suffix + ".ash")
    try:
        svc.unseal("C-002", enc, "bad", tmp / "o.bin")
    except Denied:
        ok, _ = svc.verify_ledger()
        assert ok
        print("wrong human denied   ok")
        return
    raise AssertionError("bad proof accepted")


def case_0g_denies(tmp: Path) -> None:
    svc, _ = new(tmp, allow=False)
    payload = tmp / "p.bin"
    payload.write_bytes(b"x")
    svc.seal("C-003", payload)
    enc = payload.with_suffix(payload.suffix + ".ash")
    try:
        svc.unseal("C-003", enc, "good", tmp / "o.bin")
    except Denied:
        print("0g deny blocks       ok")
        return
    raise AssertionError("0G deny did not block")


def case_key_destroyed(tmp: Path) -> None:
    svc, mcu = new(tmp)
    payload = tmp / "p.bin"
    payload.write_bytes(b"x")
    svc.seal("C-004", payload)
    enc = payload.with_suffix(payload.suffix + ".ash")
    mcu.wipe()
    try:
        svc.unseal("C-004", enc, "good", tmp / "o.bin")
    except KeyDestroyed:
        print("wipe blocks unseal   ok")
        return
    raise AssertionError("unseal worked after wipe")


def case_ledger_tamper(tmp: Path) -> None:
    svc, _ = new(tmp)
    payload = tmp / "p.bin"
    payload.write_bytes(b"x")
    svc.seal("C-005", payload)
    lines = svc.ledger.read_text().splitlines()
    lines[0] = lines[0].replace('"C-005"', '"C-006"')
    svc.ledger.write_text("\n".join(lines) + "\n")
    ok, why = svc.verify_ledger()
    assert not ok
    print(f"ledger tamper        ok ({why})")


def main() -> int:
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        for fn in (case_seal_and_unseal, case_wrong_human, case_0g_denies,
                   case_key_destroyed, case_ledger_tamper):
            sub = tmp / fn.__name__
            sub.mkdir()
            fn(sub)
    print("all seal-service tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
