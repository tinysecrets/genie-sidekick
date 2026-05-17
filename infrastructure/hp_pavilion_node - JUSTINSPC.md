# HP Pavilion — Heavy Workhorse Node

The HP Pavilion is your **Workhorse**. It runs:

- **Ollama** with the larger models (qwen2.5-coder:7b, mistral:7b, etc.)
- **VirtualBox** sandboxes for risky code execution
- Scraper jobs, file watchers, long-running sidekicks

## Setup

```bash
sudo apt update && sudo apt install -y virtualbox curl
curl -fsSL https://ollama.com/install.sh | sh

# Bind Ollama to all interfaces so the Lubuntu node can reach it over Tailscale
sudo systemctl edit ollama
# Add:
#   [Service]
#   Environment="OLLAMA_HOST=0.0.0.0:11434"
sudo systemctl restart ollama
```

Then join the Tailnet:

```bash
bash infrastructure/tailscale_setup.sh pavilion
```

## Pulling models

```bash
python3 scripts/list_models.py | xargs -n1 ollama pull
```

## Firewall

Ollama should be reachable **only over Tailscale**, never the public LAN:

```bash
sudo ufw default deny incoming
sudo ufw allow in on tailscale0 to any port 11434
sudo ufw enable
```

## VirtualBox sandbox

See `infrastructure/virtualbox_sandbox.md`.
