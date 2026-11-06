# Ash Desktop — build brief (AppImage, solo)

**For:** a fresh Hermes session, no prior context.
**Owner:** one person, ~2 days of build time. **Ship target:** a working AppImage on Linux x86_64.
**Repo:** https://github.com/LangerSword/ash · **Live API:** https://api.langersword.in · **Site:** https://langersword.github.io/ash/

Read `README.md`, `docs/ARCHITECTURE.md`, `docs/SECURITY.md`, `demo-script.md` first. Do not restate
them; build on them.

---

## 0. Contract

1. **Real integrations only.** Every device call goes to the board's local API or `adb`; every sponsor
   call goes to a real endpoint. No mocked buttons in the shipped app.
2. **No invented APIs.** The backend contract is in `website-brief-v2.md` §7. If a field is missing,
   add it to the backend and document it; never guess client-side.
3. **Fail visibly.** Every failure path has a human-readable state and a next action. A spinner that
   never resolves is a bug.
4. **Never claim what is not true.** No settled Hedera payment until a transaction id exists; no
   production World identity (sandbox only); no secure-element claim.
5. **Ship one artefact.** `Ash-<version>-x86_64.AppImage`, runnable on a clean Arch/Ubuntu without
   `npm install`.

---

## 1. What the app is

**Ash Desktop** is the product, not a wrapper around the website. It owns the seal:

- Detects an Arduino UNO Q over USB, opens the device link, and shows the board's live state.
- Seals a file or folder (encrypts with a key derived on the MCU), unseals with a World ID proof,
  and shows the hash-chained ledger.
- Runs a first-launch intro and a legend for the LED-matrix symbols.
- Works without the website; the website only distributes it.

The app is a **trust instrument**: one window, one job, no dashboards.

---

## 2. Stack

| Concern | Choice | Why |
|---|---|---|
| Shell | **Tauri v2** (Rust backend) | ~10 MB binary, real filesystem/USB access, AppImage bundling built in |
| UI | **Svelte 5 + Vite + TypeScript** | reuse the design tokens and components from `site/` |
| Styling | plain CSS + the existing tokens | no Tailwind |
| Animation | **GSAP** (already a dependency) | timeline-driven intro and state transitions |
| Device | `adb` CLI from Rust (`std::process`) + the board's HTTP API | no native USB stack to write |
| Sign-in | World IDKit through the existing backend | no credentials stored in the app |
| Packaging | `tauri build --bundles appimage` | plus `AppDir/` desktop entry, icon, `ash.desktop` |

**Fallback** if Tauri blocks on `webkit2gtk` in the build container: Python 3.12 + PySide6 + PyInstaller,
still AppImage. Do not use Electron — 120 MB for a seal terminal is wrong.

---

## 3. Device integration

1. On launch, poll `adb devices` every 2 s.
2. States: `absent` → show "Connect the UNO Q over USB"; `unauthorized` → "Authorise USB debugging on
   the board"; `device` → `adb forward tcp:8081 tcp:8080`, then `GET /status`.
3. If the board's app is not running (`/status` refuses), offer a **Start board app** button that runs
   `adb shell arduino-app-cli app start ~/ArduinoApps/ash-fw`.
4. udev: ship `99-ash-unoq.rules` with the board's VID/PID so non-root adb works; install with a polkit
   prompt on first run. If the rule is missing, explain how to add it instead of failing silently.
5. Reconnect: a USB replug must recover without restarting the app; keep the last ledger visible and
   mark it stale.

**Edge cases to handle explicitly:** two boards connected (pick the saved serial, else ask), adb server
not running (`adb start-server`), port 8081 already bound (pick 8092 and store it), board on a different
firmware without `/flex` (fall back to `/sim`), board clock wrong (do not depend on it).

---

## 4. First run

1. **Intro animation** (see §5), 4 s, skippable.
2. **Device check** — one screen: what was found, what to do if not.
3. **Sign in with World** — optional; explains that it is only needed to unseal. Sandbox identity is
   labelled as such.
4. **Legend overlay** — a small card over the matrix mapping every symbol:
   - solid breathing = ARMED · amber bars = TIER 1 / deadline · falling dots = WIPE · red X = TAMPERED
     · green diamond = UNSEALED · blank = OFFLINE
   "Got it" dismisses it and writes `legend_seen: true` to `~/.config/ash/config.json`. A "?" button
   reopens it. **Do not show it again automatically.**
5. **Two caveats on the first screen:** no board → still usable for viewing the ledger; no network → the
   0G tier is unavailable and the app says so before the user acts.

---

## 5. The intro animation

**Concept:** a box opens, burns, and becomes ash — rendered both in-app and on the board's 13×8 matrix.

- In-app: a GSAP timeline, 3.6 s. A 1px wireframe box (SVG) draws itself, the lid rotates open, a burn
  front eats the box from one corner, and the residue collapses into particles that fall and settle into
  the word `ASH` (letterspaced, monospace). Ends on the status chip.
- On the board: the same beats as 104-pixel frames over `/frame` (add this endpoint: `POST /frame`
  with `{"frames": ["0101...", ...], "fps": 12}`; the MCU sketch renders each frame). If the endpoint is
  missing, skip the on-device intro and say so — never fake it.
- `prefers-reduced-motion`: no burn, no particles; a 400 ms fade to the wordmark and a static frame.
- The animation must be interruptible by any click and must not block device polling.

**Status display in the app:** a persistent 13×8 mirror of the board (same renderer as the site), plus a
one-line state machine readout (`ARMED · counter 0 · master present`) and the last episode hash.

---

## 6. Packaging

```
app/
  src-tauri/        Rust: adb, HTTP client, config, tray
  src/              Svelte UI (shared tokens with site/)
  resources/        99-ash-unoq.rules, icons, legend.json
  AppDir/           AppRun, ash.desktop, ash.png
```

- `npm run tauri build` → `target/release/bundle/appimage/Ash_<v>_amd64.AppImage`.
- Desktop entry: `Name=Ash`, `Comment=Seal that destroys the data if you open it`, `Categories=Utility;Security;`.
- Config in `~/.config/ash/config.json`: `serial`, `api_port`, `legend_seen`, `world_sub` (opaque), `last_ledger_hash`.
- No auto-update in v1; check for a newer release on GitHub releases and show a link.

---

## 7. Error handling matrix

| Failure | Detect | UI |
|---|---|---|
| No board | `/device` state `absent` | amber line + "Connect the UNO Q"; Seal disabled |
| USB not authorised | `unauthorized` | exact adb instruction |
| Board app stopped | `/device` `forwarded` > 5 s | "Start board app" button |
| Port in use | bind error | pick next free port, persist it |
| 0G timeout | request > deadline | "0G did not answer; the seal will wipe at the deadline" (never a spinner) |
| 0G refuses | 4xx | show the request id and the model's reason verbatim |
| World cancelled | poll error | "No proof — nothing was released", LED stays red |
| Hedera 402 unpaid | 402 | explain the price and the payee; do not auto-pay |
| Ledger hash mismatch | verify fails | red banner, link to the last valid record |
| Disk full / permission denied | OS error | path + errno + remediation |

Every error is one sentence of cause and one sentence of action. No stack traces in the UI; log them to
`~/.local/state/ash/app.log`.

---

## 8. Acceptance

1. Fresh machine, `chmod +x Ash.AppImage && ./Ash.AppImage` opens to the intro, then the device screen.
2. With a board plugged in: seal → ledger row; flex loop → amber countdown; cut loop → TAMPERED.
3. Legend shows once, "?" reopens it, restarting the app does not show it again.
4. Unplug the board mid-session: app stays open, marks state stale, reconnects on replug without restart.
5. Kill the tunnel: the app shows 0G unavailable and refuses irreversible actions; no fabricated verdict.
6. `prefers-reduced-motion`: intro has no burn/particles.
7. Window at 800×600 and on a 200 % DPI screen: no clipping, matrix square.
8. Nothing in the UI claims a settled Hedera payment unless `/attestation` returned a tx id.

---

## 9. Scope discipline (solo)

**Must:** device link, seal/unseal, ledger, status mirror, intro, legend, error matrix, AppImage.
**Should:** tray icon, start-board-app button, reduced motion.
**Won't:** auto-update, Windows/macOS, multi-device, cloud sync, account system beyond World.

If the build slips: ship without the on-device intro (in-app only) and without the tray. Never ship
without the error matrix or the legend.
