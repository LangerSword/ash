"""Hedera x402 (exact scheme) resource server, minimal and honest.

Shape follows Hedera's `exact` scheme (x402Version 2):
  requirement = {scheme, network, amount, asset, payTo, maxTimeoutSeconds, extra:{feePayer}}
  client sends  X-PAYMENT: base64(PaymentPayload)
  server calls facilitator /verify then /settle, returns the transaction id.

Nothing here holds funds. If the facilitator or payTo is unset, the endpoint
returns 503 `hedera_not_configured` instead of pretending to charge.
"""
from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request

X402_VERSION = 2
HASHSCAN = {
    "hedera:testnet": "https://hashscan.io/testnet/transaction/",
    "hedera:mainnet": "https://hashscan.io/mainnet/transaction/",
}


class X402Error(Exception):
    pass


def config() -> dict:
    return {
        "network": os.environ.get("HEDERA_NETWORK", "hedera:testnet"),
        "pay_to": os.environ.get("HEDERA_PAY_TO", ""),
        "asset": os.environ.get("HEDERA_ASSET", "0.0.0"),
        "amount": os.environ.get("HEDERA_AMOUNT", "10000000"),
        "fee_payer": os.environ.get("HEDERA_FEE_PAYER", ""),
        "facilitator": os.environ.get("X402_FACILITATOR", ""),
        "timeout": int(os.environ.get("HEDERA_MAX_TIMEOUT", "180")),
    }


def ready() -> bool:
    c = config()
    return bool(c["pay_to"] and c["facilitator"])


def requirement(resource: str) -> dict:
    c = config()
    return {
        "scheme": "exact",
        "network": c["network"],
        "amount": c["amount"],
        "asset": c["asset"],
        "payTo": c["pay_to"],
        "maxTimeoutSeconds": c["timeout"],
        "resource": resource,
        "extra": {"feePayer": c["fee_payer"]},
    }


def challenge(resource: str, reason: str = "payment required") -> dict:
    return {
        "x402Version": X402_VERSION,
        "error": reason,
        "accepts": [requirement(resource)],
    }


def _post(url: str, body: dict) -> dict:
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json",
                                          "Accept": "application/json",
                                          "User-Agent": "ash-seal/1.0 (x402 client)"},
                                 method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise X402Error(f"facilitator HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:200]}") from None
    except Exception as e:
        raise X402Error(f"facilitator {type(e).__name__}: {e}") from None


def settle(x_payment: str, resource: str) -> dict:
    """Verify then settle. Returns {tx_id, hashscan, network, raw}."""
    if not ready():
        raise X402Error("hedera_not_configured")
    try:
        payload = json.loads(base64.b64decode(x_payment))
    except Exception as e:
        raise X402Error(f"bad X-PAYMENT: {e}") from None

    body = {
        "x402Version": X402_VERSION,
        "paymentPayload": payload,
        "paymentRequirements": requirement(resource),
    }
    fac = config()["facilitator"].rstrip("/")
    verify = _post(f"{fac}/verify", body)
    if not (verify.get("isValid") or verify.get("valid")):
        raise X402Error(f"verify failed: {verify.get('invalidReason') or verify}")
    settled = _post(f"{fac}/settle", body)
    tx = settled.get("transaction") or settled.get("txId") or settled.get("transactionId")
    if not tx:
        raise X402Error(f"settle returned no transaction: {str(settled)[:200]}")
    prefix = HASHSCAN.get(config()["network"], HASHSCAN["hedera:testnet"])
    return {"tx_id": tx, "hashscan": prefix + tx, "network": config()["network"], "raw": settled}
