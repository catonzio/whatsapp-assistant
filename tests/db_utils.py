"""Shared helper for tests that need a real (but throwaway) async DB.

Uses an in-memory SQLite engine restricted to the specific tables under test
(`tables=[...]`) rather than `Base.metadata.create_all()` for everything:
some models (Item, ListItem) use `postgresql.JSONB`, which SQLite can't
create. Restricting DDL to just the tables a given test needs sidesteps that
without requiring a real Postgres for fast, isolated unit tests.
"""

from sqlalchemy import Table
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from whatsapp_assistant.database.base import Base


async def make_sqlite_sessionmaker(*tables: Table) -> async_sessionmaker[AsyncSession]:
    # StaticPool: a plain in-memory SQLite DB is per-connection, so two
    # sessions checked out concurrently (e.g. asyncio.gather in a race test)
    # would otherwise see two separate empty databases. StaticPool keeps
    # every session on the one connection that actually has the schema/data.
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, tables=list(tables))
    return async_sessionmaker(engine, expire_on_commit=False)
