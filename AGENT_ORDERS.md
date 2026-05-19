# AGENT ORDERS

## Mission

Fix the repository from the original request without creating more confusion.

The original request was:

> The repo/work was already prepared, but it never got pushed and committed because the coding environment froze.

The job is to recover, organize, commit, push, and report proof.

## Non-Negotiable Rules

1. Do not rebuild the app unless explicitly ordered.
2. Do not replace working code with starter templates.
3. Do not change `main` without preserving a backup branch first.
4. Do not delete user work.
5. Do not ask planning questions when the repo state can be inspected.
6. Preserve first, clean second, commit third, report proof last.
7. Any cleanup must be reversible or documented.

## Required Repo Cleanup

Agents must inspect and clean:

- duplicate branches
- unused starter files
- accidental Vite starter remnants
- stale local-only instructions
- conflicting README instructions
- unnecessary generated files
- broken references to old branch names
- duplicated docs
- unclear run commands

Agents must not delete:

- `frontend/`
- `backend/`
- `apps/`
- `docs/PROJECT_RECOVERY_CONTEXT.md`
- any imported repo content
- any file containing project history or user intent

## Required Monorepo Target

Primary repo:

- `tinysecrets/genie-sidekick`

Related repos to preserve as apps:

- `tinysecrets/real_Genie` -> `apps/real_Genie/`
- `tinysecrets/agent-team` -> `apps/agent_team/`

Preferred merge method:

```bash
git subtree add --prefix=apps/real_Genie https://github.com/tinysecrets/real_Genie.git main
git subtree add --prefix=apps/agent_team https://github.com/tinysecrets/agent-team.git main
```

If `main` is not the correct branch in an imported repo, inspect the branch name before retrying.

## Required AI Backend Structure

Add or verify these backend paths only when implementing the model adapter layer:

```txt
backend/models/adapter.py
backend/models/local_adapter.py
backend/models/remote_adapter.py
backend/models/manager.py
backend/api/generate.py
```

The user does not want a Google Gemini backend. The user wants their own local/remote model adapters with similar capabilities.

## Required App Sections

The app should eventually include:

- Genie main command screen
- Agent Ops / Team assignments
- Projects / repo work
- Voice / live mode preparation
- Settings / runtime status

Do not confuse this with a casino dashboard. The Game Hub context matters, but the dashboard is the personal command center and agent-management interface.

## Required Proof Report

When finished, report only:

```txt
Repository:
Branch:
Commit SHA:
PR Link:
Files changed:
How to run:
Real blockers:
```

No proof means not finished.

## Local PC Cleanup Boundary

Agents do not have permission to blindly delete files from the user's PC.

If asked to clean the local machine, produce a cleanup plan that moves old folders into a dated backup folder first. Do not permanently delete anything without explicit final approval.

Suggested safe local cleanup method:

```txt
Create ~/Genie_Backups/<date>/
Move old duplicate project folders there.
Keep only one active ~/genie-sidekick folder.
Do not delete backups until the user confirms the app runs.
```
