# Render Production Deployment Checklist

## Render Dashboard Settings

| Setting | Value |
|---------|--------|
| **Root Directory** | *(blank — repo root)* |
| **Build Command** | `chmod +x start.sh && pip install -r requirements.txt` |
| **Pre-Deploy Command** | *(leave blank)* |
| **Start Command** | `bash start.sh` |
| **Health Check Path** | `/health` |

> **Critical:** Start Command must NOT be `pip install ...`. That causes "Application exited early".

## Required Environment Variables (Render)

```env
DATABASE_URL=postgresql://...
CLERK_SECRET_KEY=sk_...
CLERK_ISSUER=https://xxx.clerk.accounts.dev
CLERK_JWKS_URL=https://xxx.clerk.accounts.dev/.well-known/jwks.json
ANTHROPIC_API_KEY=sk-ant-...
CORS_ORIGINS=https://ainativeemail.vercel.app
GEMINI_API_KEY=...                    # optional fallback
```

## Git Commands

```bash
git add start.sh render.yaml Procfile app/main.py app/startup_validation.py scripts/validate_startup.py
git commit -m "fix: robust Render startup with validation and tracebacks"
git push origin main
```

## Verify After Deploy

```bash
curl https://YOUR-SERVICE.onrender.com/
curl https://YOUR-SERVICE.onrender.com/health
```

## Expected Successful Logs

```
==========================================
 AI Email Intelligence — Render Startup
==========================================
cwd:      /opt/render/project/src
python:   Python 3.12.x
PORT:     10000
app/ package: OK
app/main.py:  OK
--- Environment (presence) ---
DATABASE_URL:      set
CLERK_SECRET_KEY:  set
ANTHROPIC_API_KEY: set
CORS_ORIGINS:      set
Environment validation: OK
Application import: OK (AI Email Intelligence Platform)
==> Launching uvicorn on 0.0.0.0:10000
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:10000
```

## Production Entrypoint

**Single entrypoint:** `bash start.sh` → `uvicorn app.main:app`

Do **not** use `python cli.py serve` or `pip install` as Start Command on Render.
