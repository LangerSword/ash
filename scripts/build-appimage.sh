#!/usr/bin/env bash
# Build Ash-<version>-x86_64.AppImage from a clean checkout.
#   ./scripts/build-appimage.sh
# Requires: rust, node, npm, the .venv, rsvg-convert (icons), curl.
set -euo pipefail

root=$(cd "$(dirname "$0")/.." && pwd)
cd "$root"

version=$(sed -n 's/^version = "\(.*\)"/\1/p' app/src-tauri/Cargo.toml | head -1)
echo "ash $version"

echo "== frontend"
(cd app && npm install --include=dev --silent && npm run build)

echo "== service"
bash scripts/build-service.sh

echo "== rust"
(cd app/src-tauri && cargo build --release)

echo "== AppDir"
appdir="$root/dist/AppDir"
rm -rf "$appdir"
mkdir -p "$appdir/usr/bin" "$appdir/usr/share/applications" \
         "$appdir/usr/share/icons/hicolor/512x512/apps"

install -m 755 app/src-tauri/target/release/ash "$appdir/usr/bin/ash"
install -m 755 app/src-tauri/bin/ash-service "$appdir/usr/bin/ash-service"
install -m 644 app/src-tauri/icons/icon.png "$appdir/ash.png"
install -m 644 app/src-tauri/icons/icon.png "$appdir/usr/share/icons/hicolor/512x512/apps/ash.png"

cat > "$appdir/ash.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=Ash
Comment=Seal that destroys the data if you open it
Exec=ash
Icon=ash
Categories=Utility;Security;
Terminal=false
EOF
cp "$appdir/ash.desktop" "$appdir/usr/share/applications/ash.desktop"

cat > "$appdir/AppRun" <<'EOF'
#!/bin/sh
HERE=$(dirname "$(readlink -f "$0")")
exec "$HERE/usr/bin/ash" "$@"
EOF
chmod 755 "$appdir/AppRun"

echo "== appimagetool"
tool="${XDG_CACHE_HOME:-$HOME/.cache}/ash/appimagetool-x86_64.AppImage"
if [ ! -x "$tool" ]; then
  mkdir -p "$(dirname "$tool")"
  curl -fsSL -o "$tool" \
    https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage
  chmod +x "$tool"
fi

out="$root/dist/Ash-$version-x86_64.AppImage"
rm -f "$out"
APPIMAGE_EXTRACT_AND_RUN=1 ARCH=x86_64 "$tool" "$appdir" "$out"
chmod +x "$out"

echo
echo "built: $out"
ls -lh "$out"
