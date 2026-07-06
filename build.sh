#!/usr/bin/env bash
set -e

export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}"
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"

pip install --upgrade pip
pip install -r requirements.txt

# Embed knowledge if Chroma is empty (non-fatal on failure)
python scripts/embed_knowledge.py embed || echo "WARN: embed step skipped or failed — will retry at startup"
