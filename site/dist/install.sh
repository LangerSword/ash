#!/usr/bin/env bash
# Ash installer. Checks what it needs, then sets up the app for this user.
set -euo pipefail

REPO="${ASH_REPO:-https://github.com/LangerSword/ash}"
DEST="${ASH_HOME:-$HOME/.local/share/ash}"
BIN="${ASH_BIN:-$HOME/.local/bin}"

say() { printf '  %s\n' "$*"; }
ok()  { printf '  \033[32mok\033[0m  %s\n' "$*"; }
bad() { printf '  \033[31mmissing\033[0m  %s\n' "$*"; }

echo
echo "ash installer"
echo

fail=0
for c in git python3 adb; do
  if command -v "$c" >/dev/null 2>&1; then ok "$c"; else bad "$c"; fail=1; fi
done

if command -v python3 >/dev/null 2>&1; then
  if python3 - <<'PY'
import sys
raise SystemExit(0 if sys.version_info >= (3, 10) else 1)
PY
  then ok "python >= 3.10"; else bad "python >= 3.10"; fail=1; fi
fi

if command -v adb >/dev/null 2>&1; then
  n=$(adb devices 2>/dev/null | awk 'NR>1 && $2=="device"' | wc -l | tr -d ' ')
  if [ "${n:-0}" -ge 1 ]; then ok "board visible to adb ($n)"; else say "no board on adb yet; connect the UNO Q and enable USB debugging"; fi
fi

if [ "$fail" -ne 0 ]; then
  echo
  echo "install the missing tools, then run this again"
  exit 1
fi

echo
if [ -d "$DEST/.git" ]; then
  say "updating $DEST"
  git -C "$DEST" fetch --depth 1 origin master >/dev/null 2>&1
  git -C "$DEST" reset --hard origin/master >/dev/null
else
  say "cloning into $DEST"
  mkdir -p "$(dirname "$DEST")"
  git clone --depth 1 "$REPO" "$DEST" >/dev/null
fi

say "creating the venv"
python3 -m venv "$DEST/.venv"
"$DEST/.venv/bin/pip" install --quiet --upgrade pip
if [ -f "$DEST/requirements.txt" ]; then
  "$DEST/.venv/bin/pip" install --quiet -r "$DEST/requirements.txt"
else
  "$DEST/.venv/bin/pip" install --quiet fastapi uvicorn
fi

mkdir -p "$BIN"
cat > "$BIN/ash" <<EOF
#!/usr/bin/env bash
set -euo pipefail
cd "$DEST"
export ASH_MCU="\${ASH_MCU:-board}"
export ASH_WORLD="\${ASH_WORLD:-idkit}"
exec "$DEST/.venv/bin/python" device/demo_api.py "\$@"
EOF
chmod +x "$BIN/ash"

echo
ok "installed"
say "run:  ash"
say "open: http://127.0.0.1:8080/site/"
case ":$PATH:" in
  *":$BIN:"*) : ;;
  *) say "note: $BIN is not on PATH; add it or run $BIN/ash" ;;
esac
echo
