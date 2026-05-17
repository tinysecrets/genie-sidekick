#!/usr/bin/env bash
# infrastructure/tailscale_setup.sh
# Bridge the Lubuntu Command Center to the HP Pavilion Workhorse via Tailscale.
#
# Run this on BOTH machines after installing Tailscale.
# https://tailscale.com/download/linux

set -euo pipefail

if ! command -v tailscale >/dev/null 2>&1; then
  echo "Installing Tailscale..."
  curl -fsSL https://tailscale.com/install.sh | sh
fi

NODE_NAME="${1:-$(hostname)}"
echo "Bringing up tailscale as node: $NODE_NAME"
sudo tailscale up --hostname="$NODE_NAME" --ssh

echo
echo "Tailscale IPs:"
tailscale ip -4
echo
echo "Both nodes are now on a single WireGuard network."
echo "Test from this node:"
echo "  tailscale ping <other-node-name>"
