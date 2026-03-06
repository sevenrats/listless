"""Shared fixtures for the Listless test suite."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from listless.db.models import Base, MappingType
from listless.services.id_mapping import seed_mapping_types


@pytest.fixture()
async def async_db():
    """Yield a transactional async session backed by an in-memory SQLite DB."""
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as session:
        await seed_mapping_types(session)
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
