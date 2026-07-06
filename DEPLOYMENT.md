# Deployment Guide

Production deployment for **AI Native Email Intelligence**: FastAPI backend on Render, Next.js dashboard on Vercel, Neon PostgreSQL for per-user history, Clerk for authentication.

**Live dashboard:** [https://ainativeemail.vercel.app/](https://ainativeemail.vercel.app/)

---

## Architecture

| Service | Host | Purpose |
|---------|------|---------|
| Frontend | Vercel | Next.js dashboard + Clerk auth |
| Backend | Render | FastAPI + LangGraph API |
| Database | Neon | Per-user evaluation/generation history |
| Auth | Clerk | Sign-in, JWT for API |

The frontend never connects to Neon directly. Set `DATABASE_URL` only on **Render**.

---

## Render (Backend)

### Option A — Blueprint

1. Push repo to GitHub.
2. Render → **New → Blueprint** → connect repo.
3. Set secret environment variables (see below).
4. Deploy. Build runs `build.sh` (installs deps + embeds knowledge).

### Option B — Manual Web Service

| Setting | Value |
|---------|--------|
| Environment | Python |
| Root Directory | *(repo root)* |
| Build Command | `chmod +x build.sh && ./build.sh` |
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health Check Path | `/health` |

### Render environment variables

```env
ANTHROPIC_API_KEY=sk-ant-...          # optional if using Gemini only
GEMINI_API_KEY=...
DATABASE_URL=postgresql://...         # Neon connection string — SET HERE
CLERK_SECRET_KEY=sk_...
CLERK_ISSUER=https://xxx.clerk.accounts.dev
CLERK_JWKS_URL=https://xxx.clerk.accounts.dev/.well-known/jwks.json
CORS_ORIGINS=https://ainativeemail.vercel.app
CORS_ORIGIN_REGEX=https://.*\.vercel\.app
LOG_LEVEL=INFO
```

> **Where to put the Neon URL:** Render dashboard → your web service → **Environment** → add `DATABASE_URL` with your Neon pooled connection string. Never commit it to git.

Verify:

```bash
curl https://your-service.onrender.com/health
```

---

## Vercel (Frontend)

1. Import GitHub repo.
2. Set **Root Directory** to `dashboard`.
3. Add environment variables:

```env
NEXT_PUBLIC_API_URL=https://your-service.onrender.com
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_...
CLERK_SECRET_KEY=sk_...
```

4. Deploy.

After deploy, ensure Render `CORS_ORIGINS` includes your exact Vercel URL.

---

## Neon PostgreSQL

1. Create a project at [neon.tech](https://neon.tech).
2. Copy the **pooled** connection string (includes `-pooler` in hostname).
3. Paste into Render as `DATABASE_URL`.
4. Tables are created automatically on backend startup (`init_db()`).

---

## Clerk Authentication

1. Create application at [dashboard.clerk.com](https://dashboard.clerk.com/).
2. Enable Email sign-in.
3. Copy keys to Vercel (`NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`, `CLERK_SECRET_KEY`).
4. Copy to Render: `CLERK_SECRET_KEY`, `CLERK_ISSUER`, `CLERK_JWKS_URL`.
5. Add Vercel URL to Clerk **Allowed origins**.

When `DATABASE_URL` and Clerk are both configured, all `/generate`, `/evaluate`, `/dashboard`, and `/evaluations` requests require a valid Bearer token. Each user sees only their own history.

---

## Railway

1. New project → Deploy from GitHub.
2. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Build: `pip install -r requirements.txt && python scripts/embed_knowledge.py embed`
4. Add the same env vars as Render.
5. Health check: `/health`

---

## Docker (optional)

```dockerfile
FROM python:3.12.8-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python scripts/embed_knowledge.py embed || true
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t ai-email-intelligence .
docker run -p 8000:8000 --env-file .env ai-email-intelligence
```

---

## Local Development

Requires **Python 3.12+** (see `runtime.txt`).

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
cp .env.example .env            # add API keys
python scripts/embed_knowledge.py embed
uvicorn app.main:app --reload --port 8000
```

Dashboard (separate terminal):

```bash
cd dashboard
cp .env.local.example .env.local
npm install
npm run dev
```

Optional local auth/database: set `DATABASE_URL` and Clerk vars in `.env` / `.env.local`. Without them, history uses `results/*.json` under user id `local-dev`.

### Verify environment

```bash
python scripts/check_environment.py
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError: langgraph` | Use Python 3.12+, run `pip install -r requirements.txt` |
| Render exits immediately | Check logs; ensure `uvicorn app.main:app` start command |
| 401 on generate/evaluate | Sign in via Clerk; ensure backend has Clerk JWKS vars |
| CORS errors | Set `CORS_ORIGINS` on Render to your Vercel URL |
| Cold start timeout | Render free tier sleeps; first request may take 30–60s |
| Chroma empty | Run `python scripts/embed_knowledge.py embed` or redeploy (build.sh runs it) |
