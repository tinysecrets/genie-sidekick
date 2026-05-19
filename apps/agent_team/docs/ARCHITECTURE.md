# Architecture

## One picture

```
                      ┌──────────────────────────┐
                      │   Super Key holder (you) │
                      └────────────┬─────────────┘
                                   │ goal in natural language
                                   ▼
                      ┌──────────────────────────┐
                      │   Genie  (supervisor)    │  ← Master Key, L1
                      └────────────┬─────────────┘
            ┌────────────┬─────────┴─────────┬────────────┐
            ▼            ▼                   ▼            ▼
       ┌─────────┐  ┌─────────┐         ┌─────────┐  ┌─────────┐
       │Reporting│  │ Design  │         │ Coding  │  │   QA    │
       │ Agent   │  │ Agent   │         │ Agent   │  │ Agent   │
       └────┬────┘  └────┬────┘         └────┬────┘  └────┬────┘
            │            │                   │            │
            ▼            ▼                   ▼            ▼
       ┌─────────┐  ┌─────────┐         ┌─────────┐  ┌─────────┐
       │notifier │  │moodboard│         │scaffold │  │  a11y   │
       │ digest  │  │ palette │         │refactor │  │  perf   │
       └─────────┘  └─────────┘         └─────────┘  └─────────┘
                       Genie Sidekicks  (Agent Keys, L3)
```

## Hardware

Two nodes bridged by Tailscale (WireGuard, MagicDNS):

```
┌────────────────────┐                    ┌────────────────────┐
│ Lubuntu            │  ── Tailscale ──   │ HP Pavilion        │
│ "Command Center"   │                    │ "Workhorse"        │
│  - Super Key       │                    │  - Ollama (heavy)  │
│  - Genie           │                    │  - VirtualBox VMs  │
│  - Vault           │                    │  - Sidekicks       │
└────────────────────┘                    └────────────────────┘
```

The Super Key never leaves the Command Center. Only AES-GCM-wrapped derived
keys cross the Tailscale bridge.

## Software

| Concern | Choice | Why |
|---|---|---|
| Key derivation | HKDF-SHA256 | Deterministic, standard, simple |
| Vault sealing | AES-256-GCM | Authenticated, fast, NIST-blessed |
| Passphrase stretching | PBKDF2-HMAC-SHA256 × 480k | OWASP 2023 recommendation |
| Model runtime | Ollama | Free, local, no telemetry |
| Cloud fallback | Groq / HF (free tiers, opt-in) | Optional speed boost |
| Orchestration | Plain Python | No framework lock-in |
| CI | GitHub Actions (`workflow_dispatch` only) | Manual control |

## Why so plain?

Because anything fancier creates a tie — to a vendor, a SDK, a billing plan,
or a runtime that could disappear. The point of this repository is **maximum
optionality for the Super Key holder**. Boring tech is durable tech.
