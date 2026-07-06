#!/bin/sh
# Production entrypoint for Render — single source of truth for startup.
# Start Command in Render Dashboard MUST be: bash start.sh
set -e

APP_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd)
cd "$APP_DIR"

PORT="${PORT:-8000}"

echo "=========================================="
echo " AI Email Intelligence — Render Startup"
echo "=========================================="
echo "cwd:      $(pwd)"
echo "python:   $(python --version 2>&1)"
echo "PORT:     ${PORT}"

export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}"
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"

# --- filesystem checks ---
if [ ! -d "app" ]; then
  echo "ERROR: app/ package directory not found in $(pwd)" >&2
  exit 1
fi

if [ ! -f "app/main.py" ]; then
  echo "ERROR: app/main.py not found" >&2
  exit 1
fi

echo "app/ package: OK"
echo "app/main.py:  OK"

# --- environment presence (values printed by validate_startup.py) ---
echo ""
echo "--- Environment (presence) ---"
if [ -n "${DATABASE_URL:-}" ]; then echo "DATABASE_URL:      set"; else echo "DATABASE_URL:      MISSING"; fi
if [ -n "${CLERK_SECRET_KEY:-}" ]; then echo "CLERK_SECRET_KEY:  set"; else echo "CLERK_SECRET_KEY:  MISSING"; fi
if [ -n "${ANTHROPIC_API_KEY:-}" ]; then echo "ANTHROPIC_API_KEY: set"; else echo "ANTHROPIC_API_KEY: MISSING"; fi
if [ -n "${CORS_ORIGINS:-}" ]; then echo "CORS_ORIGINS:      set"; else echo "CORS_ORIGINS:      MISSING"; fi

# --- Python validation + import (prints full traceback on failure) ---
echo ""
python scripts/validate_startup.py || exit 1

echo ""
echo "==> Launching uvicorn on 0.0.0.0:${PORT}"
exec python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"
