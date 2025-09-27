"""
Query Profiler and Database Optimization for ArchBuilder.AI

Provides:
- Query performance monitoring
- Database index recommendations
- Slow query detection
- Connection pool optimization
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

import structlog
from sqlalchemy import text, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import QueuePool

logger = structlog.get_logger(__name__)


class QueryType(str, Enum):
    """Query type classification"""

    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    DDL = "DDL"
    UNKNOWN = "UNKNOWN"


@dataclass
class QueryProfile:
    """Query performance profile"""

    query_id: str
    query_text: str
    query_type: QueryType
    execution_time_ms: float
    rows_affected: int
    connection_id: str
    timestamp: datetime
    parameters: Optional[Dict[str, Any]] = None
    stack_trace: Optional[List[str]] = None
    is_slow: bool = False
    recommended_indexes: List[str] = None


@dataclass
class DatabaseMetrics:
    """Database performance metrics"""

    total_queries: int
    slow_queries: int
    avg_execution_time_ms: float
    max_execution_time_ms: float
    connection_pool_size: int
    active_connections: int
    idle_connections: int
    cache_hit_ratio: float
    index_usage_stats: Dict[str, int]


class QueryProfiler:
    """Advanced query profiler for ArchBuilder.AI"""

    def __init__(self, slow_query_threshold_ms: float = 1000.0):
        self.slow_query_threshold_ms = slow_query_threshold_ms
        self.query_profiles: List[QueryProfile] = []
        self.query_stats: Dict[str, Dict[str, Any]] = {}
        self.index_recommendations: Dict[str, List[str]] = {}

    def start_profiling(self, engine: Engine) -> None:
        """Start query profiling on database engine"""

        @event.listens_for(engine, "before_cursor_execute")
        def receive_before_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            context._query_start_time = time.time()
            context._query_id = f"q_{int(time.time() * 1000000)}"

        @event.listens_for(engine, "after_cursor_execute")
        def receive_after_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            if hasattr(context, "_query_start_time"):
                execution_time = (time.time() - context._query_start_time) * 1000

                # Classify query type
                query_type = self._classify_query(statement)

                # Create query profile
                profile = QueryProfile(
                    query_id=context._query_id,
                    query_text=statement,
                    query_type=query_type,
                    execution_time_ms=execution_time,
                    rows_affected=cursor.rowcount if hasattr(cursor, "rowcount") else 0,
                    connection_id=str(id(conn)),
                    timestamp=datetime.utcnow(),
                    parameters=parameters,
                    is_slow=execution_time > self.slow_query_threshold_ms,
                )

                # Analyze for index recommendations
                if profile.is_slow and profile.query_type == QueryType.SELECT:
                    profile.recommended_indexes = self._analyze_index_needs(statement)

                self.query_profiles.append(profile)

                # Update statistics
                self._update_query_stats(profile)

                # Log slow queries
                if profile.is_slow:
                    logger.warning(
                        "Slow query detected",
                        query_id=profile.query_id,
                        execution_time_ms=execution_time,
                        query_type=query_type.value,
                        recommended_indexes=profile.recommended_indexes,
                    )

    def _classify_query(self, query_text: str) -> QueryType:
        """Classify query type"""
        query_upper = query_text.upper().strip()

        if query_upper.startswith("SELECT"):
            return QueryType.SELECT
        elif query_upper.startswith("INSERT"):
            return QueryType.INSERT
        elif query_upper.startswith("UPDATE"):
            return QueryType.UPDATE
        elif query_upper.startswith("DELETE"):
            return QueryType.DELETE
        elif any(
            query_upper.startswith(ddl)
            for ddl in ["CREATE", "ALTER", "DROP", "TRUNCATE"]
        ):
            return QueryType.DDL
        else:
            return QueryType.UNKNOWN

    def _analyze_index_needs(self, query_text: str) -> List[str]:
        """Analyze query for index recommendations"""
        recommendations = []
        query_upper = query_text.upper()

        # Look for WHERE clauses with potential index candidates
        if "WHERE" in query_upper:
            # Extract column names from WHERE clause
            where_start = query_upper.find("WHERE")
            where_clause = query_text[where_start:]

            # Common patterns that benefit from indexes
            patterns = [
                "user_id =",
                "correlation_id =",
                "created_at >",
                "created_at <",
                "status =",
                "region =",
                "building_type =",
            ]

            for pattern in patterns:
                if pattern in where_clause:
                    column = pattern.split(" =")[0]
                    recommendations.append(
                        f"CREATE INDEX idx_{column} ON table_name ({column})"
                    )

        # Look for JOIN conditions
        if "JOIN" in query_upper:
            recommendations.append("Consider foreign key indexes for JOIN columns")

        # Look for ORDER BY clauses
        if "ORDER BY" in query_upper:
            recommendations.append("Consider composite indexes for ORDER BY columns")

        return recommendations

    def _update_query_stats(self, profile: QueryProfile) -> None:
        """Update query statistics"""
        query_key = f"{profile.query_type.value}_{hash(profile.query_text) % 10000}"

        if query_key not in self.query_stats:
            self.query_stats[query_key] = {
                "count": 0,
                "total_time_ms": 0.0,
                "max_time_ms": 0.0,
                "slow_count": 0,
                "query_text": (
                    profile.query_text[:100] + "..."
                    if len(profile.query_text) > 100
                    else profile.query_text
                ),
            }

        stats = self.query_stats[query_key]
        stats["count"] += 1
        stats["total_time_ms"] += profile.execution_time_ms
        stats["max_time_ms"] = max(stats["max_time_ms"], profile.execution_time_ms)

        if profile.is_slow:
            stats["slow_count"] += 1

    def get_slow_queries(self, limit: int = 50) -> List[QueryProfile]:
        """Get slow queries sorted by execution time"""
        slow_queries = [q for q in self.query_profiles if q.is_slow]
        return sorted(slow_queries, key=lambda x: x.execution_time_ms, reverse=True)[
            :limit
        ]

    def get_query_statistics(self) -> Dict[str, Any]:
        """Get comprehensive query statistics"""
        if not self.query_profiles:
            return {}

        total_queries = len(self.query_profiles)
        slow_queries = len([q for q in self.query_profiles if q.is_slow])
        avg_time = sum(q.execution_time_ms for q in self.query_profiles) / total_queries
        max_time = max(q.execution_time_ms for q in self.query_profiles)

        # Group by query type
        type_stats = {}
        for profile in self.query_profiles:
            query_type = profile.query_type.value
            if query_type not in type_stats:
                type_stats[query_type] = {
                    "count": 0,
                    "avg_time_ms": 0.0,
                    "max_time_ms": 0.0,
                }

            type_stats[query_type]["count"] += 1
            type_stats[query_type]["avg_time_ms"] += profile.execution_time_ms
            type_stats[query_type]["max_time_ms"] = max(
                type_stats[query_type]["max_time_ms"], profile.execution_time_ms
            )

        # Calculate averages
        for stats in type_stats.values():
            stats["avg_time_ms"] /= stats["count"]

        return {
            "total_queries": total_queries,
            "slow_queries": slow_queries,
            "slow_query_percentage": (
                (slow_queries / total_queries) * 100 if total_queries > 0 else 0
            ),
            "avg_execution_time_ms": avg_time,
            "max_execution_time_ms": max_time,
            "query_type_stats": type_stats,
            "top_slow_queries": [
                {
                    "query_id": q.query_id,
                    "execution_time_ms": q.execution_time_ms,
                    "query_type": q.query_type.value,
                    "recommended_indexes": q.recommended_indexes or [],
                }
                for q in self.get_slow_queries(10)
            ],
        }

    def get_index_recommendations(self) -> Dict[str, List[str]]:
        """Get index recommendations based on query analysis"""
        recommendations = {}

        for profile in self.query_profiles:
            if profile.recommended_indexes:
                query_key = (
                    f"{profile.query_type.value}_{hash(profile.query_text) % 10000}"
                )
                if query_key not in recommendations:
                    recommendations[query_key] = []

                recommendations[query_key].extend(profile.recommended_indexes)

        # Deduplicate recommendations
        for key in recommendations:
            recommendations[key] = list(set(recommendations[key]))

        return recommendations

    def clear_old_profiles(self, hours: int = 24) -> int:
        """Clear old query profiles"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        initial_count = len(self.query_profiles)

        self.query_profiles = [
            p for p in self.query_profiles if p.timestamp > cutoff_time
        ]

        cleared_count = initial_count - len(self.query_profiles)
        logger.info(
            "Cleared old query profiles", cleared_count=cleared_count, hours=hours
        )
        return cleared_count


class DatabaseOptimizer:
    """Database optimization utilities"""

    def __init__(self, engine: Engine):
        self.engine = engine
        self.profiler = QueryProfiler()

    async def analyze_database_performance(self) -> DatabaseMetrics:
        """Analyze overall database performance"""
        try:
            with self.engine.connect() as conn:
                # Get connection pool stats
                pool = self.engine.pool
                if isinstance(pool, QueuePool):
                    pool_stats = {
                        "size": pool.size(),
                        "checked_in": pool.checkedin(),
                        "checked_out": pool.checkedout(),
                        "overflow": pool.overflow(),
                        "invalid": pool.invalid(),
                    }
                else:
                    pool_stats = {}

                # Get database statistics
                stats_query = text(
                    """
                    SELECT 
                        schemaname,
                        tablename,
                        attname,
                        n_distinct,
                        correlation
                    FROM pg_stats 
                    WHERE schemaname = 'public'
                    ORDER BY n_distinct DESC
                    LIMIT 20
                """
                )

                result = conn.execute(stats_query)
                column_stats = [dict(row._mapping) for row in result]

                # Get index usage statistics
                index_query = text(
                    """
                    SELECT 
                        schemaname,
                        tablename,
                        indexname,
                        idx_scan,
                        idx_tup_read,
                        idx_tup_fetch
                    FROM pg_stat_user_indexes
                    ORDER BY idx_scan DESC
                    LIMIT 20
                """
                )

                result = conn.execute(index_query)
                index_stats = [dict(row._mapping) for row in result]

                return DatabaseMetrics(
                    total_queries=len(self.profiler.query_profiles),
                    slow_queries=len(
                        [q for q in self.profiler.query_profiles if q.is_slow]
                    ),
                    avg_execution_time_ms=sum(
                        q.execution_time_ms for q in self.profiler.query_profiles
                    )
                    / max(len(self.profiler.query_profiles), 1),
                    max_execution_time_ms=max(
                        (q.execution_time_ms for q in self.profiler.query_profiles),
                        default=0.0,
                    ),
                    connection_pool_size=pool_stats.get("size", 0),
                    active_connections=pool_stats.get("checked_out", 0),
                    idle_connections=pool_stats.get("checked_in", 0),
                    cache_hit_ratio=0.0,  # Would need additional queries to calculate
                    index_usage_stats={
                        row["indexname"]: row["idx_scan"] for row in index_stats
                    },
                )

        except Exception as e:
            logger.error("Failed to analyze database performance", error=str(e))
            return DatabaseMetrics(
                total_queries=0,
                slow_queries=0,
                avg_execution_time_ms=0.0,
                max_execution_time_ms=0.0,
                connection_pool_size=0,
                active_connections=0,
                idle_connections=0,
                cache_hit_ratio=0.0,
                index_usage_stats={},
            )

    async def get_missing_indexes(self) -> List[Dict[str, Any]]:
        """Get recommendations for missing indexes"""
        try:
            with self.engine.connect() as conn:
                # Query to find missing indexes
                missing_indexes_query = text(
                    """
                    SELECT 
                        schemaname,
                        tablename,
                        attname,
                        n_distinct,
                        correlation,
                        CASE 
                            WHEN n_distinct > 100 AND correlation < 0.1 THEN 'High cardinality, low correlation - good candidate for index'
                            WHEN n_distinct > 10 AND correlation < 0.5 THEN 'Medium cardinality, medium correlation - consider index'
                            ELSE 'Low cardinality or high correlation - index may not be beneficial'
                        END as recommendation
                    FROM pg_stats 
                    WHERE schemaname = 'public'
                    AND n_distinct > 10
                    ORDER BY n_distinct DESC, correlation ASC
                """
                )

                result = conn.execute(missing_indexes_query)
                return [dict(row._mapping) for row in result]

        except Exception as e:
            logger.error("Failed to get missing indexes", error=str(e))
            return []

    async def optimize_connection_pool(self) -> Dict[str, Any]:
        """Get connection pool optimization recommendations"""
        pool = self.engine.pool

        if not isinstance(pool, QueuePool):
            return {"message": "Pool is not QueuePool, no optimization available"}

        current_size = pool.size()
        checked_out = pool.checkedout()
        checked_in = pool.checkedin()
        overflow = pool.overflow()

        recommendations = []

        # Analyze pool utilization
        utilization = checked_out / current_size if current_size > 0 else 0

        if utilization > 0.8:
            recommendations.append(
                "High pool utilization - consider increasing pool size"
            )
        elif utilization < 0.2:
            recommendations.append(
                "Low pool utilization - consider decreasing pool size"
            )

        if overflow > 0:
            recommendations.append(
                "Pool overflow detected - increase pool size or timeout"
            )

        return {
            "current_size": current_size,
            "checked_out": checked_out,
            "checked_in": checked_in,
            "overflow": overflow,
            "utilization": utilization,
            "recommendations": recommendations,
        }


@asynccontextmanager
async def profile_query(query_name: str):
    """Context manager for profiling individual queries"""
    start_time = time.time()
    query_id = f"profiled_{int(time.time() * 1000000)}"

    try:
        logger.debug(
            "Query profiling started", query_name=query_name, query_id=query_id
        )
        yield query_id
    finally:
        execution_time = (time.time() - start_time) * 1000
        logger.info(
            "Query profiling completed",
            query_name=query_name,
            query_id=query_id,
            execution_time_ms=execution_time,
        )
