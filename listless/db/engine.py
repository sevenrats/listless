"""Async SQLAlchemy engine and session factory.

Supports both SQLite (aiosqlite) and PostgreSQL (asyncpg) backends.
The backend is selected by the ``LISTLESS_DATABASE_URL`` env var.
"""

from collections.abc import AsyncGenerator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from listless.config import settings

engine = create_async_engine(settings.database_url, echo=False)

# SQLite-specific: enforce foreign-key constraints on every connection.
if settings.is_sqlite:

    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a scoped async DB session."""
    async with AsyncSessionLocal() as db:
        yield db
