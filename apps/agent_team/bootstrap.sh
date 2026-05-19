#!/usr/bin/env bash
# bootstrap.sh — one-command setup for the Sovereign Team Repository
#
# Usage:
#   bash bootstrap.sh                # full setup (prompts for Super Key, pulls models)
#   bash bootstrap.sh --no-models    # skip Ollama model pulls
#   bash bootstrap.sh --ci           # non-interactive (reads SUPER_KEY env var)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

NO_MODELS=0
CI_MODE=0
for arg in "$@"; do
  case "$arg" in
    --no-models) NO_MODELS=1 ;;
    --ci)        CI_MODE=1 ;;
    *) echo "Unknown flag: $arg"; exit 2 ;;
  esac
done

c_green()  { printf "\033[32m%s\033[0m\n" "$*"; }
c_yellow() { printf "\033[33m%s\033[0m\n" "$*"; }
c_red()    { printf "\033[31m%s\033[0m\n" "$*"; }
c_bold()   { printf "\033[1m%s\033[0m\n" "$*"; }

c_bold "==============================================="
c_bold "  Sovereign Team Repository — Bootstrap"
c_bold "==============================================="
echo

# ---------- 1. Python deps ----------
c_green "[1/5] Installing Python dependencies..."
if ! command -v python3 >/dev/null 2>&1; then
  c_red "python3 not found. Install Python 3.10+ and re-run."
  exit 1
fi
python3 -m pip install --quiet --upgrade pip
python3 -m pip install --quiet -r "$REPO_ROOT/requirements.txt"

# ---------- 2. Super Key ----------
c_green "[2/5] Initializing Super Key (L0)..."
if [[ "$CI_MODE" -eq 1 ]]; then
  if [[ -z "${SUPER_KEY:-}" ]]; then
    c_red "CI mode requires SUPER_KEY env var."
    exit 1
  fi
  python3 scripts/init_super_key.py --from-env
else
  python3 scripts/init_super_key.py
fi

# ---------- 3. Derive lower-tier keys ----------
c_green "[3/5] Deriving Master, Pseudo, and Agent keys..."
python3 scripts/derive_keys.py --all

# ---------- 4. Encrypted vault ----------
c_green "[4/5] Sealing encrypted vault (AES-256-GCM)..."
python3 scripts/encrypt_vault.py

# ---------- 5. Free local models (optional) ----------
if [[ "$NO_MODELS" -eq 0 ]]; then
  c_green "[5/5] Pulling free local models via Ollama..."
  if ! command -v ollama >/dev/null 2>&1; then
    c_yellow "Ollama not installed. Skipping model pulls."
    c_yellow "Install: curl -fsSL https://ollama.com/install.sh | sh"
  else
    while IFS= read -r model; do
      [[ -z "$model" || "$model" =~ ^[[:space:]]*# ]] && continue
      echo "  -> ollama pull $model"
      ollama pull "$model" || c_yellow "  (skip: $model)"
    done < <(python3 scripts/list_models.py)
  fi
else
  c_yellow "[5/5] Skipping model pulls (--no-models)."
fi

echo
c_bold "==============================================="
c_green "Bootstrap complete."
c_bold "==============================================="
cat <<'EOF'

Next:
  python3 agents/genie/genie.py "your first goal"

Read the charter:
  less instructions.md

Tweak agent roles (optional):
  $EDITOR config/agents.yaml

EOF
