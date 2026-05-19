# Project Recovery Context

## Original User Request

The original problem was not to redesign the app or start a new frontend. The original problem was:

> I never got it pushed and committed.

The correct task was to recover, verify, commit, and push the existing completed work, not redirect into a fresh rebuild.

## Added From The First Pasted AI Plan

The first pasted AI plan already contained the actual items that needed to be carried forward. These must be treated as part of the project requirements, not optional brainstorming.

### Monorepo Decision

Use `tinysecrets/genie-sidekick` as the primary repository because it already had the dashboard/app foundation.

Import the other repositories into it as preserved subfolders:

- `tinysecrets/real_Genie` -> `apps/real_Genie/`
- `tinysecrets/agent-team` -> `apps/agent_team/`

The goal is one unified monorepo with one dashboard, one source of truth, and one place for the Genie + agent-team experience.

### Required Repository Layout

Target structure:

```txt
/
├── backend/
├── frontend/
├── discord_bot/
├── apps/
│   ├── real_Genie/
│   └── agent_team/
├── docs/
├── .github/workflows/
└── README.md
```

The dashboard remains in `frontend/`.

Imported apps remain under `apps/` so no original code or history is silently erased.

### Merge Method To Use

Default method:

```txt
git subtree
```

Reason:

- simple
- fast
- preserves imported repo history
- works without extra tooling
- keeps each app isolated in its own subfolder

Required subtree imports:

```bash
git subtree add --prefix=apps/real_Genie https://github.com/tinysecrets/real_Genie.git main
git subtree add --prefix=apps/agent_team https://github.com/tinysecrets/agent-team.git main
```

If a repo does not use `main`, check the real branch name before retrying.

### Do Not Delete Old Repos Immediately

After import, old repos should be archived only after testing confirms everything works.

Do not delete the old repos blindly.

### Privacy / Secrets Check

After merging:

- check repo visibility
- check for committed secrets
- rotate any exposed keys
- review `.env`, tokens, deployment files, and old config files

### README Update Required

The main README must explain:

- what Genie is
- how the monorepo is structured
- how to run frontend
- how to run backend
- where `real_Genie` lives
- where `agent_team` lives
- how agents should report proof

## Model / AI Backend Requirements From First Plan

The user corrected the AI plan: do **not** add Google Gemini as the backend.

The requirement is:

- Genie should support the user's own AI/model backends with comparable abilities.
- Use a flexible adapter layer.
- Local-first is the default.
- Remote/free/optional providers can be plugged in later.

### Backend Adapter Files To Add

Required backend structure:

```txt
backend/models/adapter.py
backend/models/local_adapter.py
backend/models/remote_adapter.py
backend/models/manager.py
backend/api/generate.py
```

Purpose:

- `adapter.py` defines the base model interface.
- `local_adapter.py` connects to local model servers.
- `remote_adapter.py` connects to user-controlled remote endpoints.
- `manager.py` registers and selects model backends.
- `generate.py` exposes a backend route for Genie responses.

### Frontend Model Selection

A frontend model selector or settings panel should allow choosing available local/remote model backends when backend support is ready.

Example location:

```txt
frontend/src/components/ModelSelector.jsx
```

## Genie / Agent Team Product Requirements

### Genie

Genie is the single visible assistant/operator.

Genie should:

- be the user's personal assistant
- coordinate the agent team
- report status to the user
- remain the main interface
- know the Game Hub context
- keep the same core identity across the app

### Agent Team

Agent team members work under Genie.

The app should include a separate Agent Ops / Team section for:

- assignments
- repo tasks
- build status
- worker roles
- proof reports

The user should not have to manually micromanage every worker unless they choose to.

### Proof-Based Execution

Agent team output must always include:

- repository
- branch
- commit SHA
- PR link if created
- files changed
- run command
- blocker if any

No proof means the task is not done.

## Repositories Involved

Primary repository:

- `tinysecrets/genie-sidekick`

Related repositories that were part of the monorepo plan:

- `tinysecrets/real_Genie`
- `tinysecrets/agent-team`

## Intended System

The user's intended system is:

- User is the owner / final authority.
- Genie is the personal AI assistant and coordinator.
- Agent team performs repository work under Genie.
- Agent team should carry repositories from start to finish.
- Game Hub / wah-lah.com context matters.
- The app should feel like an app, not a command-line-only project.
- Local-first operation matters.
- Online/free deployment can come after the local working state is verified.

## Core Failure To Avoid

Do not turn a recovery task into a rebuild task.

If the user says the repo was already finished but not pushed/committed, the first action must be Git recovery:

1. Inspect repo state.
2. Preserve current work.
3. Commit current work.
4. Push branch.
5. Return proof.

No extra UI rebuild, no new Vite starter path, no broad architecture changes unless explicitly requested.

## Proof Required

Every agent or assistant working on this repo must return:

- Repository
- Branch
- Commit SHA
- Pull request link, if created
- Files changed
- How to run
- Real blocker, if any

No proof means the task is not complete.

## Current Known GitHub State

A command-center UI commit was created:

- Branch: `genie-command-center-ui`
- Commit: `9521656752c89c9fedf4793ff58b33d48d2f7ba2`
- Backup branch: `backup/genie-command-center-ui-locked`

Main was later moved to the same commit, and the old main was backed up as:

- `backup/main-before-command-center`

A recovery context commit was also created:

- Commit: `886baae686f506c980818b607b227de5562a7f78`

Do not force-push or overwrite branches unless the user explicitly gives that exact instruction.

## Operating Rule Going Forward

When asked to fix the repo:

- Do not debate.
- Do not rebuild unless requested.
- Do not change main without explicit permission.
- Preserve first.
- Commit second.
- Push third.
- Report proof only.
