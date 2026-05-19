# UNIVERSAL LOCATION STANDARD

This file defines where Genie tools, repos, backups, downloads, and worker runs should live on the user's computer.

The goal is simple:

The user should not have to remember where a project folder is.
Genie and workers should know where to look every time.

## Primary Universal Home

Use this as the main Genie home on Linux or Ubuntu:

```txt
~/GenieOS/
```

Expanded path example:

```txt
/home/<user>/GenieOS/
```

## Required Folder Layout

```txt
~/GenieOS/
├── active/
├── incoming/
├── repos/
├── zips/
├── backups/
├── logs/
├── tools/
├── dist/
├── agents/
├── reports/
└── archive/
```

## Folder Purpose

`active/`

The one project currently being worked on.

`incoming/`

Drop random repos, extracted folders, or files here for Genie/agents to inspect.

`repos/`

All cloned GitHub repos go here.

`zips/`

Downloaded ZIP files go here before extraction.

`backups/`

Old project folders are moved here before cleanup. Do not delete first.

`logs/`

Run logs, install logs, error logs, and proof reports go here.

`tools/`

Reusable tools, scripts, installers, and runner helpers go here.

`dist/`

The permanent Genie startup kit copied from this repo.

`agents/`

Agent tasks, prompts, system orders, and assignment files.

`reports/`

Proof reports from workers.

`archive/`

Old completed or inactive projects.

## Windows Equivalent

Use this as the main Genie home on Windows:

```txt
C:\Users\<user>\GenieOS\
```

Same folder layout applies.

## Repo Rule

The active project should be available at:

```txt
~/GenieOS/active/genie-sidekick/
```

or linked from there.

If the actual repo lives somewhere else, agents should create a reference note in:

```txt
~/GenieOS/reports/ACTIVE_REPO_LOCATION.txt
```

## Universal Agent Rule

When assigned a repo, worker agents must search in this order:

1. `~/GenieOS/active/`
2. `~/GenieOS/incoming/`
3. `~/GenieOS/repos/`
4. `~/Downloads/`
5. current working directory

## ZIP Intake Rule

Downloaded ZIP files should be moved into:

```txt
~/GenieOS/zips/
```

Extracted projects should go into:

```txt
~/GenieOS/incoming/
```

After inspection, the selected working project should be moved or copied to:

```txt
~/GenieOS/active/
```

## Cleanup Rule

Never delete first.

Move old duplicates to:

```txt
~/GenieOS/backups/<date>/
```

Keep only one active project in:

```txt
~/GenieOS/active/
```

## Dist Kit Rule

The `dist/` folder from this repo should be copied to:

```txt
~/GenieOS/dist/
```

That makes the kit available even when the current terminal is in the wrong repo.

## Global Command Goal

Eventually the system should support a single command:

```txt
genie-run <repo-or-zip-path>
```

That command should:

- find or create `~/GenieOS/`
- move ZIPs into `zips/`
- extract into `incoming/`
- detect stack
- install dependencies
- run the project
- print URL
- save proof report

## Current Human Standard

Until the global command exists, every agent must still obey the universal location standard and use `~/GenieOS/` as the main operating home.
