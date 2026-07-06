# Render Production Deployment

## Render Dashboard Settings

| Setting | Value |
|---------|--------|
| **Root Directory** | *(blank — repo root)* |
| **Build Command** | `pip install -r requirements.txt` |
| **Pre-Deploy Command** | *(blank)* |
| **Start Command** | `bash start.sh` |
| **Health Check Path** | `/health` |

## Required Environment Variables

Paste these in **Render → your service → Environment**:

```env
# ── LLM Gateway (at least one API key) ─────────────────────────────────────
LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.5-flash-lite
FALLBACK_PROVIDER=groq
FALLBACK_MODEL=llama-3.3-70b-versatile
SECONDARY_PROVIDER=openai
SECONDARY_MODEL=gpt-4.1-mini

GEMINI_API_KEY=AIza...              # https://aistudio.google.com/apikey
GROQ_API_KEY=gsk_...                # optional
OPENAI_API_KEY=sk-...               # optional
ANTHROPIC_API_KEY=sk-ant-...        # optional

TEMPERATURE=0
MAX_TOKENS=4096
REQUEST_TIMEOUT=60
MAX_RETRIES=5

# ── Database (Neon) ─────────────────────────────────────────────────────────
DATABASE_URL=postgresql://user:pass@host/neondb?sslmode=require

# ── Clerk JWT verification ──────────────────────────────────────────────────
CLERK_SECRET_KEY=sk_live_...
CLERK_ISSUER=https://xxx.clerk.accounts.dev
CLERK_JWKS_URL=https://xxx.clerk.accounts.dev/.well-known/jwks.json

# ── CORS (your Vercel URL) ──────────────────────────────────────────────────
CORS_ORIGINS=https://ainativeemail.vercel.app
CORS_ORIGIN_REGEX=https://.*\.vercel\.app
```

## Vercel Environment Variables

Set in **Vercel → project → Settings → Environment Variables** (root directory: `dashboard`):

```env
NEXT_PUBLIC_API_URL=https://YOUR-SERVICE.onrender.com
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_...
CLERK_SECRET_KEY=sk_live_...
```

See `dashboard/.env.local.example` for a commented local template.

## Git Commands

```bash
git add -A
git commit -m "feat: provider-agnostic LLM gateway and env setup docs"
git push origin main
```

## Verify Locally

```bash
export PYTHONPATH=$(pwd)   # Linux/Mac
# $env:PYTHONPATH = (Get-Location).Path   # Windows PowerShell

pip install -r requirements.txt
python -c "import app; print(app.__version__)"
python scripts/validate_startup.py
bash start.sh
curl http://127.0.0.1:8000/health
```

## Expected Render Logs (success)

```
==================================
AI Email Intelligence Startup
==================================
cwd=/opt/render/project/src
python=Python 3.12.x
PYTHONPATH=/opt/render/project/src
app import successful
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:10000
```

## Health URLs

```
GET https://YOUR-SERVICE.onrender.com/        → {"status":"ok"}
GET https://YOUR-SERVICE.onrender.com/health  → {"status":"healthy", "model": "...", ...}
```

## Production Checklist

- [x] `app/` is a valid package with `__init__.py` in all subpackages
- [x] Relative imports within `app/` subpackages
- [x] `scripts/` bootstrap `sys.path` before `from app...`
- [x] Single entrypoint: `bash start.sh` → `uvicorn app.main:app`
- [x] `PYTHONPATH=$(pwd)` set in start.sh
- [x] Env validation runs in lifespan (after imports)
- [x] `/` and `/health` work without DB/LLM/Chroma
- [x] `render.yaml`: `pip install -r requirements.txt` + `bash start.sh`
- [x] LLM calls go through `app/llm/gateway.py` (no direct provider calls)

See [PACKAGE.md](./PACKAGE.md) for import graph and startup flow.
