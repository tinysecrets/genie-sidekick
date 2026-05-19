# Project Recovery Context

## Original User Request

The original problem was not to redesign the app or start a new frontend. The original problem was:

> I never got it pushed and committed.

The correct task was to recover, verify, commit, and push the existing completed work, not redirect into a fresh rebuild.

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
