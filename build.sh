#!/usr/bin/env bash
set -e

export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}"
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"

pip install --upgrade pip
pip install -r requirements.txt

# Embed knowledge if Chroma is empty (no typer/rich — production deps only)
python - <<'PY' || echo "WARN: embed step skipped or failed — will retry at startup"
from app.retriever.vector_store import get_vector_store

vs = get_vector_store()
if vs.document_count == 0:
    count = vs.ingest_policies()
    print(f"Ingested {count} documents")
else:
    print(f"Chroma already indexed: {vs.document_count} documents")
PY
