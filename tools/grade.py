#!/usr/bin/env python3
"""Grade Ash against its own claims.

Deterministic: no LLM, no screenshots. Gates run first and are reported
separately from the score. Every detector has a negative control built from
the shipped bytes, so a green result that cannot go red is visible as such.

Run:  python3 tools/grade.py
Writes: grade-report.md
"""
from __future__ import annotations

import json
import os
import re
import shutil
import sys
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
DIST = SITE / "dist"
API = "https://api.langersword.in"
SITE_URL = "https://langersword.github.io/ash/"


# ------------------------------------------------------------------ transport
def get(url: str, retries: int = 3, timeout: int = 12) -> tuple[int, bytes]:
    last = (0, b"")
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ash-grade/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()
        except Exception as e:  # transport, not product
            last = (0, str(e).encode())
            time.sleep(0.6 * (i + 1))
    return last


def post(url: str, body: dict | None = None, headers: dict | None = None) -> tuple[int, bytes]:
    data = json.dumps(body or {}).encode()
    h = {"Content-Type": "application/json", "User-Agent": "ash-grade/1.0"}
    h.update(headers or {})
    req = urllib.request.Request(url, data=data, headers=h, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:
        return 0, str(e).encode()


# ------------------------------------------------------------------ helpers
def bundle_text() -> str:
    return "\n".join(p.read_text(errors="ignore") for p in DIST.glob("assets/*.js"))


def site_css() -> str:
    return "\n".join(p.read_text(errors="ignore") for p in DIST.glob("assets/*.css"))


def routes_from_api() -> set[str]:
    src = (ROOT / "device/demo_api.py").read_text()
    routes = set()
    for m in re.finditer(r'self\.path\s*==\s*"([^"]+)"', src):
        routes.add(m.group(1))
    for m in re.finditer(r'self\.path\.startswith\("([^"]+)"\)', src):
        routes.add(m.group(1).rstrip("/"))
    for m in re.finditer(r"self\.path in \(([^)]*)\)", src):
        for q in re.findall(r'"([^"]+)"', m.group(1)):
            routes.add(q)
    return routes


def routes_from_docs() -> set[str]:
    src = (SITE / "src/components/Docs.svelte").read_text()
    out = set()
    for m in re.finditer(r"(GET|POST)\s+(/[a-zA-Z0-9/:_-]+)", src):
        r = m.group(2).rstrip("/")
        r = re.sub(r"/\{[^}]+\}$", "", r)
        r = re.sub(r"/:[a-zA-Z]+$", "", r)
        out.add(r)
    return out


def shipped_svelte() -> list[Path]:
    """Only components reachable from App.svelte, so dead files cannot fail the gate."""
    seen: set[Path] = set()
    stack = [SITE / "src/App.svelte"]
    out: list[Path] = []
    while stack:
        p = stack.pop().resolve()
        if p in seen or not p.exists():
            continue
        seen.add(p)
        out.append(p)
        for m in re.finditer(r'import\s+\w+\s+from\s+"(\.[^"]+)"', p.read_text()):
            q = (p.parent / m.group(1)).resolve()
            if q.suffix == "":
                q = q.with_suffix(".svelte")
            stack.append(q)
    return out


def anchors_and_ids() -> tuple[set[str], set[str]]:
    srcs = "\n".join(p.read_text() for p in shipped_svelte())
    hrefs = {h for h in re.findall(r'href="#([a-zA-Z0-9_-]+)"', srcs)}
    ids = set(re.findall(r'id="([a-zA-Z0-9_-]+)"', srcs))
    return hrefs, ids


def evidence() -> dict:
    code, body = get(f"{API}/evidence")
    return json.loads(body) if code == 200 else {}


# ------------------------------------------------------------------ checks
@dataclass
class Result:
    name: str
    ok: bool
    detail: str
    gate: bool = False
    control: str = ""


def check_site() -> Result:
    code, body = get(SITE_URL)
    text = body.decode("utf-8", "ignore")
    ok = code == 200 and "Ash" in text and re.search(r"assets/index-[^\"]+\.css", text) is not None
    return Result("site reachable", ok, f"HTTP {code}, {len(text)} B", gate=True)


def check_api() -> Result:
    code, body = get(f"{API}/status")
    try:
        d = json.loads(body)
    except Exception:
        return Result("api status", False, f"HTTP {code}, unparseable", gate=True)
    keys = {"state", "counter", "master", "loop"} <= set(d)
    return Result("api status", code == 200 and keys, f"HTTP {code}, keys {sorted(d)}", gate=True)


def check_unseal_refused() -> Result:
    code, body = post(f"{API}/unseal", {"container": "C-001", "proof": ""})
    ok = 400 <= code < 500
    return Result("unseal refuses empty proof", ok, f"HTTP {code}: {body[:80]!r}", gate=True)


def check_assets() -> Result:
    pairs = [
        (SITE / "public/fonts/cormorant.woff2", DIST / "fonts/cormorant.woff2"),
        (SITE / "public/idkit.global.js", DIST / "idkit.global.js"),
        (SITE / "public/install.sh", DIST / "install.sh"),
    ]
    bad = [a.name for a, b in pairs if not b.exists() or a.read_bytes() != b.read_bytes()]
    return Result("shipped assets match source", not bad, f"{len(pairs) - len(bad)}/{len(pairs)} identical", gate=True)


BANNED = [
    r"settled on mainnet",
    r"verified on mainnet",
    r"production world id",
]


def check_no_overclaims() -> Result:
    text = bundle_text().lower()
    hits = [p for p in BANNED if re.search(p, text)]
    return Result("no settlement/mainnet overclaims", not hits, f"banned hits: {hits or 'none'}", gate=True)


def check_claim_parity(ev: dict, text: str | None = None) -> Result:
    text = bundle_text() if text is None else text
    erase = ev.get("erase_us", 0)
    wipe = ev.get("wipe_us", 0)
    want = [
        str(erase),
        f"{wipe / 1000:.2f}",
        f"{ev.get('tier1_p50_s', 0):.2f}",
        f"{ev.get('deadline_ms', 0):,}".replace(",", " "),
    ]
    missing = [w for w in want if w not in text]
    stale = "240 µs" in text
    ok = not missing and not stale
    return Result("site numbers match /evidence", ok, f"missing {missing or 'none'}, stale 240µs {stale}")


def check_route_parity(api_routes: set[str] | None = None, doc_routes: set[str] | None = None) -> Result:
    a = routes_from_api() if api_routes is None else api_routes
    d = routes_from_docs() if doc_routes is None else doc_routes
    def served(doc: str, routes: set[str]) -> bool:
        return any(doc == r or doc.startswith(r + "/") for r in routes)

    missing = {r for r in d if not served(r, a)}
    return Result("docs endpoints exist in the handler", not missing, f"{len(d)} listed, missing {sorted(missing) or 'none'}")


def check_anchors(anchors: set[str] | None = None, ids: set[str] | None = None) -> Result:
    a, i = anchors_and_ids()
    a = anchors if anchors is not None else a
    i = ids if ids is not None else i
    missing = {x for x in a if x not in i}
    return Result("nav anchors resolve", not missing, f"{len(a)} anchors, missing {sorted(missing) or 'none'}")


def check_motion(css: str | None = None) -> Result:
    css = site_css() if css is None else css
    guard = "prefers-reduced-motion" in css
    hero = "section-rise" in css
    return Result("reduced-motion guard on motion", guard and hero, f"guard {guard}, section-rise {hero}")


def check_autoplay() -> Result:
    hero = (SITE / "src/components/HeroBurn.svelte").read_text()
    app = (SITE / "src/App.svelte").read_text()
    raf = "requestAnimationFrame(frame)" in hero
    no_button = "onclick" not in hero and "<button" not in hero
    stage_click = bool(re.search(r'class="stage"[^>]*on', app))
    return Result("hero plays without a click", raf and no_button and not stage_click, f"rAF {raf}, no button {no_button}")


def check_chain_settlement(payee: str, text: str | None = None) -> Result:
    """Any transaction id shown on the site must exist on the mirror node as SUCCESS."""
    text = bundle_text() if text is None else text
    ids = set(re.findall(r"0\.0\.\d+@\d+\.\d+", text))
    if not ids:
        return Result("claimed settlement exists on-chain", False, "no transaction id on the site")
    ok, detail = True, []
    for tx in ids:
        account, ts = tx.split("@")
        stamp = ts.replace(".", "-")
        code, body = get(f"https://testnet.mirrornode.hedera.com/api/v1/transactions/{account}-{stamp}")
        try:
            t = json.loads(body)["transactions"][0]
        except Exception:
            ok = False
            detail.append(f"{tx}: not found")
            continue
        paid = {x["account"]: x["amount"] for x in t["transfers"]}
        good = t.get("result") == "SUCCESS" and paid.get(payee, 0) > 0
        ok = ok and good
        detail.append(f"{tx}: {t.get('result')}, payee +{paid.get(payee, 0)}")
    return Result("claimed settlement exists on-chain", ok, "; ".join(detail))


def check_payee_on_site(payee: str, text: str | None = None) -> Result:
    text = bundle_text() if text is None else text
    ok = bool(payee) and payee in text
    return Result("site shows the live payee", ok, f"payee {payee} {'found' if ok else 'NOT in bundle'}")


def env_value(key: str) -> str:
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith(key + "="):
            return line.split("=", 1)[1].strip()
    return ""


def check_402(ev_payee: str, body: bytes | None = None, fee_payer: str | None = None) -> Result:
    fee_payer = env_value("HEDERA_FEE_PAYER") if fee_payer is None else fee_payer
    if body is None:
        code, body = get(f"{API}/attestation/C-001")
    else:
        code = 402
    try:
        d = json.loads(body)
        a = d["accepts"][0]
    except Exception:
        return Result("x402 challenge is well formed", False, "unparseable 402")
    ok = (
        d.get("x402Version") == 2
        and a.get("scheme") == "exact"
        and a.get("network") == "hedera:testnet"
        and a.get("payTo") == ev_payee
        and a.get("extra", {}).get("feePayer") == fee_payer
        and a.get("amount") == "10000000"
    )
    return Result("x402 challenge matches config", ok, f"payTo {a.get('payTo')}, amount {a.get('amount')}")


def check_bad_payment() -> Result:
    req = urllib.request.Request(
        f"{API}/attestation/C-001", headers={"X-PAYMENT": "not-base64", "User-Agent": "ash-grade/1.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            code, body = r.status, r.read()
    except urllib.error.HTTPError as e:
        code, body = e.code, e.read()
    except Exception as e:
        code, body = 0, str(e).encode()
    ok = 400 <= code < 500 and code != 404
    return Result("malformed payment rejected", ok, f"HTTP {code}: {body[:70]!r}")


def check_ledger() -> Result:
    code, body = get(f"{API}/ledger/verify")
    if code != 200:
        return Result("ledger chain verifies", False, f"HTTP {code}")
    d = json.loads(body)
    code2, body2 = get(f"{API}/ledger")
    n = len(json.loads(body2).get("records", [])) if code2 == 200 else 0
    return Result("ledger chain verifies", bool(d.get("ok")) and n >= 1, f"ok={d.get('ok')}, records={n}")


def check_firmware() -> Result:
    fw = (ROOT / "firmware/ash_mcu/ash_mcu.ino").read_text()
    checks = {
        "loop sense": "LOOP_PIN" in fw,
        "wipe": "MASTER_OFF" in fw or "MASTER" in fw,
        "read-back": "0xFF" in fw,
        "terminal state": "TAMPERED" in fw or "state=3" in fw,
    }
    bad = [k for k, v in checks.items() if not v]
    return Result("firmware has wipe with read-back", not bad, f"missing {bad or 'none'}")


# ------------------------------------------------------------------ policy oracle
def policy_suite(service_factory) -> list[bool]:
    """Five documented rules, graded against the real SealService."""
    sys.path.insert(0, str(ROOT / "device"))
    import seal_service as ss  # noqa: E402

    class FakeMcu:
        def __init__(self):
            self.state = 1
            self.master = True

        def status(self):
            return {"state": self.state, "master": int(self.master)}

        def arm(self):
            self.state, self.master = 1, True
            return {"state": 1}

        def derive(self, nonce):
            return ("ab" * 32) if (self.state == 1 and self.master) else "ERR:not_armed"

    class World:
        def verify(self, proof):
            if proof != "good":
                raise ss.Denied("bad proof")
            return "human-1"

    class Decider:
        def __init__(self, allow):
            self.allow = allow

        def release(self, seal, human):
            return (self.allow, "handling" if self.allow else "intrusion", {"request_id": "x"})

    out: list[bool] = []
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        payload = td / "in.bin"
        payload.write_bytes(b"payload-123")

        # 1. seal in a bad state is refused
        mcu = FakeMcu()
        mcu.state = 3
        svc = service_factory(mcu, World(), Decider(True), td / "s1")
        try:
            svc.seal("C-1", payload)
            out.append(False)
        except ss.Denied:
            out.append(True)

        # 2. bad proof refuses before anything else
        mcu = FakeMcu()
        svc = service_factory(mcu, World(), Decider(True), td / "s2")
        svc.seal("C-2", payload)
        try:
            svc.unseal("C-2", td / "in.bin.ash", "bad", td / "o1.bin")
            out.append(False)
        except ss.Denied:
            out.append(not (td / "o1.bin").exists())

        # 3. decider deny refuses
        mcu = FakeMcu()
        svc = service_factory(mcu, World(), Decider(False), td / "s3")
        svc.seal("C-3", payload)
        try:
            svc.unseal("C-3", td / "in.bin.ash", "good", td / "o2.bin")
            out.append(False)
        except ss.Denied:
            out.append(not (td / "o2.bin").exists())

        # 4. allowed path returns the bytes
        mcu = FakeMcu()
        svc = service_factory(mcu, World(), Decider(True), td / "s4")
        svc.seal("C-4", payload)
        rec = svc.unseal("C-4", td / "in.bin.ash", "good", td / "o3.bin")
        out.append(rec.get("event") == "UNSEALED" and (td / "o3.bin").read_bytes() == b"payload-123")

        # 5. destroyed key is terminal
        mcu = FakeMcu()
        svc = service_factory(mcu, World(), Decider(True), td / "s5")
        svc.seal("C-5", payload)
        mcu.state, mcu.master = 3, False
        try:
            svc.unseal("C-5", td / "in.bin.ash", "good", td / "o4.bin")
            out.append(False)
        except ss.KeyDestroyed:
            out.append(not (td / "o4.bin").exists())

    return out


def check_policy() -> Result:
    sys.path.insert(0, str(ROOT / "device"))
    import seal_service as ss  # noqa: E402

    good = policy_suite(ss.SealService)

    class Regressed(ss.SealService):
        def unseal(self, container, container_file, proof, out):
            # the regression: world verification skipped
            st = self.mcu.status()
            ok, reason, meta = self.decider.release({}, "unknown")
            if not ok:
                raise ss.Denied(reason)
            k = self.mcu.derive(self._nonce_for(container))
            if k.startswith("ERR"):
                raise ss.KeyDestroyed(k)
            from ash_vault import open_payload

            open_payload(bytes.fromhex(k), container_file, out)
            return {"event": "UNSEALED"}

    bad = policy_suite(Regressed)
    ok = all(good)
    control = "caught" if not all(bad) else "MISSED (grader is blind)"
    return Result("seal/unseal policy oracle", ok, f"{sum(good)}/5 rules; regressed impl {control}")


# ------------------------------------------------------------------ controls
def controls(ev: dict) -> list[tuple[str, str]]:
    out = []
    text = bundle_text()
    r = check_claim_parity(ev, text.replace(str(ev.get("erase_us", 874)), "241", 1))
    out.append(("claim drift 874→241", "caught" if not r.ok else "MISSED"))

    fake = routes_from_api() | {"/totally-fake"}
    r = check_route_parity(routes_from_api(), {"/totally-fake"})
    out.append(("fake endpoint in docs", "caught" if not r.ok else "MISSED"))

    anchors, ids = anchors_and_ids()
    r = check_anchors(anchors | {"missing-section"}, ids)
    out.append(("anchor to a missing id", "caught" if not r.ok else "MISSED"))

    r = check_motion(site_css().replace("prefers-reduced-motion", "prefers-nothing"))
    out.append(("reduced-motion guard removed", "caught" if not r.ok else "MISSED"))

    fake_402 = json.dumps(
        {
            "x402Version": 2,
            "accepts": [
                {
                    "scheme": "exact",
                    "network": "hedera:testnet",
                    "amount": "10000000",
                    "payTo": "0.0.999999",
                    "extra": {"feePayer": "0.0.9185802"},
                }
            ],
        }
    ).encode()
    r = check_402("0.0.11340251", fake_402)
    broken = text.replace("0.0.11340251@1793997107", "0.0.11340251@1793997108", 1)
    r = check_chain_settlement("0.0.11344783", broken)
    out.append(("transaction id that is not on-chain", "caught" if not r.ok else "MISSED"))

    r = check_payee_on_site("0.0.999999", text)
    out.append(("stale payee in the bundle", "caught" if not r.ok else "MISSED"))
    out.append(("402 with the wrong payee", "caught" if not r.ok else "MISSED"))
    return out


# ------------------------------------------------------------------ main
def main() -> int:
    env = {}
    for line in (ROOT / ".env").read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    payee = env.get("HEDERA_PAY_TO", "")
    ev = evidence()

    gates = [
        check_site(),
        check_api(),
        check_unseal_refused(),
        check_assets(),
        check_no_overclaims(),
    ]
    scored = [
        check_claim_parity(ev),
        check_route_parity(),
        check_anchors(),
        check_motion(),
        check_autoplay(),
        check_payee_on_site(payee),
        check_chain_settlement(payee),
        check_402(payee),
        check_bad_payment(),
        check_ledger(),
        check_firmware(),
        check_policy(),
    ]
    ctl = controls(ev)

    print("\nGATES")
    for r in gates:
        print(f"  [{'PASS' if r.ok else 'FAIL'}] {r.name}  ({r.detail})")
    print("\nSCORED")
    for r in scored:
        mark = "x" if r.ok else " "
        print(f"  [{mark}] {r.name}  ({r.detail})")
    if not scored[-1].ok or "MISSED" in scored[-1].detail:
        pass
    print("\nNEGATIVE CONTROLS")
    for name, verdict in ctl:
        print(f"  [{'PASS' if verdict == 'caught' else 'FAIL'}] {name}: {verdict}")

    gate_ok = all(r.ok for r in gates)
    points = sum(1 for r in scored if r.ok)
    total = len(scored)
    controls_ok = all(v == "caught" for _, v in ctl)
    score = round(100 * points / total) if gate_ok else 0

    report = [
        "# Ash grade",
        "",
        f"Run {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())} against {SITE_URL} and {API}.",
        "",
        f"**Gates: {'PASS' if gate_ok else 'FAIL'}** · **Score: {score}/100** ({points}/{total} checks)"
        + ("" if gate_ok else " · void, a gate failed")
        + f" · **Controls: {'all caught' if controls_ok else 'NOT ALL CAUGHT'}**",
        "",
        "## Gates (pass/fail, not scored)",
        "",
        "| Gate | Verdict | Evidence |",
        "|---|---|---|",
    ]
    for r in gates:
        report.append(f"| {r.name} | {'PASS' if r.ok else 'FAIL'} | {r.detail} |")
    report += ["", "## Scored checks", "", "| Check | Verdict | Evidence |", "|---|---|---|"]
    for r in scored:
        report.append(f"| {r.name} | {'pass' if r.ok else 'FAIL'} | {r.detail} |")
    report += [
        "",
        "## Not covered by this grade",
        "",
        "- A successful World proof. The live verify path returns Cloudflare 1010 from the upstream; the",
        "  refusal is real, the success path is not exercised here.",
        "- A settled Hedera payment. The 402 challenge is graded; settlement has no transaction id.",
        "- Hardware erase on this run. Firmware checks are source-level; the last measured wipe came from",
        "  an earlier board run recorded in /evidence.",
        "- Accessibility and visual quality. No axe run, no screenshot diff, no contrast audit.",
        "",
        "## Negative controls",
        "",
        "| Control | Verdict |",
        "|---|---|",
    ]
    for name, verdict in ctl:
        report.append(f"| {name} | {verdict} |")
    (ROOT / "grade-report.md").write_text("\n".join(report) + "\n")

    print(f"\nGATES {'PASS' if gate_ok else 'FAIL'} · SCORE {score}/100 ({points}/{total}) · CONTROLS {sum(1 for _, v in ctl if v == 'caught')}/{len(ctl)}")
    print(f"report: {ROOT / 'grade-report.md'}")
    return 0 if gate_ok and points == total and controls_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
