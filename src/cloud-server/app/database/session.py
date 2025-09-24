from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings


_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    global _engine  # noqa: PLW0603
    if _engine is None:
        # TR: Geliştirme için varsayılan SQLite; prod'da env ile override edin
        database_url = getattr(settings, "database_url", None) or "sqlite+aiosqlite:///./archbuilder.db"
        _engine = create_async_engine(database_url, echo=False, future=True)
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    global _sessionmaker  # noqa: PLW0603
    if _sessionmaker is None:
        _sessionmaker = async_sessionmaker(bind=get_engine(), expire_on_commit=False, autoflush=False, autocommit=False)
    return _sessionmaker


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    session = get_sessionmaker()()
    try:
        yield session
        await session.commit()
    except Exception:  # noqa: BLE001
        await session.rollback()
        raise
    finally:
        await session.close()


