#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

echo "============================================================"
echo " GENIE AGENT TEAM STARTUP"
echo "============================================================"
echo "Repo: $(basename "$ROOT_DIR")"
echo "Path: $ROOT_DIR"
echo ""

# 1. Preserve current state first.
echo "[1/7] Checking git state..."
git status --short || true
CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
echo "Current branch: $CURRENT_BRANCH"
echo ""

# 2. Create required folders without deleting anything.
echo "[2/7] Ensuring required folders exist..."
mkdir -p apps docs agents/tasks agents/prompts agents/system backend/models backend/api

# 3. Verify source-of-truth files.
echo "[3/7] Checking source-of-truth files..."
if [ ! -f AGENT_ORDERS.md ]; then
  cat > AGENT_ORDERS.md <<'ORDERS'
# AGENT ORDERS

Mission: recover, preserve, commit, push, and run the Genie repo without rebuilding from scratch.

Rules:
- Preserve first.
- Do not delete user work.
- Do not replace working code with starter templates.
- Do not change main without a backup.
- Report proof: Repository, Branch, Commit SHA, PR Link, Files changed, How to run, Real blockers.
ORDERS
fi

if [ ! -f docs/PROJECT_RECOVERY_CONTEXT.md ]; then
  cat > docs/PROJECT_RECOVERY_CONTEXT.md <<'CONTEXT'
# Project Recovery Context

Original task: the work was already supposed to be finished, but the environment froze before add/commit/push. The job is recovery, not rebuilding.

Required repos:
- tinysecrets/genie-sidekick
- tinysecrets/real_Genie -> apps/real_Genie
- tinysecrets/agent-team -> apps/agent_team

Genie is the main assistant/coordinator. The agent team works under Genie and reports proof.
CONTEXT
fi

# 4. Add related repos only if missing and only if git subtree is available.
echo "[4/7] Checking imported app folders..."
if [ ! -d apps/real_Genie ]; then
  echo "apps/real_Genie missing. Importing if possible..."
  git subtree add --prefix=apps/real_Genie https://github.com/tinysecrets/real_Genie.git main || echo "Could not import real_Genie automatically. Agent must inspect branch/access."
else
  echo "apps/real_Genie exists. Keeping it."
fi

if [ ! -d apps/agent_team ]; then
  echo "apps/agent_team missing. Importing if possible..."
  git subtree add --prefix=apps/agent_team https://github.com/tinysecrets/agent-team.git main || echo "Could not import agent-team automatically. Agent must inspect branch/access."
else
  echo "apps/agent_team exists. Keeping it."
fi

# 5. Install frontend dependencies if frontend exists.
echo "[5/7] Preparing frontend..."
if [ -d frontend ] && [ -f frontend/package.json ]; then
  cd frontend
  npm install
  cd "$ROOT_DIR"
else
  echo "No frontend/package.json found. Skipping frontend install."
fi

# 6. Install backend dependencies if backend exists.
echo "[6/7] Preparing backend..."
if [ -d backend ] && [ -f backend/requirements.txt ]; then
  if command -v python3 >/dev/null 2>&1; then
    python3 -m pip install -r backend/requirements.txt || echo "Backend pip install needs manual review."
  else
    echo "python3 not found. Skipping backend install."
  fi
else
  echo "No backend/requirements.txt found. Skipping backend install."
fi

# 7. Commit current recovery state if there are changes.
echo "[7/7] Saving recovery state..."
cd "$ROOT_DIR"
if [ -n "$(git status --short)" ]; then
  git add .
  git commit -m "Run Genie agent team startup recovery" || true
  git push origin HEAD || echo "Push failed. Agent must authenticate or inspect remote permissions."
else
  echo "No changes to commit."
fi

echo ""
echo "============================================================"
echo " STARTUP COMPLETE"
echo "============================================================"
echo "Proof command:"
echo "  git log --oneline -1"
echo ""
echo "Run frontend:"
echo "  cd frontend && npm run dev"
echo ""
echo "Run backend:"
echo "  cd backend && uvicorn server:app --reload --port 8000"
echo ""
echo "Open the local URL Vite prints, usually http://localhost:5173"
