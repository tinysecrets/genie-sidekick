# Key Hierarchy

Four tiers. One human-held secret. Everything else derived.

```
L0  Super Key (passphrase, in your head)
        │  PBKDF2-HMAC-SHA256, 480 000 iterations, 16-byte random salt
        ▼
       vault-encryption key  (AES-256-GCM seals keys/vault/keys.enc)
        │  HKDF-SHA256, info="master:<run_id>"
        ▼
L1  Master Key                ← held by Genie
        │  HKDF-SHA256, info=f"pseudo:{role}"
        ▼
L2  Pseudo Keys (per role)    ← held by specialist agents
        │  HKDF-SHA256, info=f"agent:{role}:{sidekick}"
        ▼
L3  Agent Keys (per sidekick) ← ephemeral, scoped to one task
```

## Derivation properties

- **Deterministic.** The same Super Key always derives the same lower-tier
  keys for the same `run_id`. Lose the vault file? Re-derive in one command.
- **One-way.** Knowing an L2 or L3 key tells you nothing about the L0 or L1
  key. HKDF gives forward secrecy across tiers.
- **Domain-separated.** Each level uses a distinct `info` string, so the same
  parent material never produces the same child output across roles.

## Rotation

| Command | Effect |
|---|---|
| `python scripts/derive_keys.py --rotate agent`  | New L3 keys; L1/L2 unchanged. |
| `python scripts/derive_keys.py --rotate pseudo` | New L2/L3; L1 unchanged. |
| `python scripts/derive_keys.py --rotate master` | New L1/L2/L3. |
| `python scripts/derive_keys.py --rotate all`    | Full new run; same L0. |

Rotation **never** asks for a new Super Key passphrase. Your L0 is permanent
until you choose to retire it.

## Compromise scenarios

| Leaked | Recovery |
|---|---|
| An L3 Agent Key | `--rotate agent`. Done. |
| A specialist's L2 Pseudo Key | `--rotate pseudo`. All sidekicks regenerated. |
| Genie's L1 Master Key | `--rotate master`. New run_id. Same L0 passphrase. |
| L0 Super Key (passphrase) | Re-init with new passphrase; old vault is dead. |

## What is never written to disk

- The Super Key passphrase.
- The vault-encryption key (held in RAM only for the session).
- Any plaintext L1/L2/L3 key (only the AES-GCM ciphertext is persisted).
