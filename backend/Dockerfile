# ── Stage 1: dependency builder ───────────────────────────────────────────────
FROM python:3.12-slim AS deps

WORKDIR /app

# System libs needed to compile psycopg2 / asyncpg wheels
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       libpq-dev \
       curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ── Stage 2: production image ─────────────────────────────────────────────────
FROM python:3.12-slim AS runner

WORKDIR /app

# Runtime libs only (no build tools)
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root user for security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Copy installed packages from deps stage
COPY --from=deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

COPY --chown=appuser:appgroup . .

# Force Python to flush stdout/stderr immediately so Railway logs are visible
ENV PYTHONUNBUFFERED=1

USER appuser

EXPOSE 8000

# Health check — FastAPI exposes /health
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# $PORT is injected by Railway; falls back to 8000 for local/other platforms
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --log-level info
