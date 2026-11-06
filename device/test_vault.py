"""Tests for the Ash payload vault. Run: python3 device/test_vault.py"""
import os
import sys
import tempfile
from pathlib import Path

from cryptography.exceptions import InvalidTag

sys.path.insert(0, str(Path(__file__).parent))
from ash_vault import open_payload, seal_payload

KEY = bytes(range(32))
WRONG = bytes(range(1, 33))


def case_roundtrip(tmp: Path) -> None:
    src = tmp / "payload.bin"
    data = os.urandom(4096) + b"ash"
    src.write_bytes(data)
    header = seal_payload(KEY, src, tmp / "c.ash", "C-001")
    assert header["size"] == len(data)
    open_payload(KEY, tmp / "c.ash", tmp / "out.bin")
    assert (tmp / "out.bin").read_bytes() == data
    print("roundtrip            ok")


def case_wrong_key(tmp: Path) -> None:
    src = tmp / "payload.bin"
    src.write_bytes(b"secret")
    seal_payload(KEY, src, tmp / "c.ash", "C-001")
    try:
        open_payload(WRONG, tmp / "c.ash", tmp / "out.bin")
    except InvalidTag:
        print("wrong key refused    ok")
        return
    raise AssertionError("wrong key was accepted")


def case_ciphertext_tamper(tmp: Path) -> None:
    src = tmp / "payload.bin"
    src.write_bytes(b"secret payload")
    seal_payload(KEY, src, tmp / "c.ash", "C-001")
    blob = bytearray((tmp / "c.ash").read_bytes())
    blob[-1] ^= 0x01
    (tmp / "c.ash").write_bytes(bytes(blob))
    try:
        open_payload(KEY, tmp / "c.ash", tmp / "out.bin")
    except InvalidTag:
        print("ciphertext tamper    ok")
        return
    raise AssertionError("tampered ciphertext was accepted")


def case_header_tamper(tmp: Path) -> None:
    src = tmp / "payload.bin"
    src.write_bytes(b"secret payload")
    seal_payload(KEY, src, tmp / "c.ash", "C-001")
    blob = bytearray((tmp / "c.ash").read_bytes())
    idx = blob.find(b"C-001")
    assert idx > 0
    blob[idx:idx + 5] = b"C-002"
    (tmp / "c.ash").write_bytes(bytes(blob))
    try:
        open_payload(KEY, tmp / "c.ash", tmp / "out.bin")
    except InvalidTag:
        print("header tamper        ok")
        return
    raise AssertionError("tampered header was accepted")


def main() -> int:
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        case_roundtrip(tmp)
        case_wrong_key(tmp)
        case_ciphertext_tamper(tmp)
        case_header_tamper(tmp)
    print("all vault tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
