# Ash grade

Run 2026-11-06 20:44 UTC against https://langersword.github.io/ash/ and https://api.langersword.in.

**Gates: FAIL** · **Score: 0/100** (9/12 checks) · void, a gate failed · **Controls: NOT ALL CAUGHT**

## Gates (pass/fail, not scored)

| Gate | Verdict | Evidence |
|---|---|---|
| site reachable | PASS | HTTP 200, 1572 B |
| api status | FAIL | HTTP 530, unparseable |
| unseal refuses empty proof | FAIL | HTTP 530: b'error code: 1033\n' |
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
| x402 challenge is well formed | FAIL | unparseable 402 |
| malformed payment rejected | FAIL | HTTP 530: b'error code: 1033\n' |
| ledger chain verifies | FAIL | HTTP 530 |
| firmware has wipe with read-back | pass | missing none |
| seal/unseal policy oracle | pass | 5/5 rules; regressed impl caught |

## Not covered by this grade

- A successful World proof. The Cloudflare block is fixed (403/1010 was the bare Python-urllib
  agent); a success still needs a World App scan of the connector, or a staging app for the simulator.
- Hardware erase unless ASH_GRADE_HW=1. The default run checks the firmware source only.
- Visual quality. Accessibility is measured separately with axe (0 WCAG 2.1 A/AA violations at the
  time of writing); no screenshot diff is part of this grade.

## Negative controls

| Control | Verdict |
|---|---|
| claim drift 874→241 | MISSED |
| fake endpoint in docs | caught |
| anchor to a missing id | caught |
| reduced-motion guard removed | caught |
| transaction id that is not on-chain | caught |
| stale payee in the bundle | caught |
| 402 with the wrong payee | caught |
