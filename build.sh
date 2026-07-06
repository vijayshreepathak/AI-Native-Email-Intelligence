#!/usr/bin/env bash
set -o errexit

export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}"
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"

pip install --upgrade pip
pip install -r requirements-prod.txt
python scripts/embed_knowledge.py embed
