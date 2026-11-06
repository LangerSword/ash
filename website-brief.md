# Ash — website brief for Claude

**Written:** 6 Nov 2026, 15:55 IST · **Submission:** 7 Nov, 09:00 IST
**Scope:** a single-page site that explains Ash and runs the live demo from the browser.
**Time-box:** 90 minutes to first deploy, 60 more for polish. After that it is done, whatever state it is in.

---

## 0. Contract

1. **No framework, no build step.** Static `site/index.html` + `site/styles.css` + `site/app.js`. It must run with `python3 -m http.server` on any machine, offline except for the API.
2. **No invented content.** Every number, quote and claim comes from this brief, `README.md`, or the live API. If a figure is missing, render `—` rather than a guess.
3. **The demo panel is real.** It calls the local API; when the API is down it must say so plainly, never fake state.
4. **The page must be honest about limitations.** The disclosures section is not optional and not hidden behind a click.
5. **No stock illustrations, no gradients, no glassmorphism, no emoji-as-icon, no "AI startup" copy.** Dark instrument panel, not a landing page template.

---

## 1. What the site is for

A judge has four minutes. The site has to do three things in that order:

1. **Explain the product in ten seconds** — a seal that destroys the data if someone opens it.
2. **Prove it is real** — a live panel wired to the actual MCU, with the real numbers and request ids on screen.
3. **Be honest** — what is hardware, what is mocked, what would break in production.

It is not a marketing site. It is an instrument panel with a narrative around it.

---

## 2. Structure and verbatim copy

Single page, sections in this order. Copy below is final; do not paraphrase.

### 2.1 Header
Wordmark: `ASH`
Right side: a live status chip — one of `ARMED`, `AMBER`, `TAMPERED`, `OFFLINE` — driven by `GET /status`.
Under the wordmark, one line:

> A seal that destroys the data if you open it.

### 2.2 The problem
Three short paragraphs, left-aligned, max 62 characters per line.

> Confidential material still moves in boxes. Discovery files, prototypes, samples, evidence. The only protection is a plastic seal and a signature.
>
> A plastic seal proves nothing. A server-side delete can be paused, rolled back, or subpoenaed.
>
> Ash puts the detector and the key in the same offline computer, inside the seal. Break the loop and the key is gone in about a millisecond. Bend it, and a model decides whether that was handling or intrusion — against a deadline, where silence means wipe.

Small caption under it, monospaced, muted:

> NIST SP 800-88r2 recognises cryptographic erase · ISO 17712 is the mechanical seal it upgrades · DPDP Act 2023 s.8(7) requires erasure

### 2.3 How it works — three tiers
A vertical stack of three rows, each with a tier number, a one-line title, and two lines of detail. Keep it dense and factual.

**Tier 0 — local wipe.** `250 ms` of continuous open → erase `MASTER`, read back `0xFF`, record `TAMPERED`. No network, no host, no model.
**Tier 1 — ambiguous event.** Amber. The MCU sends a feature vector to 0G and starts a deadline. The model may hold until the deadline or ask for a wipe; it can never un-wipe. No answer means wipe, logged as `0G_UNAVAILABLE`.
**Tier 2 — authorised unseal.** A World ID proof, then a 0G `release|deny` decision, then the MCU releases the payload key. Deny, timeout or no network: no key.

Under the three rows, a single line:

> The model is never on the kill path. It is in the loop, with a deadline, and it fails closed.

### 2.4 Live demo panel
The centrepiece. Two columns on desktop, stacked on mobile.

**Left: the matrix mirror.** A 13 × 8 CSS grid of 104 cells that reproduces the device's LED matrix state:
- `ARMED`: a breathing fill, rows lighting bottom-up, 8 steps, ~4 s cycle.
- `AMBER`: bars draining right-to-left, proportional to the remaining deadline.
- `TAMPERED`: a pulsing X.
- `UNSEALED`: a diamond.
- `OFFLINE`: all cells off, muted.

**Right: controls and state.**
Buttons: `Seal container` · `Unseal with World ID` · `Unseal (test proof)` · `Break loop` · `Reprovision`
Under them, a definition list:

```
state      ARMED | AMBER | TAMPERED
counter    0
master     present | erased
loop       closed | open
deadline   5000 ms
last 0G    <request id>   <latency> ms
```

**Below: the ledger.** A table of the last 8 records from `GET /ledger`: `event`, `container`, `at` (HH:MM:SS), `0G` (decision or `—`), `hash` (first 8 chars). Monospace, tabular numbers, no zebra stripes.

**Below that: the event log.** A single `<pre>` that streams what the buttons did, newest last, with timestamps. No fake lines.

If the API is unreachable: the panel shows `DEVICE OFFLINE` and the buttons disable. One sentence underneath: "The demo API is not running. Start it with `python3 device/demo_api.py`."

### 2.5 Evidence
A four-column table, exactly these rows, with the measured values:

| what | measured | where |
|---|---|---|
| flash page erase | 874 µs | STM32U585 |
| wipe + read-back | 1 321 µs | STM32U585 |
| bridge round trip | p50 6.19 ms / p95 7.20 ms | 1 000 calls, 0 errors |
| Tier 1 decision | 2.05 s median, p95 2.11 s | gpt-4.1-mini via 0G Router |
| decision cost | $0.000038 | 0G Router trace |
| deadline | 5 000 ms | max(5000, 2 × p95) |

Caption: "Every number was produced by a run on the board during this event. Request ids and ledger hashes are in the repository."

### 2.6 What breaks if 0G is removed
> Nothing detects the ambiguous case. The seal falls back to a hard rule: any interruption wipes. Safe, and unusable for normal handling.

### 2.7 Disclosures
A bordered block, same visual weight as the rest. Do not hide it.

> **What this is not.** The UNO Q is not a certified secure element; a bench attacker with SWD can read flash, because readout protection is unverified. The loop only covers the path it runs through, and shorting it defeats a DC sense. The payload key exists on the host at seal time. World ID proofs here are sandbox credentials. When the USB relay is used, network egress passes through the laptop.

### 2.8 Footer
Repo link, team names, the three tracks: `0G Physical AI` · `World IDKit` · `Hedera x402`. A line: "Built at ETHGlobal Mumbai, 6–7 November 2026."

---

## 3. Design system

**Palette**
```
bg          #0b0b0c
surface     #121214
border      #222226
text        #e8e8e8
muted       #8a8a8a
signal      #5ad46a   (armed, success)
amber       #ffb020   (tier 1, pending)
alert       #ff5c5c   (tampered, error)
```
One accent per state, never two at once. No gradients, no glows, no shadows except a 1px border.

**Type**
- UI: `ui-monospace, SFMono-Regular, Menlo, monospace` at 14px/1.55. Headings use the same family, heavier weight, tighter tracking.
- Display line (hero one-liner): 32–40px, weight 500, letter-spacing −0.02em.
- Numbers everywhere: `font-variant-numeric: tabular-nums`.

**Layout**
- Max width 1080px, 24px gutters, sections separated by 96px and a 1px rule.
- The demo panel is the only thing above the fold on desktop; everything else scrolls.
- No cards inside cards. No rounded corners above 4px.

**Motion**
- State transitions: 120ms opacity/colour only. Never bounce, never spring.
- The matrix mirror is the only continuously animating element.
- `prefers-reduced-motion`: freeze the matrix on its current frame and remove the countdown animation (the bar may jump in steps).

**Accessibility**
- Contrast ≥ 4.5:1 for body text; ≥ 3:1 for large text and UI borders.
- Every control reachable by keyboard, visible focus ring in `signal` at 2px offset.
- Status changes announced via `aria-live="polite"` on the status chip.
- The matrix grid is `aria-hidden`; the same information is in the definition list.

---

## 4. Live API contract

Base: `http://127.0.0.1:8080`. All responses JSON, CORS already open.

```
GET  /status        -> {"state":1,"counter":0,"master":1,"loop":0}
POST /seal          {"container":"C-001","owner":"human-001"}
POST /unseal        {"container":"C-001","proof":"good"}
POST /sim           {"closed":0}          # break (1 = closed)
POST /reprovision   {}
GET  /ledger        -> {"records":[...]}
```

State mapping: `1 = ARMED`, `3 = TAMPERED`, anything else = `OFFLINE` for display purposes.
Poll `/status` every 1 000 ms; poll `/ledger` after every action, not on a timer.
On any fetch failure: set `OFFLINE`, disable the buttons, keep the last known values visible but muted.

**Countdown.** `POST /sim {"closed":0}` starts Tier 1 on the device; the page cannot read the deadline directly, so animate the bar from 100% to 0 over 5 000 ms and stop when `/status` reports `TAMPERED`. Do not invent a different duration.

---

## 5. Files

```
site/
  index.html
  styles.css
  app.js
  README.md      # how to run, what the API needs
```

Serve with:

```bash
cd ~/projects/ash && python3 -m http.server 8090 -d site
```

The demo panel talks to `127.0.0.1:8080`; the World helper (port 7070) is a separate page and is not part of this site.

---

## 6. Acceptance

1. Loads with the API **down**: panel says `DEVICE OFFLINE`, buttons disabled, no console errors.
2. Loads with the API **up**: chip reads `ARMED`; `Seal container` writes a ledger row within 2 s; `Break loop` flips the chip to `TAMPERED` and the matrix to the X within 1 s.
3. `Unseal (test proof)` returns a payload and adds an `UNSEALED` row.
4. Keyboard only: tab to every button, activate with Enter, focus always visible.
5. 360px wide: no horizontal scroll, matrix still square, controls stack.
6. `prefers-reduced-motion`: no continuous animation, information still readable.
7. No external network requests. No fonts, scripts or images from a CDN.
8. Lighthouse: performance ≥ 95, accessibility ≥ 95.

---

## 7. Non-goals

- No routing, no framework, no state library, no SSR.
- No auth, no analytics, no cookie banner, no newsletter.
- No fake testimonials, no invented "backed by", no team photos.
- No second page. The submission is one URL.

---

## 8. Open questions

1. Does the submission want a hosted URL, or is `localhost` acceptable for judges? If hosted, the demo panel needs a tunnel to the API — decide before deploying.
2. The World button depends on a valid RP signing key; until then it should render disabled with `World: not configured` rather than throwing.
3. Should the ledger show hashes in full on hover? Default: first 8 characters, full value in `title`.
