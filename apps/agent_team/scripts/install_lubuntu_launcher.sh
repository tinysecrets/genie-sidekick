#!/usr/bin/env bash
# Install Genie as a clickable launcher on Lubuntu/LXQt.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LAUNCHER="$ROOT/scripts/start_genie_app.sh"
APP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
APP_FILE="$APP_DIR/genie.desktop"
DESKTOP_DIR="${XDG_DESKTOP_DIR:-$HOME/Desktop}"

chmod +x "$LAUNCHER"
mkdir -p "$APP_DIR"

cat >"$APP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=Genie
Comment=Open the local Genie creation environment
Exec=$LAUNCHER
Path=$ROOT
Icon=applications-development
Terminal=false
Categories=Development;Utility;
EOF

chmod +x "$APP_FILE"

if [[ -d "$DESKTOP_DIR" ]]; then
  cp "$APP_FILE" "$DESKTOP_DIR/Genie.desktop"
  chmod +x "$DESKTOP_DIR/Genie.desktop"
fi

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$APP_DIR" >/dev/null 2>&1 || true
fi

printf 'Genie launcher installed.\n'
printf 'App menu entry: %s\n' "$APP_FILE"
if [[ -d "$DESKTOP_DIR" ]]; then
  printf 'Desktop icon:   %s\n' "$DESKTOP_DIR/Genie.desktop"
fi
