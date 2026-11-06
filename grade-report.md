# Ash grade

Run 2026-11-06 20:33 UTC against https://langersword.github.io/ash/ and https://api.langersword.in.

**Gates: PASS** · **Score: 100/100** (12/12 checks) · **Controls: all caught**

## Gates (pass/fail, not scored)

| Gate | Verdict | Evidence |
|---|---|---|
| site reachable | PASS | HTTP 200, 1572 B |
| api status | PASS | HTTP 200, keys ['amber', 'counter', 'loop', 'master', 'state'] |
| unseal refuses empty proof | PASS | HTTP 403: b'{"ok": false, "error": "WorldError: proof is not a JSON object"}' |
| shipped assets match source | PASS | 3/3 identical |
| no settlement/mainnet overclaims | PASS | banned hits: none |

## Scored checks

| Check | Verdict | Evidence |
|---|---|---|
| site numbers match /evidence | pass | missing none, stale 240µs False |
| docs endpoints exist in the handler | pass | 7 listed, missing none |
| nav anchors resolve | pass | 6 anchors, missing none |
| reduced-motion guard on motion | pass | guard True, section-rise True |
| hero plays without a click | pass | rAF True, no button True |
| site shows the live payee | pass | payee 0.0.11344783 found |
| claimed settlement exists on-chain | pass | 0.0.11340251@1793997107.642204384: SUCCESS, payee +10000000 |
| x402 challenge matches config | pass | payTo 0.0.11344783, amount 10000000 |
| malformed payment rejected | pass | HTTP 402: b'{"ok": false, "error": "bad X-PAYMENT: Invalid base64-encoded string: ' |
| ledger chain verifies | pass | ok=True, records=23 |
| firmware has wipe with read-back | pass | missing none |
| seal/unseal policy oracle | pass | 5/5 rules; regressed impl caught |

## Not covered by this grade

- A successful World proof. The live verify path returns Cloudflare 1010 from the upstream; the
  refusal is real, the success path is not exercised here.
- A settled Hedera payment. The 402 challenge is graded; settlement has no transaction id.
- Hardware erase on this run. Firmware checks are source-level; the last measured wipe came from
  an earlier board run recorded in /evidence.
- Accessibility and visual quality. No axe run, no screenshot diff, no contrast audit.

## Negative controls

| Control | Verdict |
|---|---|
| claim drift 874→241 | caught |
| fake endpoint in docs | caught |
| anchor to a missing id | caught |
| reduced-motion guard removed | caught |
| transaction id that is not on-chain | caught |
| stale payee in the bundle | caught |
| 402 with the wrong payee | caught |
