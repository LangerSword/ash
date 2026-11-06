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
    def __init__(self, rp_id: str, base: str = DEFAULT_BASE, timeout: int = 20,
                 action: str = ""):
        if not rp_id:
            raise ValueError("rp_id is required")
        self.rp_id = rp_id
        self.base = base.rstrip("/")
        self.timeout = timeout
        # v4 verify rejects a uniqueness proof with no action
        # ("action is required for uniqueness proofs"); the IDKit result does not
        # always carry it, so the relying party supplies its own.
        self.action = action

    def verify(self, result: dict | str) -> str:
        """Forward the IDKit result and return a stable human identifier.

        Raises WorldError on any non-2xx, malformed body, or missing nullifier.
        """
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except json.JSONDecodeError:
                raise WorldError("proof is not a JSON object") from None
        if not isinstance(result, dict) or not result:
            raise WorldError("proof is empty")
        if result.get("success") is False:
            raise WorldError(f"proof not completed: {result.get('error') or 'unknown'}")
        url = f"{self.base}/api/v4/verify/{self.rp_id}"
        outgoing = dict(result)
        if self.action and not outgoing.get("action"):
            outgoing["action"] = self.action
        body = json.dumps(outgoing).encode()
        req = urllib.request.Request(
            url, data=body,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                # Cloudflare fronts this endpoint and rejects the bare
                # "Python-urllib/x" agent with 403/1010. Any ordinary agent passes.
                "User-Agent": "ash-seal/1.0 (+https://github.com/LangerSword/ash)",
            },
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

    def verify(self, proof: str) -> str:
        token = proof if isinstance(proof, str) else json.dumps(proof, sort_keys=True)
        if token in self.mapping:
            return self.mapping[token]
        raise WorldError("proof rejected")
