# Lubuntu — Command Center Node

The Lubuntu machine is your pristine **Command Center**. It holds the Super Key
and runs Genie. Keep it lean.

## Setup

```bash
sudo apt update && sudo apt install -y git python3 python3-pip curl
git clone <your-fork-of-this-repo> emergent-team
cd emergent-team
bash bootstrap.sh
```

## Recommended posture

- Full-disk encryption (LUKS) on the home partition.
- Auto-suspend disabled (so long Ollama pulls finish).
- Firewall: allow only outbound + Tailscale.
- No browser plugins. No social media accounts logged in.
- No second user account.

## What runs here

- `agents/genie/genie.py`  (the supervisor)
- The vault (`keys/vault/`)
- The Super Key passphrase (in your head only)

## What does NOT run here

- VirtualBox sandboxes — those live on the HP Pavilion.
- Ollama with large 70B models — too heavy. Use small models locally and call
  the HP Pavilion over Tailscale for heavy inference.

## Calling the HP Pavilion's Ollama

```bash
export OLLAMA_HOST="http://pavilion.tail-net.ts.net:11434"
python agents/genie/genie.py "your goal"
```

Replace `pavilion.tail-net.ts.net` with the Tailscale MagicDNS name of the HP Pavilion.
