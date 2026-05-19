#!/usr/bin/env bash
# Copy Genie to a Lubuntu notebook over SSH/Tailscale and install the launcher.
#
# Usage:
#   scripts/deploy_lubuntu.sh user@lubuntu-tailnet-name
#   scripts/deploy_lubuntu.sh user@100.x.y.z ~/Genie
#
# By default the encrypted local vault is not copied. Bootstrap on the notebook
# with your Super Key after deploy.

set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "Usage: $0 user@tailscale-host [remote-dir]" >&2
  exit 2
fi

REMOTE="$1"
REMOTE_DIR="${2:-~/Genie}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARCHIVE="$(mktemp -t genie-team.XXXXXX.tar.gz)"

cleanup() {
  rm -f "$ARCHIVE"
}
trap cleanup EXIT

cd "$ROOT"

tar \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='.pytest_cache' \
  --exclude='.ruff_cache' \
  --exclude='.local' \
  --exclude='keys/vault' \
  --exclude='*.pyc' \
  -czf "$ARCHIVE" .

echo "Sending Genie to $REMOTE:$REMOTE_DIR ..."
ssh "$REMOTE" "mkdir -p '$REMOTE_DIR'"
scp "$ARCHIVE" "$REMOTE:/tmp/genie-team.tar.gz"

ssh "$REMOTE" "cd '$REMOTE_DIR' && tar -xzf /tmp/genie-team.tar.gz && rm /tmp/genie-team.tar.gz && chmod +x scripts/*.sh && scripts/install_lubuntu_launcher.sh"

cat <<EOF
Genie has landed on $REMOTE.

Next on the Lubuntu notebook:
  cd $REMOTE_DIR
  SUPER_KEY='your-long-super-key' bash bootstrap.sh --ci --no-models
  ollama serve
  ollama pull qwen2.5:1.5b

Then click Genie from the desktop/app menu.
EOF
