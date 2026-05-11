from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import engine, Base
from app.routers import subjects, lectures, processing, content
from app.routers import breakdown, revise, search

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Dev only: create tables directly from models (fast, no migrations needed)
    # Production: tables are managed by `alembic upgrade head` in the start command
    if not settings.is_production:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
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
