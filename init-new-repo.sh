#!/usr/bin/env bash
# ----------------------------------------------------------------------
# init-new-repo.sh — push /app/genie-sidekick to a brand-new GitHub repo
#
# Run this on YOUR LOCAL machine after you've cloned the Wah-Lah repo
# (or downloaded the genie-sidekick folder).
#
# Prereqs:
#   1. Create an empty repo on GitHub, e.g. github.com/<you>/genie-sidekick
#   2. Have git configured locally (git config --global user.email/name)
#   3. SSH key OR HTTPS Personal Access Token set up for github.com
#
# Usage:
#   cd genie-sidekick
#   ./init-new-repo.sh git@github.com:Jrs092393/genie-sidekick.git
# ----------------------------------------------------------------------
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <git-remote-url>"
  echo "Example: $0 git@github.com:Jrs092393/genie-sidekick.git"
  exit 1
fi

REMOTE="$1"

if [[ -d .git ]]; then
  echo "[!] .git already exists in $(pwd). Aborting to avoid clobbering."
  exit 1
fi

if [[ ! -f README.md ]] || [[ ! -d backend ]] || [[ ! -d frontend ]]; then
  echo "[!] Run this from inside the genie-sidekick/ folder."
  exit 1
fi

echo "[+] Initializing fresh git repo..."
git init -b main
git add .
git commit -m "Initial commit: Genie standalone sidekick"

echo "[+] Adding remote: $REMOTE"
git remote add origin "$REMOTE"

echo "[+] Pushing to remote..."
git push -u origin main

echo ""
echo "✅ Done. Genie now lives at $REMOTE"
echo "   Next: deploy backend on Render/Fly.io and frontend on Vercel/Netlify."
echo "   See README.md for deploy instructions."
