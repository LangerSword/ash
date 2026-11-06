# Ash — website brief v2 (Svelte + GSAP + wallets + backend contract)

**Owner:** wckdnya (frontend). **Backend + device:** Lakshaya.
**Repo:** https://github.com/LangerSword/ash (public) — write access granted to `wckdnya`.
**Submission:** 7 Nov 2026, 09:00 IST. **Time-box for v1 of the site:** 4 hours, then polish only.

---

## 0. Ownership and workflow

- `site/` is yours. `device/`, `firmware/`, `tools/` are mine — read them, open issues, don't rewrite them without saying so.
- Branch per feature (`site/hero`, `site/demo-panel`), PR into `master`, squash merge. Small commits, every ≤90 min.
- The API is the contract. If you need a field that isn't in §7, ping me; do not invent it client-side.
- Never commit `.env`, keys, or the board's credentials. `.gitignore` already covers them.

---

## 1. What the site is

A judge has four minutes and no patience. The site does three things, in this order:

1. **Explain it in ten seconds** — a seal that destroys the data if someone opens it.
2. **Prove it is real** — a live panel wired to the actual MCU, with real numbers and request ids on screen.
3. **Be honest** — what is hardware, what is mocked, what would break in production.

It is an instrument panel with a narrative around it, not a startup landing page. No stock art, no gradients, no glass cards, no "revolutionising" copy.

---

## 2. Stack

| Concern | Choice | Notes |
|---|---|---|
| Framework | **Svelte 5 + Vite + TypeScript** | SPA, no SvelteKit. One route. |
| Animation | **GSAP** (`gsap`, `ScrollTrigger`) | Plus Svelte transitions for state. Nothing else. |
| Styling | Plain CSS with custom properties | No Tailwind. Design tokens in `src/styles/tokens.css`. |
| Icons | Inline SVG, 16px grid | No icon fonts. |
| Wallets | `@hashgraph/hedera-wallet-connect` + WalletConnect, `wagmi` + `viem` for EVM | See §8. |
| Build | `vite build` → `site/dist` | Static; the API is a separate origin. |

No router, no store library, no SSR, no CSS-in-JS.

---

## 3. Page structure and copy

Copy below is final. Do not paraphrase. Sections in order.

### 3.1 Hero
Wordmark `ASH`, status chip (`ARMED` / `AMBER` / `TAMPERED` / `OFFLINE`) bound to the API.
Display line, 40px, max 18 words:

> A seal that destroys the data if you open it.

Sub-line, muted:

> The key lives in the chip. Cut the loop and it is gone in a millisecond.

Below, three short facts in a row, monospaced, tabular:
`1 321 µs wipe` · `2.05 s 0G decision` · `5 000 ms deadline`

### 3.2 Problem
Three short paragraphs, max 62 characters per line.

> Confidential material still moves in boxes. Discovery files, prototypes, samples, evidence. The only protection is a plastic seal and a signature.
>
> A plastic seal proves nothing. A server-side delete can be paused, rolled back, or subpoenaed.
>
> Ash puts the detector and the key in the same offline computer, inside the seal. Break the loop and the key is gone. Bend it, and a model decides whether that was handling or intrusion — against a deadline, where silence means wipe.

Caption: `NIST SP 800-88r2 recognises cryptographic erase · ISO 17712 is the mechanical seal it upgrades · DPDP Act 2023 s.8(7) requires erasure`

### 3.3 Three tiers
Three stacked rows. Number, title, two lines each.

**Tier 0 — local wipe.** `250 ms` of continuous open → erase `MASTER`, read back `0xFF`, record `TAMPERED`. No network, no host, no model.
**Tier 1 — ambiguous event.** Amber. The MCU sends a feature vector to 0G and starts a deadline. The model may hold until the deadline or ask for a wipe; it can never un-wipe. Silence means wipe, logged as `0G_UNAVAILABLE`.
**Tier 2 — authorised unseal.** A World ID proof, then a 0G `release|deny`, then the MCU releases the payload key. Deny, timeout or no network: no key.

Closing line: `The model is never on the kill path. It is in the loop, with a deadline, and it fails closed.`

### 3.4 Live demo panel
Two columns on desktop, stacked on mobile.

**Matrix mirror.** A 13 × 8 CSS grid of 104 cells mirroring the device:
- `ARMED` — breathing fill, rows bottom-up, 8 steps, 4 s cycle.
- `AMBER` — bars draining right-to-left over the deadline.
- `TAMPERED` — pulsing X.
- `UNSEALED` — diamond.
- `OFFLINE` — all off, muted.

**Controls.**
`Seal container` · `Unseal with World ID` · `Unseal (test proof)` · `Break loop` · `Reprovision`

**State list** (definition list, tabular numbers):
```
state      ARMED | AMBER | TAMPERED | OFFLINE
counter    0
master     present | erased
loop       closed | open
deadline   5000 ms
last 0G    <request id>   <latency> ms
```

**Ledger table.** Last 8 records: `event`, `container`, `time`, `0G`, `hash` (first 8 chars, full in `title`).

**Event log.** A `<pre>` streaming what the buttons did, with timestamps. No fabricated lines.

API down → `DEVICE OFFLINE`, buttons disabled, one line: "Start the demo API with `python3 device/demo_api.py`."

### 3.5 Evidence
| what | measured | where |
|---|---|---|
| flash page erase | 874 µs | STM32U585 |
| wipe + read-back | 1 321 µs | STM32U585 |
| bridge round trip | p50 6.19 ms / p95 7.20 ms | 1 000 calls, 0 errors |
| Tier 1 decision | 2.05 s median, p95 2.11 s | gpt-4.1-mini via 0G Router |
| decision cost | $0.000038 | 0G Router trace |
| deadline | 5 000 ms | max(5000, 2 × p95) |

Caption: `Every number came from a run on the board during this event.`

### 3.6 What breaks without 0G
> Nothing detects the ambiguous case. The seal falls back to a hard rule: any interruption wipes. Safe, and unusable for normal handling.

### 3.7 Disclosures
Bordered block, same weight as the rest, never collapsed.

> **What this is not.** The UNO Q is not a certified secure element; a bench attacker with SWD can read flash, because readout protection is unverified. The loop covers only the path it runs through, and shorting it defeats a DC sense. The payload key exists on the host at seal time. World ID proofs here are sandbox credentials. When the USB relay is used, network egress passes through the laptop.

### 3.8 Footer
Repo, team (`Lakshaya`, `Ananya`), tracks `0G Physical AI · World IDKit · Hedera x402`, and `Built at ETHGlobal Mumbai, 6–7 November 2026`.

---

## 4. Design system

```
--bg       #0b0b0c     --surface  #121214    --border #222226
--text     #e8e8e8     --muted    #8a8a8a
--signal   #5ad46a     --amber    #ffb020    --alert  #ff5c5c
```
One accent at a time. No gradients, no glows, no shadows beyond a 1px border. Radius ≤ 4px.

Type: `ui-monospace, SFMono-Regular, Menlo, monospace` everywhere, 14px/1.55 body, display 40px weight 500 tracking −0.02em. Numbers: `font-variant-numeric: tabular-nums`.

Layout: max 1080px, 24px gutters, 96px between sections with a 1px rule. The demo panel is the only thing above the fold on desktop.

---

## 5. GSAP choreography

Only where it carries meaning. Durations are ceilings, not targets.

1. **Hero load (one timeline, ≤900 ms).** Wordmark mask-reveal, then the display line rises 12px with opacity, then the three facts stagger 60 ms. `power2.out`. No bounce.
2. **Section reveals (ScrollTrigger).** Each section: 1px rule draws from 0 → 100% width, then content fades up 8px. `start: "top 80%"`, `once: true`. Do not animate the evidence table rows individually.
3. **Tier 1 countdown.** The amber bar is a GSAP tween from 100% → 0 over exactly `5000 ms`, started when the state becomes `AMBER`, killed on `TAMPERED` or `ARMED`. It is a visual clock, not decoration; keep it in sync with the API.
4. **Ledger insert.** New row: height 0 → auto with opacity, 180 ms. Never animate on poll refresh — only on a genuinely new record (compare hash).
5. **State transition.** Chip background and colour tween 120 ms; no movement.
6. `prefers-reduced-motion`: skip 1, 2 and 4; keep 3 but step it in 500 ms increments; no continuous animations.

Do not animate: the matrix grid cells (Svelte drives them), the ledger on refresh, anything on scroll past the demo panel.

---

## 6. Accessibility

- Contrast ≥ 4.5:1 body, ≥ 3:1 large text and borders.
- Every control keyboard reachable; focus ring `--signal`, 2px offset.
- `aria-live="polite"` on the status chip; `aria-hidden` on the matrix.
- Buttons have `aria-busy` while their action is in flight and are disabled during it.
- Reduced motion respected everywhere, including the countdown.

---

## 7. Backend contract (I implement this; you consume it)

Base `http://127.0.0.1:8080`, CORS `*`, JSON.

```
GET  /status                -> {"state":1,"counter":0,"master":1,"loop":0,"amber":0}
GET  /ledger                -> {"records":[{"event":"SEALED","container":"C-001","at":1793966324,"hash":"…","0g":{…}}]}
GET  /evidence              -> {"erase_us":874,"wipe_us":1321,"bridge_p50_ms":6.19,"bridge_p95_ms":7.2,"tier1_p50_s":2.05,"tier1_cost_usd_micro":38,"deadline_ms":5000}
GET  /events                -> text/event-stream: event: status | ledger | tier1, data: JSON
GET  /device                -> {"state":"ready|forwarded|unauthorized|absent|error","serial":"…","api":"http://127.0.0.1:8081","mcu":{…},"detail":"…"}
POST /seal                  {"container":"C-001","owner":"human-001"} -> {"ok":true,"record":{…}}
POST /unseal                {"container":"C-001","proof":"<idkit result | \"good\">"} -> {"ok":true,"payload":"…","record":{…}} | 403 {"ok":false,"error":"…"}
POST /sim                   {"closed":0|1} -> {"mcu":"{…}"}
POST /reprovision           {} -> {"mcu":"{…}"}
GET  /world/config          -> {"app_id":"app_…","rp_id":"rp_…","action":"unseal","ready":true|false}
POST /world/rp-signature    {} -> {"sig":"0x…","nonce":"…","created_at":…,"expires_at":…}
GET  /wallet/nonce?chain=hedera&account=0.0.1234 -> {"message":"Ash demo login\nnonce: …\nissued: …"}
POST /wallet/verify         {"chain":"hedera","account":"0.0.1234","signature":"…"} -> {"ok":true,"account":"0.0.1234"}
GET  /attestation/:container -> 402 {"x402Version":2,"accepts":[{scheme:"exact",network:"hedera:testnet",amount:"10000",asset:"<HTS id>",payTo:"0.0.x",extra:{feePayer:"0.0.y"}}]}
                               paid -> 200 {"ok":true,"attestation":{…},"tx_id":"…","hashscan":"https://hashscan.io/…"}
                               503 {"ok":false,"error":"hedera_not_configured"} when unset — never a fake settlement
```

State mapping: `1 = ARMED`, `3 = TAMPERED`; `amber` true means Tier 1 in progress. Anything unreachable = `OFFLINE` on the client.

Error shape is always `{"ok":false,"error":"<message>"}` with 4xx/5xx. Never a 200 with an error inside.

---

## 8. Wallet integration

Two wallets, two honest jobs. Neither holds custody of the payload, neither is required to unseal.

**A. Hedera wallet (HashPack / Blade) — proves who funds the agent.**
- `@hashgraph/hedera-wallet-connect` `DAppConnector`, WalletConnect Cloud projectId (free; put it in `.env` as `VITE_WC_PROJECT_ID`).
- Request only `hedera_signMessage` and the account id. No transaction signing on the site.
- Flow: connect → GET `/wallet/nonce?chain=hedera&account=…` → sign the message in the wallet → POST `/wallet/verify` → the backend checks the signature against the account's key (Mirror Node) and stores a session.
- UI: a small panel under the demo — `Agent payer` with the account id, a `Connect` button, and a verified checkmark.

**B. EVM wallet (MetaMask / Coinbase / WalletConnect) — proves the operator's address.**
- `wagmi` + `viem`, injected connector first, WalletConnect fallback.
- `personal_sign` the same nonce, POST `/wallet/verify` with `chain:"evm"`; backend recovers the address with `viem.verifyMessage`.
- UI: same panel, second row.

**What the wallets do not do:** they do not decrypt the payload, do not authorise unsealing, and do not pay the x402 fee in this demo — the agent's own key settles that server-side. Say this in one line under the panel: `Wallets prove control here. They do not hold the payload key.`

If `VITE_WC_PROJECT_ID` is missing, render the panel disabled with `WalletConnect not configured` and keep the rest working.

---

## 9. Files and ownership

```
site/
  index.html
  package.json
  vite.config.ts
  src/
    main.ts
    App.svelte
    styles/tokens.css
    styles/app.css
    lib/api.ts          # typed client for §7
    lib/store.svelte.ts # status, ledger, events
    components/Hero.svelte
    components/TierStack.svelte
    components/DemoPanel.svelte
    components/MatrixMirror.svelte
    components/Ledger.svelte
    components/WalletPanel.svelte
    components/Disclosures.svelte
    components/Footer.svelte
  public/
```

`src/lib/api.ts` is the only place that talks to the API. Everything else takes props.

Run: `cd site && npm install && npm run dev` (Vite on 5173). The API must be running for the demo panel; the rest of the page works without it.

---

## 10. Skills to install if you don't have them

If Claude doesn't already have these, install them before writing UI:

- `omh-frontend` — design-system-first workflow, component contracts.
- `gsap-core`, `gsap-timeline`, `gsap-scrolltrigger` — the animation patterns in §5.
- `design-taste-frontend` — anti-generic layout and type rules.
- `web-app-verification` — scripted browser checks for §11.
- `dogfood` — exploratory QA once it runs.

Ask for them by name; if a skill is missing, say so and build without it rather than inventing a workflow.

---

## 11. Acceptance

1. API **down**: panel shows `DEVICE OFFLINE`, buttons disabled, no console errors, rest of the page fully readable.
2. API **up**: chip reads `ARMED`; `Seal container` adds a ledger row within 2 s; `Break loop` flips chip to `TAMPERED` and matrix to the X within 1 s; `Unseal (test proof)` returns a payload and adds `UNSEALED`.
3. Countdown: starting `Break loop` produces an amber bar that drains over 5 s and stops when the state flips.
4. Wallet: connect, sign, verified checkmark. With no projectId, the panel is disabled and explains why.
5. Keyboard only: every control reachable, focus visible, no traps.
6. 360px: no horizontal scroll, matrix square, controls stack.
7. `prefers-reduced-motion`: no continuous animation, countdown still legible.
8. Zero external network requests (no CDN fonts, scripts or images).
9. Lighthouse ≥ 95 performance and accessibility; no console errors on load or interaction.

---

## 12. Deployment decision

The live panel must reach `127.0.0.1:8080`. Two options:
1. **Judges use the laptop** — build `site/dist`, serve with `python3 -m http.server 8090 -d site/dist`, open `localhost:8090`. Simplest, no tunnel.
2. **Hosted URL** — GitHub Pages for the explainer, but the demo panel needs a tunnel to the API (Cloudflare Tunnel or Tailscale Funnel). If we host, the panel must degrade gracefully to `DEVICE OFFLINE` and the recorded evidence table carries the proof.

Default: option 1 for the demo video, option 2 if the submission needs a public link. Confirm before deploying.


---

## 13. References (take the pattern, not the pixels)

Spend fifteen minutes with these before writing CSS. Take **type scale, spacing rhythm, table density,
motion restraint, and copy honesty**. Do not copy layouts, and take nothing from the marketing sections.

| Site | What to take | What to leave |
|---|---|---|
| `linear.app` | restrained motion, one accent, dense-but-calm hierarchy | the gradient hero, the glow |
| `vercel.com` | black-on-black layering with 1px borders, monospace metadata | the grid noise |
| `stripe.com/docs` | documentation-grade tables and code blocks with real values | the illustrations |
| `raycast.com` | keyboard-first interactions, 120 ms state transitions | the glass |
| `github.com` (repo view) | status colours used as information, not decoration | the chrome |
| `tailscale.com` | engineer-to-engineer copy, diagrams that explain a mechanism | the long-form blog tone |
| `instrument.com` | scale contrast — 40px display against 12px metadata | the editorial serif |

The rule that comes out of them: **one idea per screen, one accent at a time, and every animation
earns its place by showing a state change.**

---

## 14. Device autodetect (the site must do this without a manual step)

The backend watches for the board and reports it; the site reflects it.

```
GET /device -> {"state":"ready","serial":"3017640407","api":"http://127.0.0.1:8081",
                "mcu":{"state":1,"counter":0,"master":1,"loop":0},"detail":""}
```

States and UI:

| state | meaning | UI |
|---|---|---|
| `ready` | board found, API answering | controls enabled; chip shows device state; `serial` in the footer of the panel |
| `forwarded` | board found, app not answering yet | controls disabled; `Booting the board…` |
| `unauthorized` | USB debugging not allowed | `Authorise USB debugging on the board` |
| `absent` | no board on USB | `Connect a UNO Q over USB` |
| `error` | adb or forward failed | show `detail` verbatim |

Poll `/device` every 2 s, alongside `/status`. When the state changes to `ready`, do a single
`Seal`-less refresh: fetch `/ledger` and `/status` once, then resume polling. Never enable a button
on a stale `ready`.

The detection itself lives in `device/link.py`: `adb devices` → pick the known serial → `adb forward
tcp:8081 tcp:8080` → `GET /status`. The site does not talk to adb; it only reads `/device`.

---

## 15. Track integration (what the site must surface)

Each track has a short, factual line in the evidence section and its own page in `docs/tracks/`.

| track | what is real today | what is pending | where the site says it |
|---|---|---|---|
| **0G Physical AI** | decision in the loop, request id per decision, 2.05 s p50, safe-stop that wipes | 0G Storage episode uploader | Evidence table + Tier 1 row + ledger `0G` column |
| **World IDKit** | IDKit page, verify client, nullifier stored, denial path | a valid 32-byte RP signing key | Tier 2 row + the unseal button's disabled state |
| **Hedera x402** | v2 `exact` challenge, verify/settle client, HashScan URL | funded testnet account + facilitator | `/attestation` panel: `402 → settled → tx id` |

Do not claim a settled Hedera payment until there is a transaction id on screen. Do not claim a World
proof until a real nullifier comes back.

---

## 16. Hosted URLs (current)

- Site: `https://langersword.github.io/ash/` (GitHub Pages, deployed by Actions from `docs/`; it builds
  `site/` automatically once `site/package.json` exists).
- Live API + same page from one origin: the current tunnel URL, stored in `docs/config.json` as
  `apiBase`. If the tunnel restarts, update that file with one commit.
- The panel must read `apiBase` from `config.json` at runtime, not from a build-time constant.
