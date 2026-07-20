from collections.abc import AsyncGenerator
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from whatsapp_assistant.configs.settings import get_settings


@lru_cache
def get_engine() -> AsyncEngine:
    """Cached accessor so the engine (and its connection pool) is created once per process."""
    settings = get_settings()
    return create_async_engine(settings.database_url)


@lru_cache
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(get_engine(), expire_on_commit=False)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an AsyncSession, one per request."""
    async with get_sessionmaker()() as session:
        yield session
