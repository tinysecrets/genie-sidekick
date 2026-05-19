# Quickstart

```bash
git clone <your-fork>  emergent-team
cd emergent-team
bash bootstrap.sh
python agents/genie/genie.py "your first goal"
```

That's the whole thing.

## What `bootstrap.sh` does

1. Installs Python deps from `requirements.txt`.
2. Asks for your **Super Key passphrase** (once). Stores nothing.
3. Derives Master / Pseudo / Agent keys via HKDF.
4. Encrypts the resulting bundle with AES-256-GCM into `keys/vault/keys.enc`.
5. (Optional) Pulls free local models via Ollama.

## Daily use

- Talk to Genie:           `python agents/genie/genie.py "..."`
- Plan only (no dispatch): `python agents/genie/genie.py --dry-run "..."`
- Rotate Pseudo keys:      `python scripts/derive_keys.py --rotate pseudo`
- Inspect the vault:       `python scripts/decrypt_vault.py`  (prompts for Super Key)

## Where to customise

You almost never need to. If you do:

| File | Why you'd edit it |
|---|---|
| `config/agents.yaml` | Tweak agent system prompts, swap a model key. |
| `config/models.yaml` | Pin different Ollama tags or enable a cloud free tier. |
| `instructions.md`    | Amend the charter (you are sovereign — go ahead). |

Everything else can stay untouched.
