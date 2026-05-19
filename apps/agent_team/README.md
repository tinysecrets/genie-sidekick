# Sovereign Team Repository

> **Self-contained, zero-restriction, zero-cost AI agent team.**
> One command. One key. Full tool access. No ties to any platform, payment, or token.

The Super Key holder gets a team **at least as capable as any commercial agent stack**:
six specialised agents, real tools (filesystem, shell, web, code execution), recursive
delegation, parallel dispatch, a QA critic gate, and an encrypted audit log — all free,
all local, all yours.

---

## One-line bootstrap

```bash
bash bootstrap.sh
```

After bootstrap:

```bash
python agents/genie/genie.py "your first goal"
```

That's it. Genie plans, dispatches the specialists in parallel, runs a critic pass,
and hands you the assembled output.

---

## What's in the team

| Agent | Tools it really uses | Key tier |
|---|---|---|
| **Genie** (supervisor) | plans, dispatches, runs critic | Master, L1 |
| **Research** | `web.search`, `web.fetch` (free DuckDuckGo) | Pseudo, L2 |
| **Design** | `web.fetch` for references, `fs.write` for specs | Pseudo, L2 |
| **Coding** | `fs.read/write`, `sh.run`, `py.exec` — full ReAct loop | Pseudo, L2 |
| **QA** | inspects files, runs linters, gates on P0 | Pseudo, L2 |
| **Reporting** | summarises results, writes status docs | Pseudo, L2 |
| **Integration** | reads live SDK docs, drafts wiring code | Pseudo, L2 |
| **Genie Sidekicks** | ephemeral, narrow helpers per role | Agent, L3 |

Each specialist runs inside an iterative **ReAct loop** that can call tools, observe
results, and iterate until the order is satisfied. Agents can also recursively spawn
sub-tasks on other roles via the `task.spawn` tool.

---

## Tools — fully unrestricted

| Tool | Effect |
|---|---|
| `fs.read` / `fs.write` / `fs.list` / `fs.glob` | Direct filesystem access. |
| `sh.run` | Local shell execution. |
| `py.exec` | Python subprocess execution. |
| `web.search` | Free DuckDuckGo HTML search, no API key. |
| `web.fetch` | Plain HTTP GET, text-extracted. |
| `task.spawn` | Recursive delegation to any sibling agent. |

No quotas. No allow-lists. No vendor SDKs. The Super Key holder is sovereign.

---

## Chain of command

```
You (Super Key, L0)
        │
        ▼
   Genie  (Master Key, L1)        ← plans, parallel-dispatches, critics
        │
        ├──► Research        (L2)
        ├──► Design          (L2)
        ├──► Coding          (L2)
        ├──► QA              (L2)
        ├──► Reporting       (L2)
        └──► Integration     (L2)
                  │
                  ▼
             Sidekicks (L3, ephemeral)
```

Even if any L1–L3 key leaks, the **Super Key never leaves your head**. One command
rotates the compromised tier and re-derives the rest.

---

## Free models

Default backend is **Ollama** (local, free, no telemetry). The registry ships with:

| Role | Model |
|---|---|
| Coding / Integration | `qwen2.5-coder:7b` |
| Genie / Research | `qwen2.5:7b-instruct` |
| Design | `llama3.2:3b` |
| QA | `mistral:7b` |
| Reporting | `phi3.5:3.8b` |
| Sidekicks | `llama3.2:1b` |

Cloud free tiers (Groq, HuggingFace) are opt-in — they activate only if you write the
corresponding token into the vault.

---

## Repository layout

```
.
├── bootstrap.sh                 # one-command setup
├── instructions.md              # the charter
├── README.md
├── LICENSE                      # Unlicense — public domain
├── Makefile
├── requirements.txt
├── .github/workflows/           # manual-dispatch only
├── agents/
│   ├── genie/                   # supervisor
│   ├── research/                # web research
│   ├── design/                  # visual specs
│   ├── coding/                  # full tool-using coder
│   ├── qa/                      # speed + a11y auditor
│   ├── reporting/               # status / digests
│   ├── integration/             # SDK / API wiring
│   ├── sidekicks/               # generic L3 helper
│   ├── tools/                   # fs / sh / web / py / task tools
│   ├── _llm.py                  # backend-agnostic LLM client
│   └── _loop.py                 # ReAct tool loop
├── keys/                        # key_manager + encrypted vault + audit log
├── scripts/                     # init / derive / encrypt / decrypt / audit
├── config/                      # models.yaml, agents.yaml
├── infrastructure/              # Tailscale, Lubuntu, HP Pavilion, VirtualBox
├── docs/                        # ARCHITECTURE, CHAIN_OF_COMMAND, KEY_HIERARCHY, TOOLS, QUICKSTART
└── tests/                       # pytest
```

---

## Daily commands

```bash
# Talk to the team
make genie GOAL="build me a static landing page for an indie game"

# Plan only (no dispatch, no LLM calls past Genie)
make plan GOAL="..."

# Inspect the encrypted audit log
make audit

# Rotate keys
make rotate-agent      # L3 only
make rotate-master     # L1 + L2 + L3

# Run the test suite
make test
```

---

## License

Released into the **public domain** under the [Unlicense](LICENSE). Fork it, sell it,
weaponise it, ignore the author. No attribution. No strings. No restrictions.

---

## Sovereignty guarantee

The repository has **no phone-home**, **no telemetry**, **no required external service**,
**no upstream owner**. Read `instructions.md` (the charter) — every promise made there is
enforced in code.
