"""0G Router client: the Tier 1 / Tier 2 decision, plus a labelled mock.

The Router is OpenAI-compatible: POST {base}/v1/chat/completions.
Tier 1 asks for a strict JSON verdict on a compact feature vector; Tier 2 asks
for a release decision with `verify_tee` on. Every response carries the model
completion id; when `verify_tee` is requested the TEE verification result is
kept alongside it. A mock response is always tagged `"mock": true` and must
never appear in README evidence or the demo.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

DEFAULT_BASE = "https://router-api.0g.ai"
DEFAULT_MODEL = "gemini-2.5-flash-lite"

TIER1_SYSTEM = (
    "You are a custody incident classifier for a tamper-evident seal. "
    "Input is a compact feature vector from a wire loop: ADC counts and timing. "
    "Return strict JSON only: "
    '{"decision":"hold|wipe","cause":"handling|intrusion|unknown"}. '
    "hold means the event is consistent with handling and the seal may stay armed. "
    "wipe means treat it as intrusion. If the evidence is insufficient, return "
    '{"decision":"wipe","cause":"unknown"}. Never invent events not present in the input.'
)

TIER2_SYSTEM = (
    "You authorise release of a sealed payload to a verified human. "
    "Return strict JSON only: "
    '{"decision":"release|deny","reason":"<short>"}. '
    "Deny if the record shows tamper, an unexplained gap, or a human id that does "
    "not match the seal. Release only when the record is consistent."
)


def _rid(payload: dict):
    """Prefer the 0G trace request id; fall back to the completion id."""
    trace = payload.get("x_0g_trace") or {}
    return trace.get("request_id") or payload.get("id")


class RouterError(Exception):
    pass


class Router:
    def __init__(self, api_key: str | None = None, base: str = DEFAULT_BASE,
                 model: str = DEFAULT_MODEL, timeout: int = 20):
        self.api_key = api_key or os.environ.get("OG_API_KEY", "")
        if not self.api_key:
            raise RouterError("OG_API_KEY is not set")
        self.base = base.rstrip("/")
        self.model = model
        self.timeout = timeout

    # ------------------------------------------------------------------ http
    def _chat(self, system: str, user: str, verify_tee: bool = False,
              max_tokens: int = 128) -> dict:
        body = {
            "model": self.model,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
            "max_tokens": max_tokens,
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
        if verify_tee:
            body["verify_tee"] = True
        req = urllib.request.Request(
            f"{self.base}/v1/chat/completions",
            data=json.dumps(body).encode(),
            headers={"Authorization": f"Bearer {self.api_key}",
                     "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                payload = json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            raise RouterError(f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:200]}") from None
        except Exception as e:
            raise RouterError(f"{type(e).__name__}: {e}") from None
        return payload

    @staticmethod
    def _content(payload: dict) -> dict:
        try:
            text = payload["choices"][0]["message"]["content"]
            return json.loads(text)
        except Exception as e:
            raise RouterError(f"non-JSON model output: {e}") from None

    # ------------------------------------------------------------------ tiers
    def classify(self, features: dict) -> dict:
        payload = self._chat(TIER1_SYSTEM, json.dumps(features, sort_keys=True))
        out = self._content(payload)
        out.setdefault("decision", "wipe")
        out.setdefault("cause", "unknown")
        if out["decision"] not in ("hold", "wipe"):
            out["decision"] = "wipe"
        out["request_id"] = _rid(payload)
        out["trace"] = payload.get("x_0g_trace")
        out["mock"] = False
        return out

    def release(self, seal: dict, human: str) -> dict:
        payload = self._chat(TIER2_SYSTEM,
                             json.dumps({"seal": seal, "human": human}, sort_keys=True),
                             verify_tee=True, max_tokens=128)
        out = self._content(payload)
        out.setdefault("decision", "deny")
        if out["decision"] not in ("release", "deny"):
            out["decision"] = "deny"
        out["request_id"] = _rid(payload)
        out["trace"] = payload.get("x_0g_trace")
        # The Router does not surface a TEE verdict on this provider; record
        # "unknown" rather than claiming verification.
        out["tee_verified"] = payload.get("tee_verified")
        out["mock"] = False
        return out


class MockRouter:
    """Labelled stand-in. Every response carries mock=True; never use as evidence."""

    def __init__(self, decision: str = "hold", cause: str = "handling",
                 release: bool = True):
        self.decision = decision
        self.cause = cause
        self.release_ok = release

    def classify(self, features: dict) -> dict:
        return {"decision": self.decision, "cause": self.cause,
                "request_id": "mock-tier1", "mock": True}

    def release(self, seal: dict, human: str) -> dict:
        return {"decision": "release" if self.release_ok else "deny",
                "reason": "mock", "request_id": "mock-tier2",
                "tee_verified": False, "mock": True}


class RouterDecider:
    """Adapts Router/MockRouter to the seal service's Decider interface."""

    def __init__(self, router):
        self.router = router

    def release(self, seal: dict, human: str):
        out = self.router.release(seal, human)
        ok = out.get("decision") == "release"
        return ok, out.get("reason", ""), out
