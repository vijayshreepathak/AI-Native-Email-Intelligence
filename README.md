# AI Native Email Intelligence Platform

[![GitHub](https://img.shields.io/badge/GitHub-vijayshreepathak%2FAI--Native--Email--Intelligence-181717?logo=github)](https://github.com/vijayshreepathak/AI-Native-Email-Intelligence)

Production-quality AI email reply platform inspired by **Hiver AI Copilot**. It ingests customer support emails, runs a multi-agent LangGraph pipeline, retrieves company knowledge, generates validated replies, and scores quality with BERTScore, embeddings, and an LLM judge — all exposed through a FastAPI backend and a polished Next.js AI Operations dashboard.

**Live app:** [https://ainativeemail.vercel.app/](https://ainativeemail.vercel.app/)  
**Repository:** [github.com/vijayshreepathak/AI-Native-Email-Intelligence](https://github.com/vijayshreepathak/AI-Native-Email-Intelligence)

---

## Architecture

```mermaid
flowchart TB
    subgraph UI["Next.js Dashboard — ainativeemail.vercel.app"]
        PG[Copilot Playground]
        PM[Premium Metrics]
        PV[Pipeline Visualization]
        KG[Knowledge Graph]
        AN[Analytics]
    end

    subgraph API["FastAPI — localhost:8000"]
        EP["/generate · /evaluate · /predict · /dashboard · /health"]
    end

    subgraph Pipeline["LangGraph Pipeline"]
        direction TB
        I[Intent] --> P[Priority]
        P --> S[Sentiment]
        S --> C[Customer Type]
        C --> K[Knowledge Retrieval]
        K --> PB[Prompt Builder]
        PB --> G[LLM Generator]
        G --> V[Validator]
        V --> E[Embedding Eval]
        E --> B[BERTScore]
        B --> J[LLM Judge]
        J --> R[Final Report]
    end

    subgraph Data["Knowledge & Storage"]
        KGJ[(Knowledge Graph JSON)]
        CH[(ChromaDB Vectors)]
        RES[(results/*.json)]
    end

    subgraph LLM["LLM Providers"]
        CL[Claude Sonnet — primary]
        GM[Gemini 2.5 Flash — fallback]
    end

    PG --> EP
    EP --> Pipeline
    K --> KGJ
    K --> CH
    G --> CL
    CL -.->|on failure| GM
    Pipeline --> RES
    RES --> AN
    EP --> PM
```

### Tech Stack

| Layer | Technology | Role |
|-------|------------|------|
| Orchestration | **LangGraph** | Stateful multi-agent workflow |
| LLM (primary) | **Claude Sonnet 4.6** | Classify, generate, validate, judge |
| LLM (fallback) | **Gemini 2.5 Flash** | Automatic fallback when Claude fails |
| Vector DB | **ChromaDB** | Semantic policy/FAQ retrieval |
| Embeddings | **ChromaDB ONNX** (prod) · **SentenceTransformers** (eval profile) | RAG retrieval; full local embeddings via `requirements-evaluation.txt` |
| API | **FastAPI** | Async REST endpoints |
| Dashboard | **Next.js 16 + Framer Motion** | AI Ops console UI |
| Evaluation | **BERTScore + Embeddings + LLM Judge** | Multi-metric quality scoring |

> **Important:** Production deployments use a **lightweight dependency profile** (`requirements.txt`) without Torch, Sentence Transformers, or BERTScore. See [Dependency Profiles](#dependency-profiles) below — evaluation metrics still run in production via **LLM judge + lightweight fallbacks**, but research-grade embedding/BERTScore scoring requires `requirements-evaluation.txt` locally.

---

## Dependency Profiles

This project intentionally uses **three dependency profiles**. Many users clone expecting every AI evaluation feature (BERTScore, Sentence Transformers, Torch, embedding similarity) to work immediately after `pip install -r requirements.txt`. **That is by design not the case in production** — heavy ML packages are excluded to keep the backend lightweight and deployable on Render.

### 1. `requirements.txt` — Production runtime

**Purpose:** Serve live API traffic with minimal footprint.

**Used by:**

- [Render](https://render.com) (backend)
- Railway
- Docker
- All production deployments

**Includes:**

- FastAPI + Uvicorn
- LangGraph + LangChain
- Anthropic (Claude)
- ChromaDB (built-in ONNX embeddings for RAG — no Torch required)
- SQLAlchemy + psycopg2 (Neon PostgreSQL)
- PyJWT (Clerk authentication)
- NumPy (lightweight fallbacks)

**Production intentionally excludes:**

- Torch
- Sentence Transformers
- BERTScore
- RapidFuzz

This reduces:

- Deployment download size (~70–80% smaller)
- Cold start time on Render free tier
- Memory usage (512MB-friendly)
- Build failures (SSL / PyTorch wheel issues on `download.pytorch.org`)

**Production behavior without heavy ML deps:**

| Endpoint | Works? | Notes |
|----------|--------|-------|
| `POST /generate` | ✅ | Full LangGraph generation + RAG |
| `POST /predict` | ✅ | Classification only |
| `POST /evaluate` | ✅ | LLM judge always runs; BERTScore/embedding similarity use **lightweight fallbacks** |
| `GET /dashboard` | ✅ | Per-user metrics via Neon |

---

### 2. `requirements-dev.txt` — Contributors & local tooling

**Purpose:** Everything in production **plus** developer workflow tools.

**Includes** (via `-r requirements.txt`):

- **pytest** + pytest-asyncio — test suite
- **typer** + **rich** — CLI (`cli.py`) and scripts

**Install:**

```bash
pip install -r requirements-dev.txt
```

Use this profile for day-to-day local backend development, running tests, and CLI commands.

---

### 3. `requirements-evaluation.txt` — Research-grade evaluation

**Purpose:** Install optional heavy ML packages for **full** offline evaluation fidelity.

**Includes** (via `-r requirements.txt`):

- **Torch** (PyPI only — never `download.pytorch.org`)
- **Sentence Transformers** (`all-MiniLM-L6-v2`)
- **BERTScore**
- **RapidFuzz**

**Enables:**

- Semantic similarity (embedding cosine)
- BERTScore F1 / precision / recall
- Offline benchmarking on `dataset/test.json`
- Research experiments and model comparison
- Reproducible evaluation papers / ablations

These packages are **optional** and **not required** for production inference or the live dashboard.

**Install:**

```bash
pip install -r requirements-evaluation.txt
```

> **Tip:** `requirements-evaluation.txt` already includes `requirements.txt`. You do not need to install both separately.

---

### Feature availability by profile

| Feature | Production (`requirements.txt`) | Local Evaluation (`requirements-evaluation.txt`) |
|---------|--------------------------------|--------------------------------------------------|
| FastAPI API | ✅ | ✅ |
| LangGraph | ✅ | ✅ |
| Claude | ✅ | ✅ |
| Gemini Fallback | ✅ | ✅ |
| ChromaDB RAG | ✅ | ✅ |
| PostgreSQL (Neon) | ✅ | ✅ |
| Clerk Authentication | ✅ | ✅ |
| Dashboard | ✅ | ✅ |
| Analytics | ✅ | ✅ |
| Semantic Similarity | ❌ (fallback) | ✅ |
| Sentence Transformers | ❌ | ✅ |
| BERTScore | ❌ (fallback) | ✅ |
| Torch Evaluation | ❌ | ✅ |
| Embedding Similarity | ❌ (fallback) | ✅ |

**Fallback behavior in production:** When Torch/BERTScore/Sentence Transformers are absent, the evaluation pipeline uses token-overlap and hash-based embedding fallbacks so `/evaluate` never crashes — scores differ from full local evaluation.

---

## Features

### Backend Pipeline
- **12-node LangGraph workflow** with per-node latency, tokens, and error tracking
- **30 support intents** — billing, refunds, API, security, sync errors, permissions, etc.
- **Knowledge graph traversal** (9 nodes) + ChromaDB vector search (top-3 docs)
- **Structured JSON generation** with citations and confidence scores
- **Validation agent** — hallucination, tone, grammar, completeness, policy compliance
- **LLM judge** — 8 criteria with weighted overall score
- **Gemini fallback** — if Claude key expires or credits run out, pipeline auto-switches to Gemini

### Next.js AI Operations Dashboard
- **Premium metric cards** — AI Quality, latency breakdown, token usage, grounded responses %
- **Copilot Playground** — Generate or Evaluate modes with 8 sample tickets
- **Live pipeline visualization** — animated LangGraph nodes with auto-scroll
- **Interactive knowledge graph** — click nodes for policies, FAQs, templates
- **Retrieval panel** — similarity, matched concepts, index status
- **AI Quality Checklist** — pass/fail gates with 6/7 style scoring
- **LLM Judge panel** — enhanced radar chart + strengths/weaknesses/suggestions
- **Score explainability** — weighted breakdown of why overall = X%
- **Execution timeline** — per-node latency bars
- **Analytics section** — quality trends, grounding, latency, intent distributions
- **Dark/light mode**, keyboard shortcuts, responsive layout

---

## Screenshots

### Platform features
Overview of all capabilities — LangGraph pipeline, RAG, validation, LLM judge, knowledge graph, and REST API.

![Platform features](./Screenshots/H0%20features.jpeg)

### Dashboard — generated reply
Copilot Playground with sample tickets. After clicking **Generate Reply**, the right panel shows intent, priority, sentiment, and the AI-drafted response.

![Dashboard with generated reply](./Screenshots/H1%20Dashboard%20with%20genereted%20reply%20after%20clicking%20genertee%20reply%20.jpeg)

### Live pipeline visualization
LangGraph nodes animate in sequence while the pipeline runs — each step shows latency, tokens, and status. Scrolling stays inside the panel.

![Running pipeline visualization](./Screenshots/h3%20running%20pipeline%20visualisation%20.jpeg)

![Pipeline step detail](./Screenshots/h3.1%20running%20visualtion%20.jpeg)

### Full evaluation
**Evaluate** mode compares the generated reply against a reference response with BERTScore, embedding similarity, and LLM judge scores.

![Evaluated response](./Screenshots/h4%20evaluated%20response.jpeg)

![Evaluation metrics and per-node timing](./Screenshots/h5%20after%20evaluated%20respinse%20u%20can%20check%20the%20time%20taken%20by%20each%20response%20.jpeg)

### Analytics
Historical quality trends, grounding scores, latency charts, and intent distributions — scroll down from the playground or use the **Analytics** button.

![Analytics dashboard](./Screenshots/h2%20Analytics.jpeg)

---

## Quick Start

### Use the live app

1. Open **[https://ainativeemail.vercel.app/](https://ainativeemail.vercel.app/)**
2. **Sign in** with Clerk (top-right) — your history is private to your account
3. Pick a sample ticket → **Generate Reply** or switch to **Evaluate**
4. Click **Sync** if metrics show dashes (Render free tier may need a moment to wake)

See [DEPLOYMENT.md](./DEPLOYMENT.md) for full production setup (Render + Vercel + Neon + Clerk).

---

### Local development

Requires **Python 3.12+** (`runtime.txt` pins 3.12.8 for Render).

Choose the dependency profile that matches your goal:

#### Production-only install (matches Render)

Minimal footprint — same packages deployed to production:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

#### Contributor install (recommended for most local work)

Production deps + CLI + pytest:

```bash
pip install -r requirements-dev.txt
```

#### Full evaluation install (research / benchmarking)

All production deps + Torch + BERTScore + Sentence Transformers:

```bash
pip install -r requirements-evaluation.txt
python scripts/validate_startup.py   # verify imports
pytest tests/ -v                     # run evaluation tests
```

Quick reference:

```bash
pip install -r requirements.txt              # production / Render parity
pip install -r requirements-dev.txt          # + CLI, pytest
pip install -r requirements-evaluation.txt   # + torch, BERTScore, full metrics
```

#### 1. Clone & install

```bash
git clone https://github.com/vijayshreepathak/AI-Native-Email-Intelligence.git
cd AI-Native-Email-Intelligence

python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements-dev.txt   # includes production deps + CLI + pytest
```

#### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:

```env
ANTHROPIC_API_KEY=your_claude_key          # primary LLM
ANTHROPIC_MODEL=claude-sonnet-4-6
GEMINI_API_KEY=your_gemini_key             # fallback when Claude fails
GEMINI_MODEL=gemini-2.5-flash
```

> **Tip:** If Claude credits expire, the pipeline automatically falls back to Gemini. You only need `GEMINI_API_KEY` set.

#### 3. Index knowledge base

```bash
python scripts/embed_knowledge.py embed
```

#### 4. Start backend (Terminal 1)

```bash
uvicorn app.main:app --reload --port 8000
# API → http://127.0.0.1:8000
# Docs → http://127.0.0.1:8000/docs
```

#### 5. Start dashboard (Terminal 2)

```bash
cd dashboard
npm run dev
# UI → http://localhost:3000
```

#### 6. Try it

1. Open **http://localhost:3000**
2. Click a **Sample Ticket** (e.g. OAuth / Gmail Sync Error)
3. Click **Generate Reply** (~60s) or switch to **Evaluate** for full scoring
4. Explore tabs: **Reply · Pipeline · Graph · Quality · Retrieval · Judge · Insights**
5. Scroll down for **Analytics**

---

## Pipeline Steps

| # | Node | Description |
|---|------|-------------|
| 1 | Intent Agent | Classifies into 30 support intents |
| 2 | Priority Agent | critical / high / medium / low |
| 3 | Sentiment Agent | Customer sentiment analysis |
| 4 | Customer Agent | enterprise, business, pro, etc. |
| 5 | Knowledge Agent | Graph traversal + ChromaDB top-3 retrieval |
| 6 | Prompt Builder | Assembles context-rich prompt |
| 7 | Generator Agent | LLM produces structured JSON reply |
| 8 | Validator Agent | Hallucination, tone, grammar, policy checks |
| 9 | Embedding Evaluation | Cosine similarity vs expected reply |
| 10 | BERTScore | Semantic F1 overlap |
| 11 | LLM Judge | 8-criteria quality assessment |
| 12 | Final Report | Weighted score + feedback |

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Status, model, Chroma index, fallback availability |
| `POST` | `/predict` | Classification only (intent, priority, sentiment) |
| `POST` | `/generate` | Full generation pipeline |
| `POST` | `/evaluate` | Generation + BERTScore + judge + metrics |
| `GET` | `/dashboard` | Aggregated metrics for analytics UI |

### Examples

```bash
# Health
curl http://127.0.0.1:8000/health

# Generate
curl -X POST http://127.0.0.1:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"subject":"Gmail sync broken","email":"Our shared inbox stopped syncing. 12 agents affected.","customer_name":"Maria"}'

# Evaluate
curl -X POST http://127.0.0.1:8000/evaluate \
  -H "Content-Type: application/json" \
  -d '{"subject":"Refund request","email":"I want a pro-rated refund.","expected_response":"Your refund is approved within 5-10 business days."}'
```

---

## LLM Fallback

```
Claude (primary)  →  success  →  use Claude response
                 ↘  failure (expired key, no credits, rate limit)
                    Gemini (fallback)  →  use Gemini response
```

Configured in `app/agents/base.py`. No pipeline changes needed — fallback is transparent to all agents.

---

## Knowledge Graph

9 interconnected nodes in `knowledge/knowledge_graph.json`:

**Billing · Refund · Shipping · Technical · Security · Account · API · Subscription · Permissions**

Each node has policies, FAQs, response templates, escalation rules, and related-node links. Intent-to-node mapping drives targeted retrieval during inference.

---

## Evaluation

> For **full** BERTScore and embedding similarity scores, install [`requirements-evaluation.txt`](#3-requirements-evaluationtxt--research-grade-evaluation). Production uses LLM judge + lightweight fallbacks — see [Dependency Profiles](#dependency-profiles).

| Metric | Weight | Description |
|--------|--------|-------------|
| LLM Judge | 35% | 8 criteria vs expected reply |
| Embedding Similarity | 35% | Sentence embedding cosine similarity |
| BERTScore | 30% | Contextual F1 score |

**Judge criteria:** Correctness, Completeness, Empathy, Professionalism, Actionability, Safety, Hallucination, Policy Adherence

**Validation checks:** No hallucination, action items, professional tone, grammar, completeness, policy compliance

---

## Dataset Generation

```bash
python scripts/generate_dataset.py generate
```

Generates 300 synthetic Hiver-style emails (30 intents × 10). Features incremental checkpoint saves, retry with backoff, deduplication, and train/val/test split.

---

## Project Structure

```
ai-email-intelligence/
├── app/                     # FastAPI + LangGraph backend
│   ├── agents/              # Pipeline agent nodes + LLM client (Claude/Gemini)
│   ├── retriever/           # ChromaDB + knowledge graph
│   ├── evaluation/          # BERTScore, embeddings, judge
│   ├── services/            # Dashboard aggregation
│   └── main.py              # API entry point
├── dashboard/               # Next.js AI Operations UI
│   └── src/
│       ├── app/             # Pages + API routes
│       └── components/      # Pipeline viz, metrics, analytics, etc.
├── knowledge/               # Graph, policies, FAQs, templates, ChromaDB
├── dataset/                 # train / validation / test JSON
├── scripts/                 # embed_knowledge, generate_dataset, test_llm_fallback
├── results/                 # generated.json, evaluation.json, dashboard.json
├── Screenshots/             # UI screenshots for README
├── cli.py                   # Typer CLI (local dev — production uses start.sh)
├── requirements.txt         # Production runtime (Render)
├── requirements-dev.txt     # + pytest, typer, rich
├── requirements-evaluation.txt  # + torch, BERTScore, sentence-transformers
├── start.sh                 # Production entrypoint (Render)
├── render.yaml              # Render Blueprint
├── PACKAGE.md               # Package structure & import graph
├── RENDER_DEPLOY.md         # Render deployment checklist
└── README.md
```

---

## CLI

```bash
python cli.py serve --port 8000
python cli.py generate-reply "Subject" "Email body" --name "Customer"
python cli.py evaluate-dataset --split test --limit 5
python scripts/test_llm_fallback.py    # verify Claude → Gemini fallback
```

---

## Tests

Requires `requirements-dev.txt` (includes pytest):

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Evaluation-specific tests (`tests/test_evaluation.py`) additionally require:

```bash
pip install -r requirements-evaluation.txt
pytest tests/test_evaluation.py -v
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | — | Primary Claude API key |
| `ANTHROPIC_MODEL` | `claude-sonnet-4-6` | Claude model |
| `GEMINI_API_KEY` | — | Fallback Gemini API key |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence transformer |
| `RETRIEVAL_TOP_K` | `3` | Documents retrieved per query |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `CORS_ORIGINS` | `http://localhost:3000,https://ainativeemail.vercel.app` | Comma-separated allowed frontend origins |
| `CORS_ORIGIN_REGEX` | `https://.*\.vercel\.app` | Regex for Vercel preview/production URLs |
| `DATABASE_URL` | — | Neon PostgreSQL connection string (**Render only**) |
| `CLERK_SECRET_KEY` | — | Clerk secret key for JWT verification |
| `CLERK_ISSUER` | — | Clerk issuer URL, e.g. `https://xxx.clerk.accounts.dev` |
| `CLERK_JWKS_URL` | — | Clerk JWKS URL for token verification |

---

## Deployment

See **[DEPLOYMENT.md](./DEPLOYMENT.md)** for Render, Vercel, Neon, Clerk, Railway, Docker, and local instructions.

### Backend → [Render](https://render.com)

The repo includes a [Render Blueprint](https://render.com/docs/blueprint-spec) (`render.yaml`).

1. Push the repo to [GitHub](https://github.com/vijayshreepathak/AI-Native-Email-Intelligence)
2. In Render: **New → Blueprint** → connect the repo
3. Set secret env vars in the Render dashboard:
   - `GEMINI_API_KEY` (and/or `ANTHROPIC_API_KEY`)
   - `DATABASE_URL` → **paste your Neon connection string here**
   - `CLERK_SECRET_KEY`, `CLERK_ISSUER`, `CLERK_JWKS_URL`
   - `CORS_ORIGINS` → `https://ainativeemail.vercel.app`
4. Deploy — build runs `pip install -r requirements.txt` (no Torch/BERTScore)
5. Copy the Render URL for Vercel `NEXT_PUBLIC_API_URL`

**Render settings (manual deploy):**

| Setting | Value |
|---------|--------|
| Root Directory | *(repo root)* |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `bash start.sh` |
| Health Check | `/health` |
| Python Version | 3.12.8 (`runtime.txt`) |

> Generate/Evaluate requests take **30–120 seconds**. Free Render tiers may timeout or sleep — first request after idle can take 30–60s.

---

### Frontend → [Vercel](https://vercel.com)

**Production URL:** [https://ainativeemail.vercel.app/](https://ainativeemail.vercel.app/)

1. Import the GitHub repo in Vercel
2. Set **Root Directory** to `dashboard`
3. Add environment variables:

```env
NEXT_PUBLIC_API_URL=https://your-render-service.onrender.com
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_...
CLERK_SECRET_KEY=sk_...
```

4. Deploy — Vercel auto-detects Next.js via `dashboard/vercel.json`

**After deploy:** update Render `CORS_ORIGINS` with your exact Vercel production URL.

---

### Verify production

```bash
curl https://your-api.onrender.com/health
# Open https://ainativeemail.vercel.app → Sign in → Sync → Generate Reply
```

```bash
python scripts/check_runtime.py
```

---

## License

MIT
