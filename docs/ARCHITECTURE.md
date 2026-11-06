# Architecture

## Tiers

- **Tier 0 — hard break.** Loop open continuously for 250 ms → erase the MASTER page, read back
  0xFF, write `TAMPERED{reason:"open"}`, LED red. Terminal, offline, no MPU involvement.
- **Tier 1 — ambiguous.** Partial/drifting/bouncing event → amber, keep the key, start
  `DEADLINE_MS = max(5000, 2*p95)` (cap 8000). MCU computes features:
  `{v_min, v_max, v_mean, edges, open_ms, since_arm_ms, counter, policy}`. 0G returns
  `{"decision":"hold|wipe","cause":"handling|intrusion|unknown"}`. The model may hold until the
  deadline or request a wipe; it can never un-wipe or extend. Timeout/invalid ⇒ wipe, recorded as
  `0G_UNAVAILABLE`, never disguised as a verdict. `hold` clears only after 2 s of stable closed.
- **Tier 2 — authorised unseal.** World device grant → `(iss, sub)` → 0G `release|deny` with
  `verify_tee: true`. Deny/timeout/unreachable ⇒ no key, `UNSEAL_DENIED`.
- **Tier 3 — audit.** Async hash-chained episodes to 0G Storage, off the hot path.

## Key handling

- `MASTER` in MCU flash, never returned.
- Seal: `K = HMAC-SHA256(MASTER, nonce||container)`; host derives the AES key with HKDF-SHA256,
  encrypts with AES-256-GCM, then wipes `K` from memory (tested).
- Unseal: Tier 2 only.
- Tamper: erase MASTER page, verify 0xFF, increment the counter page, sign the record.

## Flash layout (measured)

| Region | Offset | Size |
|---|---|---|
| MASTER page | 2080768 | 8192 B |
| counter page | 2072576 | 8192 B |
| storage_partition | 1835008 | 262144 B |

Wipe-pending flag lives on the counter page: set before erase, cleared after read-back verification;
on boot, a set flag completes the wipe before anything else.

## Threat model

Holds: an attacker with the box but without the owner's World identity cannot obtain `K`; after
tamper the ciphertext is useless.
Does not hold: the host sees `K` at seal time (a compromised sender host can retain it); the UNO Q
is not a certified secure element; the loop only covers the path it runs through; shorting the loop
defeats a DC sense; RDP is unverified.

## Network

Board is on ETHGlobal WiFi and reaches 0G and World directly. A USB relay exists as a fallback
(`tools/relay.py`, `adb reverse tcp:9000`); when used, TLS terminates on the laptop and the
disclosure applies.
