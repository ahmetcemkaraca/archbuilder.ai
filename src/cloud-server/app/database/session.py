from __future__ import annotations

from typing import AsyncGenerator

try:
    from sqlalchemy.ext.asyncio import (
        AsyncEngine,
        AsyncSession,
        async_sessionmaker,
        create_async_engine,
    )
    from app.core.config import settings

    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """TR: Optimize edilmiş async database engine"""
    if not SQLALCHEMY_AVAILABLE:
        raise ImportError("SQLAlchemy is not available")

    global _engine  # noqa: PLW0603
    if _engine is None:
        # TR: Geliştirme için varsayılan SQLite; prod'da env ile override edin
        # TR: Default database URL
        database_url = "sqlite+aiosqlite:///./archbuilder.db"

        # TR: Try to get settings if available
        try:
            database_url = settings.database_url or database_url
        except NameError:
            pass  # TR: settings not available, use default

        # TR: PostgreSQL connection pool optimizasyonları
        config = {}
        if database_url.startswith("postgresql"):
            # TR: PostgreSQL için asyncpg kullan
            if not database_url.startswith("postgresql+asyncpg"):
                database_url = database_url.replace(
                    "postgresql://", "postgresql+asyncpg://"
                )

            # TR: Production-ready pool settings with defaults
            try:
                pool_size = settings.db_pool_size
                max_overflow = settings.db_max_overflow
                pool_recycle = settings.db_pool_recycle
                pool_timeout = settings.db_pool_timeout
                echo = settings.db_echo
            except (NameError, AttributeError):
                # TR: Fallback to defaults
                pool_size = 20
                max_overflow = 30
                pool_recycle = 3600
                pool_timeout = 30
                echo = False

            config = {
                "pool_size": pool_size,
                "max_overflow": max_overflow,
                "pool_pre_ping": True,  # TR: Connection sağlığını kontrol et
                "pool_recycle": pool_recycle,
                "pool_timeout": pool_timeout,
                "echo": echo,
                "connect_args": {
                    "server_settings": {
                        "application_name": "ArchBuilder.AI",
                        "jit": "off",  # TR: Küçük queryler için JIT kapalı
                    }
                },
            }
        else:
            # TR: SQLite config
            try:
                echo = settings.db_echo
            except (NameError, AttributeError):
                echo = False

            config = {"echo": echo, "connect_args": {"check_same_thread": False}}

        _engine = create_async_engine(database_url, future=True, **config)

    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """TR: Optimize edilmiş session factory"""
    if not SQLALCHEMY_AVAILABLE:
        raise ImportError("SQLAlchemy is not available")

    global _sessionmaker  # noqa: PLW0603
    if _sessionmaker is None:
        _sessionmaker = async_sessionmaker(
            bind=get_engine(),
            expire_on_commit=False,  # TR: Session commit'ten sonra otomatik expire etme
            autoflush=False,  # TR: Manuel flush kontrolü için
            autocommit=False,  # TR: Explicit transaction yönetimi
        )
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
