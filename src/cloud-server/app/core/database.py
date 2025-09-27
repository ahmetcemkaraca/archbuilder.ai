"""
Database Connection and Management for ArchBuilder.AI

Handles database connections, transactions, and session management.

Author: ArchBuilder.AI Team
Date: 2025-09-26
"""

import asyncio
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

import asyncpg
from structlog import get_logger

from .exceptions import DatabaseError, ConfigurationError

logger = get_logger(__name__)


class DatabaseManager:
    """Database connection manager"""

    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.database_url = os.getenv("DATABASE_URL")

        if not self.database_url:
            raise ConfigurationError("DATABASE_URL environment variable not set")

    async def initialize(self) -> None:
        """Initialize database connection pool"""

        try:
            self.pool = await asyncpg.create_pool(
                self.database_url, min_size=5, max_size=20, command_timeout=30
            )

            logger.info("Database connection pool initialized")

        except Exception as e:
            logger.error("Failed to initialize database pool", error=str(e))
            raise DatabaseError(f"Database initialization failed: {str(e)}")

    async def close(self) -> None:
        """Close database connection pool"""

        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")

    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[asyncpg.Connection, None]:
        """Get database connection from pool"""

        if not self.pool:
            raise DatabaseError("Database pool not initialized")

        async with self.pool.acquire() as connection:
            yield connection

    @asynccontextmanager
    async def get_transaction(self) -> AsyncGenerator[asyncpg.Connection, None]:
        """Get database transaction"""

        async with self.get_connection() as connection:
            async with connection.transaction():
                yield connection


# Global database manager instance
db_manager = DatabaseManager()


async def get_database() -> DatabaseManager:
    """Get database manager instance"""
    return db_manager


async def initialize_database():
    """Initialize database connection"""
    await db_manager.initialize()


async def close_database():
    """Close database connection"""
    await db_manager.close()
