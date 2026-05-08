# LectureLens

> AI-powered lecture companion that turns YouTube lectures into personalized study systems.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind CSS, shadcn/ui, Framer Motion |
| Backend | FastAPI, Python 3.12 |
| Database | PostgreSQL 16 + pgvector |
| Cache / Queue | Redis 7 |
| Orchestration | LangGraph |
| Infra | Docker Compose |

## Quick Start

```bash
# 1. Copy env template
cp .env.example .env
# Fill in your API keys

# 2. Start all services
docker compose up -d

# 3. Run migrations
docker compose exec backend alembic upgrade head

# 4. Visit
open http://localhost:3000
```

## Project Structure

```
lecturelens/
├── frontend/           # Next.js App Router
│   ├── app/            # Pages & layouts
│   ├── components/     # Reusable UI components
│   ├── lib/            # API client, types, hooks, utils
│   └── styles/         # Global CSS
└── backend/
    └── app/
        ├── routers/        # FastAPI route handlers
        ├── services/       # Business logic
        ├── models/         # SQLAlchemy ORM models
        ├── schemas/        # Pydantic request/response schemas
        ├── agents/         # LangGraph agent stubs
        ├── orchestration/  # Pipeline & state management
        ├── vector/         # pgvector search layer
        └── jobs/           # Background task workers
```

## Core UI Flow

1. User creates or selects a **Subject**
2. User pastes a **YouTube lecture URL**
3. User clicks **Analyze Lecture**
4. **Processing screen** shows agent pipeline progress
5. **Lecture Dashboard** opens with five modes:
   - **Learn** — structured summaries with timestamps
   - **Break It Down** — concept explanations
   - **Revise** — flashcards & quizzes
   - **Search** — semantic search over transcript
   - **Mind Map** — visual concept graph

## Development

```bash
# Frontend dev server
cd frontend && npm run dev

# Backend dev server
cd backend && uvicorn app.main:app --reload

# Run Postgres + Redis only
docker compose up postgres redis -d
```
