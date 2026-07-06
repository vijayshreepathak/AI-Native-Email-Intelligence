#!/usr/bin/env bash
# Render start script — MUST be the Start Command (not pip install).
set -euo pipefail

cd "$(dirname "$0")"

export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}"
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
export PORT="${PORT:-8000}"

echo "==> Starting AI Email Intelligence on port ${PORT}"

# Verify app imports before binding (surfaces errors in Render logs)
python -c "from app.main import app; print('Import OK:', app.title)"

exec python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"
