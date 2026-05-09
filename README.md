# LectureLens

> AI-powered lecture companion that turns YouTube lectures into personalized study systems.

![LectureLens](https://img.shields.io/badge/built%20with-Next.js%2014-black?logo=nextdotjs)
![FastAPI](https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi)
![pgvector](https://img.shields.io/badge/search-pgvector-336791?logo=postgresql)
![LangGraph](https://img.shields.io/badge/AI-LangGraph-orange)

## What it does

Paste any YouTube lecture URL → LectureLens runs a multi-agent pipeline to produce:

| Mode | What you get |
|------|-------------|
| **Learn** | Timestamped summary, key concepts, chapter outline |
| **Break It Down** | Deep-dive concept cards with audio explanations |
| **Revise** | Flashcards (SM-2 spaced repetition), quiz mode, oral exam simulator |
| **Search** | Semantic search over the transcript with confidence scoring |
| **Mind Map** | Interactive concept graph with mastery overlays |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind CSS, Framer Motion |
| Backend | FastAPI + Python 3.12 |
| Database | PostgreSQL 16 + pgvector (1536-dim embeddings) |
| Cache / Queue | Redis 7 + Celery |
| AI Orchestration | LangGraph (8-node DAG) |
| LLMs | Anthropic Claude (primary) + OpenAI GPT-4o-mini (optional fallback) |
| Embeddings | Anthropic Claude embeddings or OpenAI text-embedding-3-small |
| TTS | ElevenLabs (optional) |

---

## Quick Start (Docker Compose)

```bash
# 1. Clone and enter the project
git clone https://github.com/your-org/lecturelens.git
cd lecturelens

# 2. Configure environment
cp .env.example .env
# Edit .env — fill in ANTHROPIC_API_KEY; OPENAI_API_KEY is optional

# 3. Start all services
docker compose up -d

# 4. Run database migrations
docker compose exec backend alembic upgrade head

# 5. Open the app
open http://localhost:3000
```

---

## Local Development (without Docker)

### Prerequisites

- Node.js ≥ 20
- Python ≥ 3.12
- PostgreSQL 16 with pgvector extension
- Redis 7

### Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp ../.env.example .env
# Edit .env with your credentials

# Run migrations
alembic upgrade head

# Start the dev server
uvicorn app.main:app --reload --port 8000
```

### Celery Worker (for background processing)

```bash
cd backend
celery -A app.jobs.celery_app worker --loglevel=info --concurrency=2
```

### Frontend

```bash
cd frontend

# Install dependencies
npm ci

# Configure API endpoint
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Start dev server
npm run dev
```

Visit **http://localhost:3000**

---

## Project Structure

```
lecturelens/
├── frontend/
│   ├── app/                     # Next.js App Router pages & layouts
│   │   ├── dashboard/           # Main app (subject + lecture management)
│   │   ├── lecture/[lectureId]/ # Five-mode lecture dashboard
│   │   ├── processing/[jobId]/  # Real-time pipeline progress
│   │   └── page.tsx             # Landing page
│   ├── components/
│   │   ├── content/             # Learn & Break It Down modes
│   │   ├── revise/              # Flashcards, quiz, oral exam, revision plan
│   │   ├── mindmap/             # Interactive concept graph canvas
│   │   ├── search/              # Semantic search results
│   │   ├── tracking/            # Mastery tracker
│   │   └── ui/                  # Design system primitives
│   └── lib/
│       ├── api/                 # Typed API client modules
│       ├── hooks/               # TanStack Query hooks
│       ├── types/               # TypeScript interfaces
│       └── store/               # Zustand global state
│
└── backend/
    └── app/
        ├── routers/             # FastAPI route handlers
        ├── services/            # Business logic layer
        ├── models/              # SQLAlchemy 2.0 ORM models
        ├── schemas/             # Pydantic request/response schemas
        ├── agents/              # LangGraph agent implementations
        ├── orchestration/       # Pipeline coordinator + state machine
        ├── vector/              # pgvector semantic search
        └── jobs/                # Celery tasks + workers
```

---

## Deployment

### Frontend → Vercel

```bash
cd frontend
npx vercel --prod
```

Set the environment variable `NEXT_PUBLIC_API_URL` to your backend URL in the Vercel dashboard.

The `vercel.json` in `frontend/` already configures:
- Security headers (CSP, X-Frame-Options, etc.)
- Long-lived cache for static assets
- API proxy rewrite (update the destination URL)

### Backend → Render

1. Push your code to GitHub.
2. Create a new Render Blueprint using `render.yaml` in the repo root.
3. Fill in your secret env vars (`ANTHROPIC_API_KEY`, and `OPENAI_API_KEY` if you want optional embeddings/fallbacks) in the Render dashboard.
4. Deploy — Render will provision Postgres, Redis, the web service, and the Celery worker automatically.

After first deploy, run migrations:

```bash
# From Render shell tab on the backend service
alembic upgrade head
```

### Backend → Railway

```bash
# Install Railway CLI
npm i -g @railway/cli

railway login
railway init
railway up --service backend
```

Set environment variables via `railway variables set KEY=value`.

---

## Environment Variables

See [`.env.example`](.env.example) for a full list with descriptions.

**Required:**

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API key (primary LLM) |
| `DATABASE_URL` | PostgreSQL async URL |
| `REDIS_URL` | Redis connection URL |

**Optional:**

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | OpenAI key for optional embeddings, GPT-4o-mini fallback, and Whisper |
| `ELEVENLABS_API_KEY` | TTS for audio explanations |
| `AUDIO_STORAGE_PATH` | Where to cache generated MP3 files |

---

## Database Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Create a new migration after model changes
alembic revision --autogenerate -m "describe your change"

# Rollback one step
alembic downgrade -1
```

Migration history:
- `0001` — core subjects, lectures, segments, concepts
- `0002` — mastery tracking, flashcards, quiz
- `0003` — mind map nodes & edges
- `0004` — ElevenLabs audio cache
- `0005` — revise mode (SM-2, oral exam, revision plans)
- `0006` — semantic search (pgvector IVFFlat index, subject graph)

---

## API Reference

Interactive docs available at **http://localhost:8000/docs** (Swagger UI) or **/redoc** (ReDoc).

Core endpoint groups:

| Prefix | Description |
|---|---|
| `POST /api/v1/lectures/` | Create lecture + trigger pipeline |
| `GET /api/v1/content/{id}/` | Learn mode content |
| `GET /api/v1/breakdown/{id}/` | Break It Down content |
| `GET /api/v1/revise/{id}/` | Flashcards, quiz, oral exam, revision plan |
| `POST /api/v1/search/` | Semantic segment search |
| `POST /api/v1/search/concepts/` | Concept search |
| `GET /api/v1/subjects/{id}/graph` | Subject knowledge graph |

---

## Contributing

```bash
# Type-check frontend
cd frontend && npm run type-check

# Lint frontend
cd frontend && npm run lint

# Format (if configured)
cd backend && black . && ruff check .
```
