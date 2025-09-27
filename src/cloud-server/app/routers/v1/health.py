"""
Health Check Endpoints for ArchBuilder.AI

Provides:
- Liveness probes
- Readiness probes
- System health monitoring
- Performance metrics
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
import structlog

from app.core.connection_pool import get_pool_manager
from app.core.cache import get_cache_service
from app.core.celery_app import get_task_queue_manager
from app.database.session import get_db_session

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


class HealthStatus(BaseModel):
    """Health status model"""

    status: str
    timestamp: datetime
    version: str
    uptime_seconds: float
    checks: Dict[str, Any]


class ComponentHealth(BaseModel):
    """Component health model"""

    name: str
    status: str
    response_time_ms: float
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class SystemHealth(BaseModel):
    """System health model"""

    overall_status: str
    timestamp: datetime
    version: str
    uptime_seconds: float
    components: List[ComponentHealth]
    performance_metrics: Dict[str, Any]


# Application start time for uptime calculation
_app_start_time = time.time()


@router.get("/liveness", response_model=HealthStatus)
async def liveness_check() -> HealthStatus:
    """
    Liveness probe endpoint

    Returns basic application health status.
    Used by Kubernetes liveness probes.
    """
    uptime = time.time() - _app_start_time

    return HealthStatus(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0",
        uptime_seconds=uptime,
        checks={"application": "running", "uptime": f"{uptime:.2f}s"},
    )


@router.get("/readiness", response_model=HealthStatus)
async def readiness_check() -> HealthStatus:
    """
    Readiness probe endpoint

    Checks if application is ready to serve traffic.
    Used by Kubernetes readiness probes.
    """
    uptime = time.time() - _app_start_time
    checks = {}
    overall_status = "healthy"

    # Check database connection
    try:
        db_session = get_db_session()
        db_session.execute("SELECT 1")
        db_session.close()
        checks["database"] = "connected"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"
        overall_status = "unhealthy"

    # Check Redis cache
    try:
        cache_service = await get_cache_service()
        await cache_service.cache_manager._redis_client.ping()
        checks["cache"] = "connected"
    except Exception as e:
        checks["cache"] = f"error: {str(e)}"
        overall_status = "unhealthy"

    # Check task queue
    try:
        task_manager = get_task_queue_manager()
        stats = await task_manager.get_queue_stats()
        checks["task_queue"] = "connected"
    except Exception as e:
        checks["task_queue"] = f"error: {str(e)}"
        overall_status = "unhealthy"

    return HealthStatus(
        status=overall_status,
        timestamp=datetime.utcnow(),
        version="1.0.0",
        uptime_seconds=uptime,
        checks=checks,
    )


@router.get("/detailed", response_model=SystemHealth)
async def detailed_health_check() -> SystemHealth:
    """
    Detailed health check endpoint

    Provides comprehensive system health information.
    """
    uptime = time.time() - _app_start_time
    components = []
    overall_status = "healthy"

    # Database health check
    db_start = time.time()
    try:
        db_session = get_db_session()
        result = db_session.execute("SELECT 1 as health_check")
        result.fetchone()
        db_session.close()

        components.append(
            ComponentHealth(
                name="database",
                status="healthy",
                response_time_ms=(time.time() - db_start) * 1000,
                details={"connection_pool": "active", "query_response": "success"},
            )
        )
    except Exception as e:
        components.append(
            ComponentHealth(
                name="database",
                status="unhealthy",
                response_time_ms=(time.time() - db_start) * 1000,
                error=str(e),
            )
        )
        overall_status = "degraded"

    # Redis cache health check
    cache_start = time.time()
    try:
        cache_service = await get_cache_service()
        await cache_service.cache_manager._redis_client.ping()
        stats = await cache_service.cache_manager.get_stats()

        components.append(
            ComponentHealth(
                name="cache",
                status="healthy",
                response_time_ms=(time.time() - cache_start) * 1000,
                details=stats,
            )
        )
    except Exception as e:
        components.append(
            ComponentHealth(
                name="cache",
                status="unhealthy",
                response_time_ms=(time.time() - cache_start) * 1000,
                error=str(e),
            )
        )
        overall_status = "degraded"

    # Task queue health check
    queue_start = time.time()
    try:
        task_manager = get_task_queue_manager()
        queue_stats = await task_manager.get_queue_stats()

        components.append(
            ComponentHealth(
                name="task_queue",
                status="healthy",
                response_time_ms=(time.time() - queue_start) * 1000,
                details=queue_stats,
            )
        )
    except Exception as e:
        components.append(
            ComponentHealth(
                name="task_queue",
                status="unhealthy",
                response_time_ms=(time.time() - queue_start) * 1000,
                error=str(e),
            )
        )
        overall_status = "degraded"

    # Connection pool health check
    pool_start = time.time()
    try:
        pool_manager = get_pool_manager()
        pool_metrics = pool_manager.get_pool_metrics()

        if pool_metrics:
            components.append(
                ComponentHealth(
                    name="connection_pool",
                    status="healthy",
                    response_time_ms=(time.time() - pool_start) * 1000,
                    details={
                        "pool_size": pool_metrics.pool_size,
                        "checked_out": pool_metrics.checked_out,
                        "checked_in": pool_metrics.checked_in,
                        "utilization_percentage": pool_metrics.utilization_percentage,
                    },
                )
            )
        else:
            components.append(
                ComponentHealth(
                    name="connection_pool",
                    status="unhealthy",
                    response_time_ms=(time.time() - pool_start) * 1000,
                    error="Pool metrics not available",
                )
            )
            overall_status = "degraded"
    except Exception as e:
        components.append(
            ComponentHealth(
                name="connection_pool",
                status="unhealthy",
                response_time_ms=(time.time() - pool_start) * 1000,
                error=str(e),
            )
        )
        overall_status = "degraded"

    # Calculate performance metrics
    performance_metrics = {
        "total_components": len(components),
        "healthy_components": len([c for c in components if c.status == "healthy"]),
        "unhealthy_components": len([c for c in components if c.status == "unhealthy"]),
        "avg_response_time_ms": (
            sum(c.response_time_ms for c in components) / len(components)
            if components
            else 0
        ),
        "max_response_time_ms": (
            max(c.response_time_ms for c in components) if components else 0
        ),
    }

    return SystemHealth(
        overall_status=overall_status,
        timestamp=datetime.utcnow(),
        version="1.0.0",
        uptime_seconds=uptime,
        components=components,
        performance_metrics=performance_metrics,
    )


@router.get("/metrics")
async def metrics_endpoint() -> Dict[str, Any]:
    """
    Metrics endpoint for Prometheus scraping

    Returns system metrics in Prometheus format.
    """
    metrics = {}

    try:
        # Database metrics
        pool_manager = get_pool_manager()
        pool_metrics = pool_manager.get_pool_metrics()

        if pool_metrics:
            metrics.update(
                {
                    "database_connection_pool_size": pool_metrics.pool_size,
                    "database_connections_checked_out": pool_metrics.checked_out,
                    "database_connections_checked_in": pool_metrics.checked_in,
                    "database_connection_utilization_percentage": pool_metrics.utilization_percentage,
                    "database_overflow_connections": pool_metrics.overflow,
                }
            )

        # Cache metrics
        cache_service = await get_cache_service()
        cache_stats = await cache_service.cache_manager.get_stats()

        if cache_stats:
            metrics.update(
                {
                    "redis_connected_clients": cache_stats.get("connected_clients", 0),
                    "redis_used_memory_bytes": cache_stats.get("used_memory", 0),
                    "redis_keyspace_hits": cache_stats.get("keyspace_hits", 0),
                    "redis_keyspace_misses": cache_stats.get("keyspace_misses", 0),
                    "redis_total_commands": cache_stats.get(
                        "total_commands_processed", 0
                    ),
                    "redis_ops_per_sec": cache_stats.get(
                        "instantaneous_ops_per_sec", 0
                    ),
                }
            )

        # Task queue metrics
        task_manager = get_task_queue_manager()
        queue_stats = await task_manager.get_queue_stats()

        if queue_stats:
            metrics.update(
                {
                    "celery_total_active_tasks": queue_stats.get("total_active", 0),
                    "celery_total_scheduled_tasks": queue_stats.get(
                        "total_scheduled", 0
                    ),
                    "celery_total_reserved_tasks": queue_stats.get("total_reserved", 0),
                }
            )

            # Per-queue metrics
            for queue_name, queue_data in queue_stats.get("queues", {}).items():
                metrics[f"celery_queue_{queue_name}_active"] = queue_data.get(
                    "active", 0
                )
                metrics[f"celery_queue_{queue_name}_scheduled"] = queue_data.get(
                    "scheduled", 0
                )
                metrics[f"celery_queue_{queue_name}_reserved"] = queue_data.get(
                    "reserved", 0
                )

        # Application metrics
        uptime = time.time() - _app_start_time
        metrics.update(
            {
                "application_uptime_seconds": uptime,
                "application_start_time": _app_start_time,
            }
        )

    except Exception as e:
        logger.error("Failed to collect metrics", error=str(e))
        metrics["metrics_collection_error"] = 1

    return metrics


@router.get("/status")
async def status_endpoint() -> Dict[str, Any]:
    """
    Status endpoint for monitoring dashboards

    Returns current system status and key metrics.
    """
    try:
        # Get basic health status
        health_status = await detailed_health_check()

        # Get additional metrics
        cache_service = await get_cache_service()
        cache_stats = await cache_service.cache_manager.get_stats()

        task_manager = get_task_queue_manager()
        queue_stats = await task_manager.get_queue_stats()

        pool_manager = get_pool_manager()
        pool_metrics = pool_manager.get_pool_metrics()

        return {
            "status": health_status.overall_status,
            "timestamp": health_status.timestamp.isoformat(),
            "uptime_seconds": health_status.uptime_seconds,
            "components": {
                component.name: {
                    "status": component.status,
                    "response_time_ms": component.response_time_ms,
                    "error": component.error,
                }
                for component in health_status.components
            },
            "metrics": {
                "cache": cache_stats,
                "task_queue": queue_stats,
                "connection_pool": pool_metrics.dict() if pool_metrics else None,
            },
            "performance": health_status.performance_metrics,
        }

    except Exception as e:
        logger.error("Failed to get status", error=str(e))
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }
