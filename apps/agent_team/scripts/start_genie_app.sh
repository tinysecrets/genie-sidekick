#!/usr/bin/env bash
# Double-click friendly launcher for the local Genie interface.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

HOST="${DREAM_UI_HOST:-127.0.0.1}"
PORT="${DREAM_UI_PORT:-8765}"
URL="http://${HOST}:${PORT}"
LOG_DIR="$ROOT/.local/logs"
mkdir -p "$LOG_DIR"

if [[ ! -f "$ROOT/keys/vault/keys.enc" ]]; then
  if [[ -z "${SUPER_KEY:-}" ]]; then
    if command -v zenity >/dev/null 2>&1; then
      SUPER_KEY="$(zenity --password --title='Genie Super Key')"
      export SUPER_KEY
    else
      printf '%s\n' "Genie needs a SUPER_KEY before first launch."
      printf '%s\n' "Run bootstrap once or launch with SUPER_KEY set."
      exit 1
    fi
  fi
  SUPER_KEY="$SUPER_KEY" bash bootstrap.sh --ci --no-models
fi

if command -v ollama >/dev/null 2>&1; then
  if ! curl -fsS "http://127.0.0.1:11434/api/tags" >/dev/null 2>&1; then
    nohup ollama serve >"$LOG_DIR/ollama.log" 2>&1 &
    sleep 2
  fi
else
  printf '%s\n' "Ollama is not installed. Install it or store a cloud token."
fi

if ! curl -fsS "$URL/api/health" >/dev/null 2>&1; then
  nohup python3 scripts/ui_server.py >"$LOG_DIR/genie-ui.log" 2>&1 &
  sleep 1
fi

if command -v xdg-open >/dev/null 2>&1; then
  xdg-open "$URL" >/dev/null 2>&1 || true
elif command -v open >/dev/null 2>&1; then
  open "$URL" >/dev/null 2>&1 || true
else
  printf 'Genie is awake at %s\n' "$URL"
fi
