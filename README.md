# Ash — a seal that destroys the data if you open it

A tamper-responsive seal for confidential shipments. A wire loop runs through the case lid into the
UNO Q's MCU. The payload is encrypted under a key derived from a secret that never leaves the chip.
A hard break wipes the key in about a millisecond, offline. An ambiguous event is sent to 0G, which
decides hold or wipe against a hard deadline — and no answer means wipe. Authorised unsealing needs
World authentication and a 0G release decision. An agent pays $0.01 in USDC over x402 on Hedera to
read the history and refuse the delivery.

**Status:** live on hardware, hosted, ETHGlobal Mumbai 2026.

- Site: https://langersword.github.io/ash/ (Svelte 5 + GSAP, deployed by GitHub Actions)
- API: https://api.langersword.in (named Cloudflare tunnel to the laptop)
- Demo script: `demo-script.md` · submission copy: `submission-copy.md`
- Run locally: `python3 device/demo_api.py` and `cd site && npm run dev`

## Why

Confidential material still moves in boxes. A plastic seal proves nothing, and a server-side delete
can be paused, rolled back, or subpoenaed. Ash puts the detector and the key in the same offline
computer, inside the seal.

## Architecture

```
case lid ── wire loop ──► STM32 (ADC/digital, 200 Hz)
                            │  Tier 0: break > 250 ms → erase MASTER, read back 0xFF, LED red
                            │  Tier 1: ambiguous → features → 0G hold|wipe, deadline, fail-closed
                            │  Tier 2: unseal → World token + 0G release|deny → key
                            ▼
                     arduino-router (JSON, 115200)
                            ▼
                  MPU (Debian, Python): vault, relay client, World, Hedera
```

## What breaks if 0G is removed

Nothing detects the ambiguous case, so the seal falls back to a hard rule: any interruption wipes.
That is safe but unusable for handling, which is why the model sits in the loop.

## Measured facts

- Flash: 8 KB pages; MASTER page at offset 2080768; erase 874 µs, write 254 µs, wipe with read-back 1321 µs.
- Bridge: 1000 calls, 0 errors, p50 6.19 ms, p95 7.20 ms.
- Board network: ETHGlobal WiFi, direct HTTPS works (0G 200, World sandbox 200).

## Tier 0 on hardware (measured 6 Nov, 09:15 UTC)

```
selftest      ok            # SHA-256 and HMAC-SHA256 against published vectors
status        state=1 counter=0 master=1 loop=0
derive(x2)    identical      # deterministic, from MCU-held MASTER
open loop     state=3 counter=1 master=0   # wipe, read-back verified
derive after  ERR:not_armed  # key is gone
reprovision   state=1 master=1             # dev-only
```

## Live 0G decision (measured 6 Nov, 10:50 UTC)

| call | model | latency | request id (from `x_0g_trace`) | decision |
|---|---|---|---|---|
| Tier 1 classify | gpt-4.1-mini (default) | 2.05 s | `3538c131-2f3f-4213-ab6e-e70fbf830620` | hold / handling |
| Tier 2 release | gemini-2.5-flash-lite | 1.88 s | `18f73aef-3789-40e3-987d-178d2174d79f` | release / consistent |

Note: `glm-5.2` is a reasoning model (254 reasoning tokens, ~7 s) and misses a 5 s deadline;
gemini-2.5-flash-lite returns strict JSON in ~1.8 s. The Router does not surface a TEE verdict on
this provider, so `tee_verified` is recorded as `unknown`, never `true`.

## Tier 1 on hardware (measured 6 Nov, 11:12 UTC)

```
ambiguous   edges=1 open_ms=130 deadline=6000
0G verdict  hold / handling   request_id 5990999b-06cd-4022-835b-484d15f08a55   relay 2449 ms
hold        cleared after 2 s stable closed -> state 1 (ARMED)
ambiguous   again, no decision
timeout     wipe at the deadline -> state 3, counter 1, master 0   (fail-closed)
```

Note: the app container cannot do TLS on this platform (WRONG_VERSION_NUMBER on every HTTPS
origin), so decisions go container -> host forwarder :9001 -> USB -> laptop relay -> 0G.
Board-direct TLS is flaky on venue WiFi. The laptop relay is the documented egress.

## The site

Svelte 5 + Vite + GSAP, dark instrument panel, no framework beyond that. It polls `/device` and
`/status`, mirrors the board's 13×8 matrix, and drives seal / unseal / cut / reprovision through the
API. With no board attached it says `DEVICE OFFLINE` and disables the controls.

```bash
python3 device/demo_api.py          # API on :8080, talks to the board over adb
cd site && npm install && npm run dev   # site on :5173
```

`site/public/config.json` holds the API base used by the hosted build. If the tunnel changes, update
that file and push; Actions redeploys.

## The desktop app

`app/` is the product: a Tauri v2 shell (Rust) with a Svelte 5 UI. It detects the board over adb,
seals and unseals payloads, mirrors the 13×8 matrix, shows the hash-chained ledger, and ships as one
AppImage.

```bash
./scripts/build-appimage.sh          # -> dist/Ash-0.1.0-x86_64.AppImage
```

It attaches to a running `device/demo_api.py` on :8080, or spawns its own bundled copy on a free port.
`app/README.md` documents the split between the Rust device link, the Python service and the UI, and
the endpoints added for it (`POST /frame`, `GET /ledger/verify`, `evidence.mock|world`).

## Layout

```
firmware/ash_mcu/   STM32 sketch (state machine, flash, sensing, host frames)
firmware/ash_app/   the board's Python bridge (server.py)
device/             Python service (vault, 0G, World, Hedera)
app/                Ash Desktop (Tauri + Svelte): the AppImage
tools/              relay, time sync, test scripts
docs/               ARCHITECTURE, SECURITY, AI_USE
scripts/            build-service.sh, build-appimage.sh
```

## Setup

TODO — filled in as the components land.
