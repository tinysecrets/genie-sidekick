# Runbook

This is the quick rejoin point for the local agent team.

## Start Fresh

```bash
SUPER_KEY='choose-a-long-local-passphrase' bash bootstrap.sh --ci --no-models
```

Use `--no-models` when Ollama is not installed. Without a reachable LLM backend,
the CLI now stops with a setup message instead of a Python traceback.

## Provide a Model Backend

Local default:

```bash
ollama serve
ollama pull qwen2.5:1.5b
```

Optional free cloud token:

```bash
SUPER_KEY='choose-a-long-local-passphrase' python3 scripts/set_token.py GEMINI_API_KEY
```

## Run

```bash
SUPER_KEY='choose-a-long-local-passphrase' make plan GOAL="verify the team"
SUPER_KEY='choose-a-long-local-passphrase' make genie GOAL="build the requested thing"
```

Genie local interface:

```bash
ollama serve
SUPER_KEY='choose-a-long-local-passphrase' make ui
```

Open `http://127.0.0.1:8765`. Genie greets the user, asks what they want
to build, captures their personal opinion, and streams the team run.

Clickable launcher:

```bash
chmod +x scripts/start_genie_app.sh
SUPER_KEY='choose-a-long-local-passphrase' scripts/start_genie_app.sh
```

On a Linux desktop, `Genie.desktop` can be placed on the desktop or app menu
and clicked to open Genie.

Lubuntu installer:

```bash
chmod +x scripts/install_lubuntu_launcher.sh
scripts/install_lubuntu_launcher.sh
```

This creates a Genie app-menu entry and, when `~/Desktop` exists, a desktop
icon with the correct path for that notebook.

Send Genie to a Lubuntu notebook over Tailscale/SSH:

```bash
chmod +x scripts/deploy_lubuntu.sh
scripts/deploy_lubuntu.sh user@lubuntu-tailnet-name ~/Genie
```

The deploy script copies the project, installs the app launcher, and leaves the
encrypted vault behind so the notebook can be bootstrapped with its own Super Key.

Verified local healthcheck command:

```bash
SUPER_KEY='choose-a-long-local-passphrase' \
GENIE_DETERMINISTIC_CRITIC=1 \
AGENT_MAX_STEPS=1 \
OLLAMA_NUM_PREDICT=80 \
python3 agents/genie/genie.py --serial \
  "write a short status report confirming the local agent team can run end to end"
```

The last verified run transcript is saved at `docs/LAST_RUN.md`.

## Verify

```bash
make test
make lint
```
