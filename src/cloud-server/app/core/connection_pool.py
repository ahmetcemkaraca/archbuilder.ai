"""
Connection Pool and Timeout Tuning for ArchBuilder.AI

Provides:
- Optimized database connection pooling
- Connection timeout management
- Connection health monitoring
- Pool performance metrics
"""

from __future__ import annotations

import asyncio
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

import structlog
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool, StaticPool, NullPool
from sqlalchemy.pool.events import PoolEvents

logger = structlog.get_logger(__name__)


class PoolType(str, Enum):
    """Connection pool types"""

    QUEUE = "queue"
    STATIC = "static"
    NULL = "null"


@dataclass
class PoolConfig:
    """Connection pool configuration"""

    pool_type: PoolType = PoolType.QUEUE
    pool_size: int = 20
    max_overflow: int = 30
    pool_timeout: int = 30
    pool_recycle: int = 3600
    pool_pre_ping: bool = True
    pool_reset_on_return: str = "commit"

    # Connection parameters
    connect_args: Dict[str, Any] = None

    # Timeout settings
    statement_timeout: int = 30000  # 30 seconds
    connection_timeout: int = 10  # 10 seconds
    query_timeout: int = 60  # 60 seconds

    # Health check settings
    health_check_interval: int = 30  # 30 seconds
    health_check_timeout: int = 5  # 5 seconds


@dataclass
class PoolMetrics:
    """Connection pool metrics"""

    pool_size: int
    checked_in: int
    checked_out: int
    overflow: int
    invalid: int
    total_connections: int
    utilization_percentage: float
    overflow_percentage: float
    avg_connection_time: float
    health_status: str
    last_health_check: datetime


class ConnectionPoolManager:
    """Advanced connection pool manager for ArchBuilder.AI"""

    def __init__(self, database_url: str, config: PoolConfig):
        self.database_url = database_url
        self.config = config
        self.engine: Optional[Engine] = None
        self._health_check_task: Optional[asyncio.Task] = None
        self._metrics_history: List[PoolMetrics] = []
        self._connection_times: List[float] = []

    def create_engine(self) -> Engine:
        """Create optimized database engine with connection pooling"""

        # Configure connection arguments
        connect_args = self.config.connect_args or {}
        connect_args.update(
            {
                'command_timeout': self.config.statement_timeout,
                'connect_timeout': self.config.connection_timeout,
                'server_settings': {
                    'statement_timeout': f'{self.config.statement_timeout}ms',
                    'idle_in_transaction_session_timeout': f'{self.config.statement_timeout}ms',
                },
            }
        )

        # Configure pool based on type
        pool_kwargs = {
            'pool_recycle': self.config.pool_recycle,
            'pool_pre_ping': self.config.pool_pre_ping,
            'pool_reset_on_return': self.config.pool_reset_on_return,
            'connect_args': connect_args,
        }

        if self.config.pool_type == PoolType.QUEUE:
            pool_kwargs.update(
                {
                    'poolclass': QueuePool,
                    'pool_size': self.config.pool_size,
                    'max_overflow': self.config.max_overflow,
                    'pool_timeout': self.config.pool_timeout,
                }
            )
        elif self.config.pool_type == PoolType.STATIC:
            pool_kwargs.update(
                {'poolclass': StaticPool, 'pool_size': self.config.pool_size}
            )
        elif self.config.pool_type == PoolType.NULL:
            pool_kwargs.update({'poolclass': NullPool})

        # Create engine
        self.engine = create_engine(
            self.database_url,
            **pool_kwargs,
            echo=False,  # Set to True for SQL debugging
            echo_pool=False,  # Set to True for pool debugging
        )

        # Add event listeners for monitoring
        self._add_pool_event_listeners()

        logger.info(
            "Database engine created",
            pool_type=self.config.pool_type.value,
            pool_size=self.config.pool_size,
            max_overflow=self.config.max_overflow,
        )

        return self.engine

    def _add_pool_event_listeners(self) -> None:
        """Add event listeners for pool monitoring"""

        @event.listens_for(self.engine, "connect")
        def receive_connect(dbapi_connection, connection_record):
            connection_record._start_time = time.time()
            logger.debug("Database connection established")

        @event.listens_for(self.engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            connection_record._checkout_time = time.time()
            if hasattr(connection_record, '_start_time'):
                connection_time = time.time() - connection_record._start_time
                self._connection_times.append(connection_time)
                logger.debug("Connection checked out", connection_time=connection_time)

        @event.listens_for(self.engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            if hasattr(connection_record, '_checkout_time'):
                checkout_duration = time.time() - connection_record._checkout_time
                logger.debug(
                    "Connection checked in", checkout_duration=checkout_duration
                )

    async def start_health_monitoring(self) -> None:
        """Start connection pool health monitoring"""
        if self._health_check_task:
            return

        self._health_check_task = asyncio.create_task(self._health_check_loop())
        logger.info("Connection pool health monitoring started")

    async def stop_health_monitoring(self) -> None:
        """Stop connection pool health monitoring"""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
            self._health_check_task = None
            logger.info("Connection pool health monitoring stopped")

    async def _health_check_loop(self) -> None:
        """Health check loop for connection pool"""
        while True:
            try:
                await asyncio.sleep(self.config.health_check_interval)
                await self._perform_health_check()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Health check failed", error=str(e))

    async def _perform_health_check(self) -> None:
        """Perform health check on connection pool"""
        if not self.engine:
            return

        start_time = time.time()
        health_status = "healthy"

        try:
            # Test database connection
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()

            # Get pool metrics
            pool = self.engine.pool
            if hasattr(pool, 'size'):
                metrics = PoolMetrics(
                    pool_size=pool.size(),
                    checked_in=pool.checkedin(),
                    checked_out=pool.checkedout(),
                    overflow=pool.overflow(),
                    invalid=pool.invalid(),
                    total_connections=pool.size() + pool.overflow(),
                    utilization_percentage=(
                        (pool.checkedout() / pool.size()) * 100
                        if pool.size() > 0
                        else 0
                    ),
                    overflow_percentage=(
                        (pool.overflow() / pool.size()) * 100 if pool.size() > 0 else 0
                    ),
                    avg_connection_time=(
                        sum(self._connection_times[-100:])
                        / min(len(self._connection_times), 100)
                        if self._connection_times
                        else 0.0
                    ),
                    health_status=health_status,
                    last_health_check=datetime.utcnow(),
                )

                self._metrics_history.append(metrics)

                # Keep only last 100 metrics
                if len(self._metrics_history) > 100:
                    self._metrics_history = self._metrics_history[-100:]

                # Log warnings for unhealthy conditions
                if metrics.utilization_percentage > 80:
                    logger.warning(
                        "High pool utilization",
                        utilization=metrics.utilization_percentage,
                    )

                if metrics.overflow > 0:
                    logger.warning("Pool overflow detected", overflow=metrics.overflow)

                logger.debug(
                    "Pool health check completed",
                    utilization=metrics.utilization_percentage,
                    overflow=metrics.overflow,
                    avg_connection_time=metrics.avg_connection_time,
                )

        except Exception as e:
            health_status = "unhealthy"
            logger.error("Database health check failed", error=str(e))

    def get_pool_metrics(self) -> Optional[PoolMetrics]:
        """Get current pool metrics"""
        if not self.engine:
            return None

        pool = self.engine.pool
        if not hasattr(pool, 'size'):
            return None

        return PoolMetrics(
            pool_size=pool.size(),
            checked_in=pool.checkedin(),
            checked_out=pool.checkedout(),
            overflow=pool.overflow(),
            invalid=pool.invalid(),
            total_connections=pool.size() + pool.overflow(),
            utilization_percentage=(
                (pool.checkedout() / pool.size()) * 100 if pool.size() > 0 else 0
            ),
            overflow_percentage=(
                (pool.overflow() / pool.size()) * 100 if pool.size() > 0 else 0
            ),
            avg_connection_time=(
                sum(self._connection_times[-100:])
                / min(len(self._connection_times), 100)
                if self._connection_times
                else 0.0
            ),
            health_status="healthy",
            last_health_check=datetime.utcnow(),
        )

    def get_metrics_history(self, hours: int = 24) -> List[PoolMetrics]:
        """Get pool metrics history"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return [m for m in self._metrics_history if m.last_health_check > cutoff_time]

    def get_optimization_recommendations(self) -> List[str]:
        """Get pool optimization recommendations"""
        recommendations = []

        if not self.engine:
            return recommendations

        metrics = self.get_pool_metrics()
        if not metrics:
            return recommendations

        # High utilization recommendation
        if metrics.utilization_percentage > 80:
            recommendations.append(
                f"High pool utilization ({metrics.utilization_percentage:.1f}%) - consider increasing pool size"
            )

        # Overflow recommendation
        if metrics.overflow > 0:
            recommendations.append(
                f"Pool overflow detected ({metrics.overflow} connections) - increase pool size or max_overflow"
            )

        # Low utilization recommendation
        if metrics.utilization_percentage < 20:
            recommendations.append(
                f"Low pool utilization ({metrics.utilization_percentage:.1f}%) - consider decreasing pool size"
            )

        # Connection time recommendation
        if metrics.avg_connection_time > 1.0:
            recommendations.append(
                f"Slow connection times ({metrics.avg_connection_time:.2f}s) - check network and database performance"
            )

        return recommendations

    async def optimize_pool_settings(self) -> Dict[str, Any]:
        """Analyze and recommend pool optimization settings"""
        if not self.engine:
            return {"error": "Engine not initialized"}

        metrics = self.get_pool_metrics()
        if not metrics:
            return {"error": "No metrics available"}

        # Analyze historical data
        history = self.get_metrics_history(24)
        if not history:
            return {"error": "No historical data available"}

        # Calculate average utilization
        avg_utilization = sum(m.utilization_percentage for m in history) / len(history)
        max_utilization = max(m.utilization_percentage for m in history)
        avg_overflow = sum(m.overflow for m in history) / len(history)

        # Generate recommendations
        recommendations = {
            "current_settings": {
                "pool_size": self.config.pool_size,
                "max_overflow": self.config.max_overflow,
                "pool_timeout": self.config.pool_timeout,
            },
            "current_metrics": {
                "utilization_percentage": metrics.utilization_percentage,
                "overflow": metrics.overflow,
                "avg_connection_time": metrics.avg_connection_time,
            },
            "historical_analysis": {
                "avg_utilization": avg_utilization,
                "max_utilization": max_utilization,
                "avg_overflow": avg_overflow,
            },
            "recommendations": [],
        }

        # Pool size recommendations
        if avg_utilization > 70:
            recommended_size = int(self.config.pool_size * 1.5)
            recommendations["recommendations"].append(
                {
                    "type": "pool_size",
                    "current": self.config.pool_size,
                    "recommended": recommended_size,
                    "reason": f"High average utilization ({avg_utilization:.1f}%)",
                }
            )

        # Max overflow recommendations
        if avg_overflow > 5:
            recommended_overflow = int(self.config.max_overflow * 1.5)
            recommendations["recommendations"].append(
                {
                    "type": "max_overflow",
                    "current": self.config.max_overflow,
                    "recommended": recommended_overflow,
                    "reason": f"Frequent overflow ({avg_overflow:.1f} average)",
                }
            )

        # Timeout recommendations
        if metrics.avg_connection_time > 2.0:
            recommendations["recommendations"].append(
                {
                    "type": "timeout",
                    "current": self.config.pool_timeout,
                    "recommended": self.config.pool_timeout * 2,
                    "reason": f"Slow connection times ({metrics.avg_connection_time:.2f}s)",
                }
            )

        return recommendations

    def close(self) -> None:
        """Close connection pool"""
        if self.engine:
            self.engine.dispose()
            logger.info("Connection pool closed")


@asynccontextmanager
async def managed_connection(pool_manager: ConnectionPoolManager):
    """Context manager for managed database connections"""
    if not pool_manager.engine:
        raise RuntimeError("Pool manager not initialized")

    connection = None
    start_time = time.time()

    try:
        connection = pool_manager.engine.connect()
        yield connection
    except Exception as e:
        logger.error("Database connection error", error=str(e))
        raise
    finally:
        if connection:
            connection.close()
            connection_time = time.time() - start_time
            logger.debug("Connection closed", connection_time=connection_time)


# Global pool manager instance
_pool_manager: Optional[ConnectionPoolManager] = None


def initialize_pool_manager(
    database_url: str, config: PoolConfig
) -> ConnectionPoolManager:
    """Initialize global pool manager"""
    global _pool_manager

    _pool_manager = ConnectionPoolManager(database_url, config)
    _pool_manager.create_engine()

    return _pool_manager


def get_pool_manager() -> ConnectionPoolManager:
    """Get global pool manager instance"""
    if _pool_manager is None:
        raise RuntimeError("Pool manager not initialized")
    return _pool_manager


async def start_pool_monitoring() -> None:
    """Start global pool monitoring"""
    if _pool_manager:
        await _pool_manager.start_health_monitoring()


async def stop_pool_monitoring() -> None:
    """Stop global pool monitoring"""
    if _pool_manager:
        await _pool_manager.stop_health_monitoring()
        _pool_manager.close()
