#!/usr/bin/env bash
set -e

echo "=================================="
echo "AI Email Intelligence Startup"
echo "=================================="

echo "cwd=$(pwd)"
echo "python=$(python --version)"

export PYTHONPATH="$(pwd)"
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}"
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"

echo "PYTHONPATH=$PYTHONPATH"

python -c "
import sys
print(sys.path)
import app
print('app import successful')
"

exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port ${PORT:-8000}
