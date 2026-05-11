from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import engine, Base
from app.routers import subjects, lectures, processing, content
from app.routers import breakdown, revise, search

settings = get_settings()


async def _init_db() -> None:
    """Create tables + extra columns. Retries up to 10× so Railway Postgres
    startup race doesn't kill the healthcheck."""
    import asyncio
    from sqlalchemy import text

    extras = [
        "ALTER TABLE processing_jobs ADD COLUMN IF NOT EXISTS stage_errors JSONB",
        "ALTER TABLE processing_jobs ADD COLUMN IF NOT EXISTS progress_metadata JSONB",
        "ALTER TABLE semantic_segments ADD COLUMN IF NOT EXISTS topic_label VARCHAR(200)",
        "ALTER TABLE semantic_segments ADD COLUMN IF NOT EXISTS topic_boundary_score FLOAT",
        "ALTER TABLE concepts ADD COLUMN IF NOT EXISTS why_it_matters TEXT",
        "ALTER TABLE concepts ADD COLUMN IF NOT EXISTS prerequisites JSONB DEFAULT '[]'",
        "ALTER TABLE concepts ADD COLUMN IF NOT EXISTS related_concepts JSONB DEFAULT '[]'",
        "ALTER TABLE concepts ADD COLUMN IF NOT EXISTS evidence_quote TEXT",
        "ALTER TABLE concepts ADD COLUMN IF NOT EXISTS exam_likelihood FLOAT DEFAULT 0.5",
        "ALTER TABLE concepts ADD COLUMN IF NOT EXISTS time_spent_seconds FLOAT",
        "ALTER TABLE concepts ADD COLUMN IF NOT EXISTS evidence_timestamps JSONB DEFAULT '[]'",
        "ALTER TABLE lectures ADD COLUMN IF NOT EXISTS channel_name VARCHAR(200)",
        "ALTER TABLE lectures ADD COLUMN IF NOT EXISTS processing_error TEXT",
        "ALTER TABLE lectures ADD COLUMN IF NOT EXISTS processed_at TIMESTAMPTZ",
    ]

    for attempt in range(10):
        try:
            async with engine.begin() as conn:
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                await conn.run_sync(Base.metadata.create_all)
                for sql in extras:
                    try:
                        await conn.execute(text(sql))
                    except Exception:
                        pass  # column already exists
            return  # success
        except Exception as exc:
            wait = 3 * (attempt + 1)
            print(f"[startup] DB not ready (attempt {attempt + 1}/10): {exc} — retrying in {wait}s")
            await asyncio.sleep(wait)

    print("[startup] WARNING: DB init failed after 10 attempts — app will start anyway")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run DB init in background so /health is reachable immediately even if
    # Postgres is still booting (Railway starts services in parallel).
    import asyncio
    asyncio.create_task(_init_db())
    yield
    await engine.dispose()


app = FastAPI(
    title="LectureLens API",
    description="AI-powered lecture companion backend",
    version="0.1.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
_cors_origins = settings.CORS_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    # credentials + wildcard origin is invalid per CORS spec — disable when using *
    allow_credentials="*" not in _cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
API_PREFIX = "/api/v1"

app.include_router(subjects.router, prefix=API_PREFIX)
app.include_router(lectures.router, prefix=API_PREFIX)
app.include_router(processing.router, prefix=API_PREFIX)
app.include_router(content.router, prefix=API_PREFIX)
app.include_router(breakdown.router, prefix=API_PREFIX)
app.include_router(revise.router, prefix=API_PREFIX)
app.include_router(search.router, prefix=API_PREFIX)


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["meta"])
async def health():
    return {"status": "ok", "version": app.version}
