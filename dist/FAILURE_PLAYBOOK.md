# FAILURE PLAYBOOK

This file covers common things that can go wrong when running or recovering any repo.

Agents must check this file before asking the user to troubleshoot manually.

## Core Rule

Do not guess.
Inspect the folder.
Identify the exact failure.
Fix the smallest thing possible.
Preserve the user's work.
Report proof.

## Wrong Folder

Symptom:

- file not found
- frontend not found
- backend not found
- package.json not found
- requirements.txt not found

Action:

- find the repo root
- list folders
- confirm where frontend and backend live
- do not create a new project just because the current folder is wrong

## Local Changes Block Branch Switch

Symptom:

- local changes would be overwritten
- checkout aborted
- merge aborted

Action:

- preserve local work first
- commit or stash before switching branches
- never hard reset unless the user explicitly says to discard local changes

## Old Browser Page Still Showing

Symptom:

- app code changed but browser still shows old page
- Vite starter still appears
- wrong localhost tab is open

Action:

- use the exact URL printed by the running dev server
- close old localhost tabs
- hard refresh the browser
- check whether another dev server is using an older port

## Port Already In Use

Symptom:

- port already in use
- Vite starts on another port
- backend cannot bind port

Action:

- use the new printed port if available
- stop old terminal process if needed
- do not assume 5173 is always correct

## Missing Command

Symptom:

- git not found
- node not found
- npm not found
- python not found
- pip not found
- uvicorn not found
- docker not found

Action:

- identify the missing tool
- install only that tool
- retry the original command
- do not rebuild the repo

## Missing Script

Symptom:

- npm missing script dev
- npm missing script start

Action:

- inspect package.json
- identify available scripts
- run the correct script
- if scripts are missing, repair package.json only when appropriate
- do not create a new starter app unless explicitly ordered

## Dependency Install Failure

Symptom:

- npm install fails
- pip install fails
- dependency version error
- unsupported engine warning

Action:

- read the exact package error
- check Node and Python versions
- upgrade only the required runtime if needed
- retry install
- do not delete source code

## Node Version Problem

Symptom:

- unsupported engine
- package requires newer Node

Action:

- check node version
- upgrade Node if required
- rerun npm install

## Backend Environment Missing

Symptom:

- login fails
- JWT secret missing
- admin email missing
- database connection error
- Mongo connection error

Action:

- inspect backend README or environment examples
- create or update .env only if the user permits secrets locally
- do not commit real secrets
- use placeholder examples in repo docs

## Git Push Failure

Symptom:

- authentication failed
- permission denied
- rejected non-fast-forward
- remote branch changed

Action:

- confirm remote URL
- confirm branch
- pull or fetch first
- never force push unless ordered
- report the exact blocker

## Subtree Import Failure

Symptom:

- repository not found
- branch main not found
- prefix already exists
- unrelated history issue

Action:

- verify repo URL
- verify branch name
- if prefix exists, do not import again
- preserve existing apps folder

## ZIP Intake Failure

Symptom:

- downloaded zip extracts nested folder
- repo root hidden inside another folder
- no package files in top directory

Action:

- search extracted folders for package.json, requirements.txt, index.html, Dockerfile, or README
- set the project root to the folder containing build files

## Full Stack Confusion

Symptom:

- frontend runs but backend does not
- backend runs but frontend cannot connect
- API path errors

Action:

- run frontend and backend separately
- check CORS config
- check frontend API base URL
- check backend health endpoint

## Cleanup Risk

Symptom:

- duplicate project folders
- old clones
- broken local copies
- too many downloads

Action:

- move old folders into a dated backup folder
- keep one active repo folder
- do not permanently delete until the user confirms the app runs

## Final Agent Report

Every failure response must include:

Repository:
Current folder:
Detected stack:
Exact error:
Smallest safe fix:
Files changed:
Commit SHA if committed:
Local URL if running:
Real blockers:
