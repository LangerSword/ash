# Ash — a seal that destroys the data if you open it

A tamper-responsive seal for confidential shipments. A wire loop runs through the case lid into the
UNO Q's MCU. The payload is encrypted under a key derived from a secret that never leaves the chip.
A hard break wipes the key in about a millisecond, offline. An ambiguous event is sent to 0G, which
decides hold or wipe against a hard deadline — and no answer means wipe. Authorised unsealing needs
World authentication and a 0G release decision. An agent pays $0.01 in USDC over x402 on Hedera to
read the history and refuse the delivery.

**Status:** build in progress (ETHGlobal Mumbai, 6–7 Nov 2026). Nothing here is finished; the
README is updated as gates pass.

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

## Layout

```
firmware/ash_mcu/   STM32 sketch (state machine, flash, sensing)
device/             Python service (vault, 0G, World, Hedera)
tools/              relay, time sync, test scripts
docs/               ARCHITECTURE, SECURITY, AI_USE
```

## Setup

TODO — filled in as the components land.
