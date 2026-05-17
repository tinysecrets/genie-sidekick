# Chain of Command

## Protocol

1. **Goal** — the Super Key holder issues a single natural-language goal.
2. **Acknowledgement** — Genie acknowledges in one sentence.
3. **Plan** — Genie emits a numbered plan whose lines are typed orders:
   - `[report] ...`  → Reporting Agent
   - `[design] ...`  → Design Agent
   - `[code]   ...`  → Coding Agent
   - `[qa]     ...`  → QA Agent
4. **Dispatch** — each order is routed to exactly one specialist agent.
5. **Sidekicks** — a specialist may spawn an L3 sidekick for narrow sub-tasks.
6. **Assembly** — Genie collects results and returns one document to the human.

## Forbidden moves

| Action | Reason |
|---|---|
| Specialist-to-specialist messaging | Topology must remain auditable. |
| Agent requests Super Key | Sovereignty boundary. |
| Genie impersonates the human | Sovereignty boundary. |
| Sidekick persists state across runs | Sidekicks are ephemeral by design. |
| Any agent calls a paid API without a vault entry | "Free by default" invariant. |

## Override

Only the Super Key holder may override the QA Agent's `BLOCK` verdict on a
P0 issue. Genie cannot override on its own.

## Audit

Every order dispatch is appended (encrypted, AES-GCM) to `keys/vault/audit.log`.
The Super Key holder is the only entity that can read it
(`python scripts/decrypt_vault.py`).
