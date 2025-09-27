from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional, Union, Type
from datetime import datetime
from dataclasses import dataclass
import time

try:
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import DeclarativeBase
    from sqlalchemy.sql import Select, Update, Delete, Insert

    from app.database.session import get_sessionmaker
    from app.services.database_monitoring_service import get_database_monitoring_service

    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False

# TR: Structured logging setup
logger = logging.getLogger(__name__)


@dataclass
class QueryPerformanceMetrics:
    """TR: Query performance metrikleri"""

    query_hash: str
    execution_count: int
    total_duration_ms: float
    avg_duration_ms: float
    min_duration_ms: float
    max_duration_ms: float
    last_executed: datetime


class DatabaseOptimizationService:
    """TR: Database query optimization ve performance tuning servisi"""

    def __init__(self):
        if not SQLALCHEMY_AVAILABLE:
            raise ImportError("SQLAlchemy is not available")

        self._query_metrics: Dict[str, QueryPerformanceMetrics] = {}
        self._monitoring_service = get_database_monitoring_service()

    async def execute_optimized_query(
        self,
        session: AsyncSession,
        query: Union[Select, Update, Delete, Insert, str],
        parameters: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        timeout_seconds: int = 30,
    ) -> Any:
        """TR: Optimize edilmiş query execution"""

        start_time = time.perf_counter()
        query_str = str(query) if not isinstance(query, str) else query
        query_hash = str(hash(query_str))

        try:
            # TR: Query execution
            if isinstance(query, str):
                result = await session.execute(text(query), parameters or {})
            else:
                result = await session.execute(query)

            # TR: Performance tracking
            duration_ms = (time.perf_counter() - start_time) * 1000

            # TR: Metrics update
            self._update_query_metrics(query_hash, duration_ms, query_str)

            # TR: Slow query tracking
            self._monitoring_service.track_slow_query(
                query=query_str,
                duration_ms=duration_ms,
                correlation_id=correlation_id,
                parameters=parameters,
            )

            logger.debug(
                f"query_executed duration_ms={duration_ms} correlation_id={correlation_id} query_hash={query_hash}"
            )

            return result

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000

            logger.error(
                "query_execution_failed",
                error=str(e),
                duration_ms=duration_ms,
                correlation_id=correlation_id,
                query_hash=query_hash,
                exc_info=True,
            )
            raise

    def _update_query_metrics(
        self, query_hash: str, duration_ms: float, query_str: str
    ):
        """TR: Query performance metriklerini güncelle"""

        if query_hash in self._query_metrics:
            metrics = self._query_metrics[query_hash]
            metrics.execution_count += 1
            metrics.total_duration_ms += duration_ms
            metrics.avg_duration_ms = (
                metrics.total_duration_ms / metrics.execution_count
            )
            metrics.min_duration_ms = min(metrics.min_duration_ms, duration_ms)
            metrics.max_duration_ms = max(metrics.max_duration_ms, duration_ms)
            metrics.last_executed = datetime.utcnow()
        else:
            self._query_metrics[query_hash] = QueryPerformanceMetrics(
                query_hash=query_hash,
                execution_count=1,
                total_duration_ms=duration_ms,
                avg_duration_ms=duration_ms,
                min_duration_ms=duration_ms,
                max_duration_ms=duration_ms,
                last_executed=datetime.utcnow(),
            )

    async def analyze_slow_queries(
        self, threshold_ms: float = 1000
    ) -> List[Dict[str, Any]]:
        """TR: Yavaş queryları analiz et"""

        slow_queries = [
            {
                "query_hash": metrics.query_hash,
                "avg_duration_ms": metrics.avg_duration_ms,
                "max_duration_ms": metrics.max_duration_ms,
                "execution_count": metrics.execution_count,
                "last_executed": metrics.last_executed.isoformat(),
            }
            for metrics in self._query_metrics.values()
            if metrics.avg_duration_ms > threshold_ms
        ]

        # TR: En yavaş queryleri önce
        slow_queries.sort(key=lambda x: x["avg_duration_ms"], reverse=True)

        return slow_queries

    async def suggest_indexes(
        self, model_class: Type[DeclarativeBase]
    ) -> List[Dict[str, Any]]:
        """TR: Model için index önerileri"""

        suggestions = []
        table = model_class.__table__

        # TR: Foreign key columnları için index önerisi
        for fk in table.foreign_keys:
            column = fk.parent
            if not any(column in idx.columns for idx in table.indexes):
                suggestions.append(
                    {
                        "type": "foreign_key_index",
                        "table": table.name,
                        "column": column.name,
                        "reason": "Foreign key column should be indexed for JOIN performance",
                        "index_sql": f"CREATE INDEX idx_{table.name}_{column.name} ON {table.name} ({column.name});",
                    }
                )

        # TR: Frequently queried columnlar için composite index önerisi
        # Bu gerçek usage patterns'e göre geliştirilmeli

        return suggestions

    async def create_recommended_indexes(
        self, recommendations: List[Dict[str, Any]], execute: bool = False
    ) -> Dict[str, Any]:
        """TR: Önerilen indexleri oluştur"""

        session = get_sessionmaker()()
        created_indexes = []
        errors = []

        try:
            async with session:
                for rec in recommendations:
                    try:
                        if execute and rec.get("index_sql"):
                            await session.execute(text(rec["index_sql"]))
                            created_indexes.append(rec)

                            logger.info(
                                "database_index_created",
                                table=rec.get("table"),
                                column=rec.get("column"),
                                index_type=rec.get("type"),
                            )
                        else:
                            # TR: Dry run mode
                            created_indexes.append(rec)

                    except Exception as e:
                        error_info = {"recommendation": rec, "error": str(e)}
                        errors.append(error_info)

                        logger.error(
                            "index_creation_failed", **error_info, exc_info=True
                        )

                if execute and created_indexes:
                    await session.commit()

        except Exception as e:
            await session.rollback()
            logger.error(
                "index_creation_transaction_failed", error=str(e), exc_info=True
            )
            raise

        finally:
            await session.close()

        return {
            "created_count": len(created_indexes),
            "error_count": len(errors),
            "created_indexes": created_indexes,
            "errors": errors,
            "dry_run": not execute,
        }

    async def analyze_query_plan(
        self, query: str, parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """TR: PostgreSQL query plan analizi"""

        session = get_sessionmaker()()

        try:
            async with session:
                # TR: EXPLAIN ANALYZE query
                explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}"
                result = await session.execute(text(explain_query), parameters or {})

                query_plan = result.scalar()

                # TR: Plan analizi
                analysis = self._analyze_execution_plan(
                    query_plan[0] if query_plan else {}
                )

                return {
                    "query": query,
                    "execution_plan": query_plan,
                    "analysis": analysis,
                    "timestamp": datetime.utcnow().isoformat(),
                }

        except Exception as e:
            logger.error("query_plan_analysis_failed", error=str(e), exc_info=True)
            return {
                "query": query,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

        finally:
            await session.close()

    def _analyze_execution_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """TR: Execution plan analizi"""

        analysis = {
            "total_cost": plan.get("Total Cost", 0),
            "actual_total_time": plan.get("Actual Total Time", 0),
            "planning_time": plan.get("Planning Time", 0),
            "execution_time": plan.get("Execution Time", 0),
            "recommendations": [],
        }

        # TR: Seq Scan uyarıları
        if self._has_sequential_scan(plan):
            analysis["recommendations"].append(
                {
                    "type": "sequential_scan_detected",
                    "message": "Sequential scans detected. Consider adding indexes.",
                    "severity": "warning",
                }
            )

        # TR: Yüksek cost uyarıları
        if plan.get("Total Cost", 0) > 10000:
            analysis["recommendations"].append(
                {
                    "type": "high_cost_query",
                    "message": "Query has high cost. Consider optimization.",
                    "severity": "error",
                }
            )

        # TR: Execution time uyarıları
        if plan.get("Actual Total Time", 0) > 1000:
            analysis["recommendations"].append(
                {
                    "type": "slow_execution",
                    "message": "Query execution is slow. Review query structure.",
                    "severity": "warning",
                }
            )

        return analysis

    def _has_sequential_scan(self, node: Dict[str, Any]) -> bool:
        """TR: Plan içinde sequential scan var mı kontrol et"""

        if node.get("Node Type") == "Seq Scan":
            return True

        # TR: Nested planları kontrol et
        for plan in node.get("Plans", []):
            if self._has_sequential_scan(plan):
                return True

        return False

    async def get_performance_summary(self) -> Dict[str, Any]:
        """TR: Database performance özeti"""

        if not self._query_metrics:
            return {"message": "No query metrics available"}

        # TR: Genel metrikler
        total_queries = len(self._query_metrics)
        avg_duration = (
            sum(m.avg_duration_ms for m in self._query_metrics.values()) / total_queries
        )

        slowest_queries = sorted(
            self._query_metrics.values(), key=lambda m: m.avg_duration_ms, reverse=True
        )[:5]

        most_frequent_queries = sorted(
            self._query_metrics.values(), key=lambda m: m.execution_count, reverse=True
        )[:5]

        return {
            "total_unique_queries": total_queries,
            "average_duration_ms": avg_duration,
            "slowest_queries": [
                {
                    "query_hash": q.query_hash,
                    "avg_duration_ms": q.avg_duration_ms,
                    "execution_count": q.execution_count,
                }
                for q in slowest_queries
            ],
            "most_frequent_queries": [
                {
                    "query_hash": q.query_hash,
                    "execution_count": q.execution_count,
                    "avg_duration_ms": q.avg_duration_ms,
                }
                for q in most_frequent_queries
            ],
            "timestamp": datetime.utcnow().isoformat(),
        }


# TR: Global optimization service instance
_optimization_service: Optional[DatabaseOptimizationService] = None


def get_database_optimization_service() -> DatabaseOptimizationService:
    """TR: Database optimization service singleton"""
    global _optimization_service
    if _optimization_service is None:
        _optimization_service = DatabaseOptimizationService()
    return _optimization_service
