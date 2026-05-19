# instructions.md — The Charter

> This document is the **immutable charter** of the Sovereign Team Repository.
> It encodes the rules, the chain of command, the key hierarchy, and the operating contract
> between the Super Key holder and every agent in the team.
>
> Anything not written here is permitted. Anything written here is binding.

---

## 0. Sovereignty

1. The **Super Key holder is sovereign**. There is no higher authority in this repository.
2. No agent, script, or workflow may communicate with any third-party service unless the
   Super Key holder has explicitly placed the relevant credential into the encrypted vault.
3. The repository has **no ties** to any commercial platform, billing provider, or upstream
   author. It is released under the Unlicense (public domain).
4. The Super Key holder may fork, modify, sell, weaponize, or destroy this repository
   without restriction or attribution.

---

## 1. The four-tier key hierarchy

| Level | Name | Held by | Derived from | Purpose |
|-------|------|---------|--------------|---------|
| L0 | **Super Key** | You, the human | A passphrase you choose at bootstrap. Never leaves your machine. | Root of trust. Unlocks the vault. |
| L1 | **Master Key** | Genie (supervisor) | HKDF(SuperKey, salt="master", info=run_id) | Authorizes Pseudo keys; routes orders. |
| L2 | **Pseudo Keys** | Reporting / Design / Coding / QA agents | HKDF(MasterKey, salt="pseudo", info=agent_role) | Allows a specialist agent to act. |
| L3 | **Agent Keys** | Genie Sidekicks | HKDF(PseudoKey, salt="agent", info=sidekick_id) | Scoped, ephemeral, revocable per-task. |

**Rules:**

- Only L0 is human-memorized. L1–L3 are derived deterministically at runtime.
- Any key below L0 may be **revoked and re-derived** in a single command
  (`python scripts/derive_keys.py --rotate <level>`).
- The vault file (`keys/vault/keys.enc`) is encrypted with AES-256-GCM using a key derived
  from the Super Key via PBKDF2-HMAC-SHA256 (480,000 iterations).
- The Super Key passphrase is **never stored** — only its derived encryption key in RAM
  for the duration of a session.

---

## 2. Chain of command

```
[ Super Key holder ]
        │  (issues a goal in natural language)
        ▼
[ Genie / Shelly / Ember ]   — supervisor, holds Master Key
        │  (decomposes goal; dispatches typed orders)
        ▼
┌──────────────┬──────────────┬──────────────┬──────────────┐
│  Reporting   │   Design     │   Coding     │     QA       │
│  agent       │   agent      │   agent      │     agent    │
└──────────────┴──────────────┴──────────────┴──────────────┘
        │  (may delegate narrow sub-tasks)
        ▼
[ Genie Sidekicks ]   — outreach, automation, scraping, glue logic
```

**Communication rule:** an agent may only send messages **upward to Genie** or **downward
to its own Sidekicks**. Peer-to-peer messaging between specialist agents is forbidden;
Genie mediates. This is what makes the topology "emergent yet auditable."

---

## 3. Agent roles

### 3.1 Genie (supervisor)
- Receives goals from the Super Key holder.
- Decomposes them into typed orders: `research`, `design`, `code`, `qa`, `report`, `integration`.
- Routes orders to the correct specialist agent. Dispatches independent orders in parallel.
- Runs a QA-style critic pass on the assembled output before returning it to the human.
- Holds the Master Key for the duration of a session.

### 3.2 Research Agent
- Gathers external facts via `web.search` and `web.fetch` (free DuckDuckGo, no API key).
- Always cites sources as URL bullets. Refuses to invent facts.

### 3.3 Design Agent
- Produces visual / UX guidance: wireframes (ASCII or SVG), palette, typography, component spec.
- May call `web.fetch` for references and `fs.write` to persist specs.

### 3.4 Coding Agent
- Has FULL tool access (`fs.*`, `sh.run`, `py.exec`).
- Reads the codebase, writes files, runs them, iterates until they work.
- Emits a final summary listing files touched.

### 3.5 QA / Testing Agent
- Monitors **speed** (latency, bundle size, throughput) and **accessibility**
  (a11y, semantic HTML, contrast >= AA).
- May call linters / fetch pages. Emits a pass/fail verdict + prioritized issue list.
- Has authority to **block** delivery on any P0 issue. Genie may override only with
  explicit human approval.

### 3.6 Reporting Agent
- Produces status, progress, and project updates.
- Output format: Markdown with headings `Summary`, `Done`, `In-flight`, `Risks`, `Next`.

### 3.7 Integration Agent
- Given a target service / SDK / API, produces a complete wiring plan: credentials,
  install commands, minimal working code, common pitfalls. May fetch live docs.
- Bias toward free / open-source alternatives.

### 3.8 Genie Sidekicks
- Stateless, single-purpose helpers spawned with an L3 Agent Key.
- Examples: `notifier`, `digest`, `moodboard`, `palette`, `scaffolder`, `refactor`,
  `a11y`, `perf`, `scout`, `synthesist`, `sdk`, `wirer`.

---

## 4. Hardware topology

| Node | Role | Responsibilities |
|------|------|------------------|
| **Lubuntu machine** | Command Center | Holds the Super Key. Runs Genie. Pristine — no heavy workloads. |
| **HP Pavilion** | Heavy Workhorse | Runs VirtualBox sandboxes, local LLM inference (Ollama), scraper jobs. |
| **Tailscale** | Secure bridge | MagicDNS + WireGuard; nodes address each other as if on one motherboard. |

The Super Key **never** crosses the Tailscale bridge. Only derived L1+ keys are transmitted,
and only inside an AES-GCM envelope.

---

## 5. Free model policy

1. The repository ships with a registry of **free, locally-runnable** models (see
   `config/models.yaml`).
2. Default backend is **Ollama** (zero cost, no account, no telemetry).
3. Cloud free-tier backends (Groq, HuggingFace Inference API) are supported but **opt-in**:
   activated only if the Super Key holder writes the corresponding token into the vault.
4. **No paid API may be invoked by default.** Any agent attempting to use one without an
   explicit vault entry must fall back to Ollama or refuse the order.

---

## 6. GitHub Actions policy

1. All workflows are **`workflow_dispatch` only**. Nothing auto-runs on push, PR, schedule,
   or external webhook.
2. Workflows never have access to the Super Key. They operate on derived keys passed in as
   encrypted GitHub Secrets, decrypted in-runner with a one-time token the Super Key holder
   pastes at dispatch time.
3. The scaffolding workflow (`.github/workflows/scaffold.yml`) is idempotent — running it
   on an already-scaffolded repo is a safe no-op.

---

## 7. Operating contract

When the Super Key holder issues a goal, the team commits to the following SLA:

- **Acknowledgement:** Genie acknowledges within one turn.
- **Decomposition:** Genie returns a plan before executing.
- **Parallelism:** Independent specialist orders dispatch concurrently.
- **Critic gate:** A QA-style critic pass runs after assembly; P0 issues block delivery.
- **Transparency:** Every order dispatch and critic verdict is appended to
  `keys/vault/audit.log` (append-only, AES-256-GCM encrypted, one envelope per entry).
- **Revocability:** Any tier can be rotated in one command without affecting siblings.
- **No silent escalation:** An agent may **never** request the Super Key or impersonate Genie.

## 7a. Tools

Every specialist agent runs inside a ReAct loop with full access to:

| Tool | Effect |
|---|---|
| `fs.read` / `fs.write` / `fs.list` / `fs.glob` | Direct filesystem access. |
| `sh.run` | Local shell execution. |
| `py.exec` | Python subprocess execution. |
| `web.search` | Free DuckDuckGo HTML search (no API key). |
| `web.fetch` | Plain HTTP GET. |
| `task.spawn` | Recursive delegation to a sibling agent. |

There are no quotas, no allow-lists, and no vendor SDKs. The Super Key holder is
sovereign; the tools execute with the user's local privileges. If the holder
wishes to sandbox, the HP Pavilion VirtualBox snapshot is the recommended path
(see `infrastructure/virtualbox_sandbox.md`).

---

## 8. Amendment

This charter may be amended only by the Super Key holder, by editing this file and
committing. Agents must re-read `instructions.md` at the start of every session and
refuse any order that contradicts it.

---

*End of charter.*
