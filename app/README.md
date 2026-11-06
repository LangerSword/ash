# Ash Desktop

The product, not a wrapper around the site. One window, one job: detect the UNO Q, seal and unseal a
payload, show the hash-chained ledger. Tauri v2 shell (Rust) + Svelte 5 + GSAP; AppImage on Linux
x86_64.

```
app/
  src-tauri/src/device.rs    adb detection, the forward, board /status, board-app start, udev
  src-tauri/src/service.rs   attach to :8080, or spawn the bundled Python service
  src-tauri/src/config.rs    ~/.config/ash/config.json, ~/.local/state/ash/app.log
  src/                       Svelte UI (intro, device check, legend, console)
  src-tauri/bin/ash-service  PyInstaller build of device/demo_api.py (gitignored)
```

## Build

```bash
./scripts/build-appimage.sh          # -> dist/Ash-0.1.0-x86_64.AppImage
```

The script builds the frontend, the Python sidecar, the Rust binary, assembles an AppDir and runs
`appimagetool`.

Two build traps this script handles, both of which produce a **blank window**:

- the release binary must be compiled with `--features custom-protocol`, otherwise Tauri navigates to
  `devUrl` (`localhost:5183`) instead of the embedded bundle and shows a connection error;
- cargo does not track `app/dist`, so a frontend-only change does not re-embed the bundle. The script
  touches `src-tauri/src/lib.rs` before building to force it.

Requirements: Rust, Node, a `.venv` with `cryptography` (PyInstaller is installed on
demand), `rsvg-convert`, `curl`, and a system `webkit2gtk-4.1` at runtime.

Dev loop:

```bash
python3 device/demo_api.py           # the service the app attaches to
cd app && npm install --include=dev && npm run dev
cd app/src-tauri && cargo run        # or: npm run tauri dev
```

## The signature

The in-app intro and the board play the same film: the wordmark takes ink, a burn front crosses it
left to right, embers fall, and the word reforms (`src/lib/intro-frames.ts`, 40 frames, 14 fps).

The board copy is fired by **Rust**, not the webview: the UI arms it once (`arm_signature`) and the
device thread plays it the first time the board answers in that process. A hidden or throttled
webview cannot swallow it, and a board that is plugged in later still gets its play.

## How the pieces split

- **Rust owns the device link.** `adb devices` every 2 s, `adb forward tcp:<port> tcp:8080`, probe
  `/status`, install the udev rule through `pkexec`. If the board is present but its app is not
  answering for two polls, Rust starts it itself (30 s cooldown) — the common "connected but dead"
  case recovers without the user finding a button. The device screen keeps working when the Python
  service is down.
- **The Python service owns the protocol.** Seal/unseal, the vault, World verification, the 0G
  decision, Hedera x402. The app never reimplements it; it speaks the same contract as the site.
- **Svelte owns the window.** Intro, legend, matrix mirror, controls, ledger, event log.

Service resolution at launch: `ASH_API_URL` if set, else an existing API on `127.0.0.1:8080`, else the
bundled `ash-service` on a free port with state in `~/.local/share/ash`. When the app spawns the
service it passes `ASH_LINK=0` (Rust already owns adb) and `ASH_MCU_URL` for the chosen forward.

## Config and state

| path | contents |
|---|---|
| `~/.config/ash/config.json` | `serial`, `api_port`, `legend_seen`, `intro_seen`, `world_sub`, `last_ledger_hash` |
| `~/.local/state/ash/app.log` | one line per action and failure (no stack traces in the UI) |
| `~/.local/state/ash/service.log` | the spawned service's stderr |
| `~/.local/share/ash/state/` | ledger and sealed payloads, when the app spawns its own service |

## What is real

- Every device action goes to the board over adb and its HTTP API. No mocked buttons.
- The intro frames really are pushed to the MCU (`POST /frame`, 43 frames at 12 fps) and rendered on
  the 13×8 matrix; if the firmware lacks the endpoint the app says so and plays the intro in-app only.
- Ledger verification runs server-side (`GET /ledger/verify`) against the same hash chain the writer
  uses, so a mismatch is a real mismatch.

## What is not

- World ID proofs are sandbox credentials; the UI labels them wherever they appear.
- Hedera settlement is only claimed when `/attestation/:container` returns a transaction id. The app
  never pays automatically; it shows the 402 price and payee.
- No tray icon in v1, no auto-update, Linux only.

## Endpoints added for the app

| endpoint | why |
|---|---|
| `POST /frame {"frames": ["0101…"], "fps": 12}` | play a host-generated animation on the matrix (max 64 frames, 104 chars each) |
| `GET /ledger/verify` | verify the hash chain server-side; `409` with the offending record index on mismatch |
| `arm_signature` (Tauri command) | UI hands Rust the 40 frames; Rust plays them on first contact |
| `GET /evidence` gains `mock` and `world` | so the UI can label a mock 0G decision or a static World verifier honestly |

Service env knobs used by the desktop build: `ASH_API_PORT`, `ASH_STATE_DIR`, `ASH_MCU_URL`,
`ASH_LINK=0`, `ASH_SERIAL`.
