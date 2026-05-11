from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool
from app.config import get_settings


class Base(DeclarativeBase):
    pass


_settings = get_settings()

# NullPool is required when SQLAlchemy async is used inside Celery tasks.
# Celery calls asyncio.run() which creates a NEW event loop each time.
# A regular connection pool caches connections bound to the OLD loop,
# causing "Future attached to a different loop" on every task.
# NullPool creates a fresh connection per session — no cross-loop state.
engine = create_async_engine(
    _settings.async_database_url,
    echo=not _settings.is_production,
    poolclass=NullPool,
)

AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# Alias used by background workers / agents
async_session_factory = AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
