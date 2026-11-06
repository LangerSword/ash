"""World ID via IDKit — server-side verification.

Endpoint confirmed from the Developer Portal OpenAPI reference:
    POST https://developer.world.org/api/v4/verify/{rp_id}
    body: the complete IDKit result, unmodified.
    rp_id (`rp_...`) is preferred; app_id is accepted for compatibility.

The RP signature is produced by `tools/rp_sign.mjs` (the official
`@worldcoin/idkit-core/signing` helper), not reimplemented here.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request

DEFAULT_BASE = "https://developer.world.org"


class WorldError(Exception):
    pass


class WorldIdKit:
    def __init__(self, rp_id: str, base: str = DEFAULT_BASE, timeout: int = 20):
        if not rp_id:
            raise ValueError("rp_id is required")
        self.rp_id = rp_id
        self.base = base.rstrip("/")
        self.timeout = timeout

    def verify(self, result: dict) -> str:
        """Forward the IDKit result and return a stable human identifier.

        Raises WorldError on any non-2xx, malformed body, or missing nullifier.
        """
        url = f"{self.base}/api/v4/verify/{self.rp_id}"
        body = json.dumps(result).encode()
        req = urllib.request.Request(
            url, data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                payload = json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:300]
            raise WorldError(f"verify HTTP {e.code}: {detail}") from None
        except Exception as e:
            raise WorldError(f"verify failed: {type(e).__name__}: {e}") from None

        return _human_id(payload)


def _human_id(payload: dict) -> str:
    """Pull the nullifier out of the verify response, tolerating both shapes."""
    # 4.0 shape: {"responses":[{"nullifier": ...}, ...]}
    for key in ("nullifier", "nullifier_hash"):
        if isinstance(payload.get(key), str) and payload[key]:
            return payload[key]
    responses = payload.get("responses")
    if isinstance(responses, list):
        for r in responses:
            if isinstance(r, dict):
                for key in ("nullifier", "nullifier_hash"):
                    if isinstance(r.get(key), str) and r[key]:
                        return r[key]
    raise WorldError(f"no nullifier in response: {json.dumps(payload)[:200]}")


class StaticWorld:
    """Test double: maps proof tokens to human ids."""

    def __init__(self, mapping: dict[str, str]):
        self.mapping = mapping

    def verify(self, result) -> str:
        token = result if isinstance(result, str) else json.dumps(result, sort_keys=True)
        if token in self.mapping:
            return self.mapping[token]
        raise WorldError("proof rejected")
