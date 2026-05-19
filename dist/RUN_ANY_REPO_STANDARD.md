# RUN ANY REPO STANDARD

Goal: the user can provide any repository, ZIP, or project folder and assign Genie or a worker to make it run.

The user should not need to know the project language, stack, scripts, or setup order.

## Worker Responsibility

A worker must:

1. Locate the project root.
2. Inspect files before acting.
3. Detect the stack.
4. Detect available scripts.
5. Install dependencies when appropriate.
6. Start the app using the detected run method.
7. Report the exact local URL or blocker.
8. Preserve source code.
9. Never replace the project with a starter template unless explicitly ordered.

## Detection Targets

Workers must recognize at least:

- JavaScript projects
- React projects
- Vite projects
- Next projects
- Node server projects
- Python projects
- FastAPI projects
- Flask projects
- Django projects
- Static HTML projects
- Docker projects
- Full stack projects with frontend and backend folders

## Proof Required

Every run attempt must end with:

Repository:
Detected stack:
Install result:
Run result:
Local URL:
Files changed:
Commit SHA if committed:
Real blockers:

## Rule

No guessing. Inspect first. Preserve first. Run second. Report proof last.
