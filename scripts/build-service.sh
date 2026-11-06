#!/usr/bin/env bash
# Build the Python service into a single binary that the AppImage carries.
set -euo pipefail

root=$(cd "$(dirname "$0")/.." && pwd)
py="$root/.venv/bin/python"

if [ ! -x "$py" ]; then
  echo "no .venv at $root/.venv — create one with: uv venv .venv && uv pip install --python .venv/bin/python cryptography" >&2
  exit 1
fi

if ! "$py" -c "import PyInstaller" >/dev/null 2>&1; then
  echo "installing pyinstaller into .venv"
  uv pip install --python "$py" pyinstaller
fi

mkdir -p "$root/app/src-tauri/bin"
"$py" -m PyInstaller \
  --onefile \
  --name ash-service \
  --paths "$root/device" \
  --distpath "$root/app/src-tauri/bin" \
  --workpath /tmp/ash-pybuild \
  --specpath /tmp/ash-pybuild \
  "$root/device/demo_api.py"

ls -lh "$root/app/src-tauri/bin/ash-service"
