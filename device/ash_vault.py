"""Ash payload vault.

The payload is encrypted with a key derived from a secret held by the MCU.
This module never generates or stores that secret; it takes `ikm` (the 32-byte
value returned by the MCU's HMAC for a given seal) and derives a per-container
AES-256-GCM key.

Container layout:
    b"ASH1" | 4-byte big-endian header length | header JSON | ciphertext

The header is authenticated as AAD, so editing the container name, salt or
nonce breaks decryption.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import struct
from pathlib import Path

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

MAGIC = b"ASH1"
INFO = b"ash-payload-v1"
CHUNK = 1 << 20


def hkdf_sha256(ikm: bytes, salt: bytes, info: bytes, length: int = 32) -> bytes:
    """RFC 5869 HKDF with SHA-256."""
    prk = hmac.new(salt, ikm, hashlib.sha256).digest()
    okm = b""
    t = b""
    counter = 1
    while len(okm) < length:
        t = hmac.new(prk, t + info + bytes([counter]), hashlib.sha256).digest()
        okm += t
        counter += 1
    return okm[:length]


def _derive(ikm: bytes, salt: bytes) -> bytes:
    return hkdf_sha256(ikm, salt, INFO, 32)


def seal_payload(ikm: bytes, src: Path, dst: Path, container: str) -> dict:
    """Encrypt `src` into an Ash container at `dst`. Returns the header."""
    plaintext = src.read_bytes()
    salt = os.urandom(16)
    nonce = os.urandom(12)
    key = _derive(ikm, salt)
    ct = AESGCM(key).encrypt(nonce, plaintext, None)
    header = {
        "v": 1,
        "container": container,
        "alg": "AES-256-GCM",
        "salt": salt.hex(),
        "nonce": nonce.hex(),
        "plaintext_sha256": hashlib.sha256(plaintext).hexdigest(),
        "size": len(plaintext),
    }
    hb = json.dumps(header, sort_keys=True, separators=(",", ":")).encode()
    # Re-encrypt with the header as AAD so the header itself is authenticated.
    ct = AESGCM(key).encrypt(nonce, plaintext, hb)
    with dst.open("wb") as f:
        f.write(MAGIC)
        f.write(struct.pack(">I", len(hb)))
        f.write(hb)
        f.write(ct)
    return header


def open_payload(ikm: bytes, src: Path, dst: Path) -> dict:
    """Decrypt an Ash container. Raises InvalidTag on any tamper or wrong key."""
    blob = src.read_bytes()
    if blob[:4] != MAGIC:
        raise ValueError("not an Ash container")
    (hlen,) = struct.unpack(">I", blob[4:8])
    header = json.loads(blob[8:8 + hlen])
    ct = blob[8 + hlen:]
    key = _derive(ikm, bytes.fromhex(header["salt"]))
    pt = AESGCM(key).decrypt(bytes.fromhex(header["nonce"]), ct, blob[8:8 + hlen])
    if hashlib.sha256(pt).hexdigest() != header["plaintext_sha256"]:
        raise ValueError("plaintext hash mismatch")
    dst.write_bytes(pt)
    return header


def _cli() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Ash vault (test harness)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("seal")
    s.add_argument("src")
    s.add_argument("dst")
    s.add_argument("--key", required=True, help="hex 32 bytes (test only)")
    s.add_argument("--container", default="C-001")
    o = sub.add_parser("open")
    o.add_argument("src")
    o.add_argument("dst")
    o.add_argument("--key", required=True)
    a = ap.parse_args()

    ikm = bytes.fromhex(a.key)
    if a.cmd == "seal":
        h = seal_payload(ikm, Path(a.src), Path(a.dst), a.container)
        print(json.dumps(h))
    else:
        h = open_payload(ikm, Path(a.src), Path(a.dst))
        print(json.dumps(h))
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
