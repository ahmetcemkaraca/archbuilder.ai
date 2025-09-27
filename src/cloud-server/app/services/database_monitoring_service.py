from __future__ import annotations

import asyncio
import logging
import structlog
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import (
    get_sessionmaker,
    get_connection_stats,
    check_connection_health,
)

# TR: Structured logging setup
logger = structlog.get_logger(__name__)


@dataclass
class ConnectionHealth:
    """TR: Database connection sağlık bilgisi"""

    is_healthy: bool
    response_time_ms: float
    active_connections: int
    pool_size: int
    checked_out_connections: int
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SlowQuery:
    """TR: Yavaş sorgu bilgisi"""

    query: str
    duration_ms: float
    correlation_id: Optional[str]
    timestamp: datetime
    parameters: Optional[Dict[str, Any]]


class DatabaseMonitoringService:
    """TR: Database performance ve connection monitoring servisi"""

    def __init__(self):
        self._slow_queries: List[SlowQuery] = []
        self._health_history: List[ConnectionHealth] = []
        self._monitoring_task: Optional[asyncio.Task] = None
        self._slow_query_threshold_ms = 1000  # TR: 1 saniye üstü yavaş

    async def start_monitoring(self, interval_seconds: int = 60):
        """TR: Monitoring taskını başlat"""
        if self._monitoring_task and not self._monitoring_task.done():
            logger.warning("database_monitoring_already_running")
            return

        self._monitoring_task = asyncio.create_task(
            self._monitoring_loop(interval_seconds)
        )
        logger.info("database_monitoring_started", interval_seconds=interval_seconds)

    async def stop_monitoring(self):
        """TR: Monitoring taskını durdur"""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            logger.info("database_monitoring_stopped")

    async def _monitoring_loop(self, interval_seconds: int):
        """TR: Ana monitoring döngüsü"""
        while True:
            try:
                await self._collect_health_metrics()
                await self._check_connection_leaks()
                await self._cleanup_old_data()
                await asyncio.sleep(interval_seconds)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("database_monitoring_error", error=str(e), exc_info=True)
                await asyncio.sleep(interval_seconds)

    async def _collect_health_metrics(self):
        """TR: Sağlık metriklerini topla"""
        start_time = datetime.utcnow()

        # TR: Connection health check
        is_healthy = await check_connection_health()

        # TR: Response time hesapla
        response_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        # TR: Connection pool stats
        pool_stats = await get_connection_stats()

        health = ConnectionHealth(
            is_healthy=is_healthy,
            response_time_ms=response_time_ms,
            active_connections=pool_stats.get("active_connections", 0),
            pool_size=pool_stats.get("pool_size", 0),
            checked_out_connections=pool_stats.get("checked_out", 0),
            timestamp=datetime.utcnow(),
        )

        self._health_history.append(health)

        # TR: Alert logic
        if response_time_ms > 5000:  # 5 saniye üstü
            logger.warning(
                "database_slow_response_detected",
                response_time_ms=response_time_ms,
                **health.to_dict(),
            )

        if not is_healthy:
            logger.error("database_health_check_failed", **health.to_dict())

    async def _check_connection_leaks(self):
        """TR: Connection leak detection"""
        pool_stats = await get_connection_stats()

        active_connections = pool_stats.get("active_connections", 0)
        checked_out = pool_stats.get("checked_out", 0)
        pool_size = pool_stats.get("pool_size", 0)

        # TR: Connection leak uyarıları
        if checked_out > pool_size * 0.9:  # %90 üstü kullanım
            logger.warning(
                "high_connection_usage_detected",
                checked_out=checked_out,
                pool_size=pool_size,
                usage_percent=(checked_out / pool_size) * 100,
            )

        if active_connections > pool_size * 1.5:  # Pool size'ın 1.5 katı
            logger.error(
                "potential_connection_leak_detected",
                active_connections=active_connections,
                pool_size=pool_size,
                **pool_stats,
            )

    async def _cleanup_old_data(self):
        """TR: Eski monitoring verilerini temizle"""
        cutoff_time = datetime.utcnow() - timedelta(hours=24)

        # TR: 24 saatten eski health verilerini sil
        self._health_history = [
            h for h in self._health_history if h.timestamp > cutoff_time
        ]

        # TR: 24 saatten eski slow queryları sil
        self._slow_queries = [
            q for q in self._slow_queries if q.timestamp > cutoff_time
        ]

    def track_slow_query(
        self,
        query: str,
        duration_ms: float,
        correlation_id: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ):
        """TR: Yavaş sorguyu kaydet"""
        if duration_ms > self._slow_query_threshold_ms:
            slow_query = SlowQuery(
                query=query[:500],  # TR: İlk 500 karakter
                duration_ms=duration_ms,
                correlation_id=correlation_id,
                timestamp=datetime.utcnow(),
                parameters=parameters,
            )

            self._slow_queries.append(slow_query)

            logger.warning(
                "slow_query_detected",
                duration_ms=duration_ms,
                correlation_id=correlation_id,
                query_preview=query[:100],
            )

    async def get_health_summary(self) -> Dict[str, Any]:
        """TR: Sağlık özeti döndür"""
        if not self._health_history:
            return {"status": "no_data", "message": "No health data collected yet"}

        recent_health = self._health_history[-10:]  # Son 10 kayıt

        avg_response_time = sum(h.response_time_ms for h in recent_health) / len(
            recent_health
        )
        success_rate = sum(1 for h in recent_health if h.is_healthy) / len(
            recent_health
        )

        current_stats = await get_connection_stats()

        return {
            "status": "healthy" if success_rate > 0.9 else "degraded",
            "average_response_time_ms": avg_response_time,
            "success_rate": success_rate,
            "slow_queries_count": len(self._slow_queries),
            "current_pool_stats": current_stats,
            "last_check": self._health_history[-1].timestamp.isoformat(),
            "health_checks_count": len(self._health_history),
        }

    async def get_slow_queries(self, limit: int = 50) -> List[Dict[str, Any]]:
        """TR: Yavaş sorguları döndür"""
        recent_queries = sorted(
            self._slow_queries, key=lambda q: q.timestamp, reverse=True
        )[:limit]

        return [
            {
                "query": q.query,
                "duration_ms": q.duration_ms,
                "correlation_id": q.correlation_id,
                "timestamp": q.timestamp.isoformat(),
                "parameters": q.parameters,
            }
            for q in recent_queries
        ]

    async def run_database_diagnostics(self) -> Dict[str, Any]:
        """TR: Kapsamlı database diagnostic"""
        session = get_sessionmaker()()

        try:
            async with session:
                # TR: PostgreSQL specific diagnostics
                diagnostics = {}

                # TR: Active connections
                result = await session.execute(
                    text(
                        """
                    SELECT 
                        count(*) as total_connections,
                        count(*) FILTER (WHERE state = 'active') as active_connections,
                        count(*) FILTER (WHERE state = 'idle') as idle_connections
                    FROM pg_stat_activity 
                    WHERE datname = current_database()
                """
                    )
                )

                row = result.first()
                if row:
                    diagnostics["connections"] = {
                        "total": row[0],
                        "active": row[1],
                        "idle": row[2],
                    }

                # TR: Long running queries
                result = await session.execute(
                    text(
                        """
                    SELECT 
                        query,
                        state,
                        now() - query_start as duration
                    FROM pg_stat_activity 
                    WHERE datname = current_database() 
                      AND state = 'active'
                      AND now() - query_start > interval '30 seconds'
                    ORDER BY query_start
                    LIMIT 10
                """
                    )
                )

                long_queries = []
                for row in result:
                    long_queries.append(
                        {
                            "query": row[0][:200],
                            "state": row[1],
                            "duration": str(row[2]),
                        }
                    )

                diagnostics["long_running_queries"] = long_queries

                # TR: Database size
                result = await session.execute(
                    text(
                        """
                    SELECT pg_size_pretty(pg_database_size(current_database())) as db_size
                """
                    )
                )

                db_size = result.scalar()
                diagnostics["database_size"] = db_size

                return {
                    "status": "success",
                    "timestamp": datetime.utcnow().isoformat(),
                    "diagnostics": diagnostics,
                }

        except Exception as e:
            logger.error("database_diagnostics_failed", error=str(e), exc_info=True)
            return {
                "status": "error",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
            }


# TR: Global monitoring service instance
_monitoring_service: Optional[DatabaseMonitoringService] = None


def get_database_monitoring_service() -> DatabaseMonitoringService:
    """TR: Database monitoring service singleton"""
    global _monitoring_service
    if _monitoring_service is None:
        _monitoring_service = DatabaseMonitoringService()
    return _monitoring_service
