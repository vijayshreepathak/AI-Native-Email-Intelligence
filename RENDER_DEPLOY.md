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

```env
DATABASE_URL=postgresql://...
CLERK_SECRET_KEY=sk_...
CLERK_ISSUER=https://xxx.clerk.accounts.dev
CLERK_JWKS_URL=https://xxx.clerk.accounts.dev/.well-known/jwks.json
ANTHROPIC_API_KEY=sk-ant-...
CORS_ORIGINS=https://ainativeemail.vercel.app
```

## Git Commands

```bash
git add -A
git commit -m "fix: production Python package structure and Render startup"
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
GET https://YOUR-SERVICE.onrender.com/health  → {"status":"healthy"}
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

See [PACKAGE.md](./PACKAGE.md) for import graph and startup flow.
