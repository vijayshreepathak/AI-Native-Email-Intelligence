# Render Deployment Report — Dependency Optimization

## Checklist

| Item | Status |
|------|--------|
| requirements optimized | ✓ |
| PyTorch download removed | ✓ |
| SSL issue eliminated | ✓ |
| Render compatible | ✓ |
| FastAPI startup (no torch) | ✓ |
| No unnecessary packages in prod | ✓ |

## Production vs Optional Dependencies

| File | Purpose | Installed on Render |
|------|---------|---------------------|
| `requirements.txt` | API runtime (FastAPI, LangGraph, ChromaDB, DB, Clerk) | **Yes** |
| `requirements-dev.txt` | CLI, scripts, pytest | No |
| `requirements-evaluation.txt` | torch, bert-score, sentence-transformers, rapidfuzz | No |

## Removed from Production

| Package | Reason |
|---------|--------|
| `--extra-index-url download.pytorch.org` | Caused SSLV3_ALERT_HANDSHAKE_FAILURE on Render |
| `torch==2.6.0+cpu` | ~700MB; only needed for evaluation embeddings/BERTScore |
| `sentence-transformers` | Evaluation-only; ChromaDB uses built-in ONNX embeddings |
| `bert-score` | Evaluation-only; lazy-loaded with token-overlap fallback |
| `rapidfuzz` | Evaluation-only; optional BERTScore fallback |
| `typer`, `rich` | Dev/CLI scripts only |
| `pytest`, `pytest-asyncio` | Tests only |

## Kept in Production

| Package | Reason |
|---------|--------|
| `chromadb` | RAG vector store (ONNX DefaultEmbeddingFunction) |
| `numpy` | Lightweight cosine/hash embeddings for evaluation fallback |
| `langgraph`, `langchain-*`, `anthropic` | Core pipeline |
| `sqlalchemy`, `psycopg2-binary`, `PyJWT` | Neon + Clerk |

## Graceful Degradation (no code path changes)

- **Generate / Predict** — never import torch or bert-score
- **Evaluate** — BERTScore lazy-loads; falls back to token overlap if `bert-score` absent
- **Embedding similarity** — lazy-loads SentenceTransformer; falls back to hash embeddings if absent
- **ChromaDB retrieval** — uses Chroma built-in ONNX model (no torch)

## Build Command (Render)

```bash
pip install -r requirements.txt
```

No contact with `download.pytorch.org`.

## Verification

```bash
pip install -r requirements.txt
python scripts/check_runtime.py
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Full evaluation locally:

```bash
pip install -r requirements-evaluation.txt
```

## Estimated Impact

| Metric | Before | After | Reduction |
|--------|--------|-------|-----------|
| Download size | ~2.0–2.5 GB | ~400–600 MB | **~70–80%** |
| Install time (Render) | ~8–15 min | ~2–4 min | **~60–75%** |
| PyTorch.org fetches | 1+ (SSL failure) | **0** | **100%** |

*Estimates based on torch+transformers+bert-score removal; ChromaDB + LangChain remain the largest prod deps.*
