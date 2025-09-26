from __future__ import annotations

from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

try:
    from app.services.database_monitoring_service import get_database_monitoring_service
    from app.services.database_migration_service import DatabaseMigrationService, BackupService
    from app.database.session import get_connection_stats, check_connection_health
    from app.core.config import settings
    SERVICES_AVAILABLE = True
except ImportError:
    SERVICES_AVAILABLE = False

router = APIRouter(prefix="/v1/database", tags=["database-admin"])

class DatabaseHealthResponse(BaseModel):
    """TR: Database sağlık durumu response"""
    status: str
    is_healthy: bool
    response_time_ms: float
    connection_stats: Dict[str, Any]
    timestamp: str

class MigrationStatusResponse(BaseModel):
    """TR: Migration durumu response"""
    current_revision: Optional[str]
    head_revision: Optional[str]
    is_up_to_date: bool
    pending_upgrades: List[Dict[str, Any]]
    pending_count: int

class BackupResponse(BaseModel):
    """TR: Backup işlemi response"""
    status: str
    backup_name: Optional[str] = None
    file_size_bytes: Optional[int] = None
    error: Optional[str] = None
    timestamp: str

# TR: Admin authentication dependency
async def require_admin():
    """TR: Admin yetkisi gerekli - TODO: gerçek authentication"""
    # TODO: Implement real admin authentication
    return True

@router.get("/health", response_model=DatabaseHealthResponse)
async def get_database_health():
    """TR: Database sağlık durumu"""
    if not SERVICES_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database services not available")
    
    start_time = datetime.utcnow()
    
    # TR: Connection health check
    is_healthy = await check_connection_health()
    
    # TR: Response time
    response_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
    
    # TR: Connection stats
    connection_stats = await get_connection_stats()
    
    return DatabaseHealthResponse(
        status="healthy" if is_healthy else "unhealthy",
        is_healthy=is_healthy,
        response_time_ms=response_time_ms,
        connection_stats=connection_stats,
        timestamp=datetime.utcnow().isoformat()
    )

@router.get("/monitoring/summary")
async def get_monitoring_summary(_: bool = Depends(require_admin)):
    """TR: Database monitoring özeti"""
    if not SERVICES_AVAILABLE:
        raise HTTPException(status_code=503, detail="Monitoring service not available")
    
    monitoring_service = get_database_monitoring_service()
    summary = await monitoring_service.get_health_summary()
    
    return summary

@router.get("/monitoring/slow-queries")
async def get_slow_queries(
    limit: int = Query(50, ge=1, le=200),
    _: bool = Depends(require_admin)
):
    """TR: Yavaş sorguları listele"""
    if not SERVICES_AVAILABLE:
        raise HTTPException(status_code=503, detail="Monitoring service not available")
    
    monitoring_service = get_database_monitoring_service()
    slow_queries = await monitoring_service.get_slow_queries(limit=limit)
    
    return {
        "slow_queries": slow_queries,
        "count": len(slow_queries),
        "limit": limit,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.post("/monitoring/start")
async def start_monitoring(
    interval_seconds: int = Query(60, ge=30, le=3600),
    _: bool = Depends(require_admin)
):
    """TR: Database monitoring başlat"""
    if not SERVICES_AVAILABLE:
        raise HTTPException(status_code=503, detail="Monitoring service not available")
    
    monitoring_service = get_database_monitoring_service()
    await monitoring_service.start_monitoring(interval_seconds)
    
    return {
        "status": "started",
        "interval_seconds": interval_seconds,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.post("/monitoring/stop")
async def stop_monitoring(_: bool = Depends(require_admin)):
    """TR: Database monitoring durdur"""
    if not SERVICES_AVAILABLE:
        raise HTTPException(status_code=503, detail="Monitoring service not available")
    
    monitoring_service = get_database_monitoring_service()
    await monitoring_service.stop_monitoring()
    
    return {
        "status": "stopped",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/monitoring/diagnostics")
async def run_database_diagnostics(_: bool = Depends(require_admin)):
    """TR: Kapsamlı database diagnostics"""
    if not SERVICES_AVAILABLE:
        raise HTTPException(status_code=503, detail="Monitoring service not available")
    
    monitoring_service = get_database_monitoring_service()
    diagnostics = await monitoring_service.run_database_diagnostics()
    
    return diagnostics

@router.get("/migrations/status", response_model=MigrationStatusResponse)
async def get_migration_status(_: bool = Depends(require_admin)):
    """TR: Migration durumu"""
    if not SERVICES_AVAILABLE:
        raise HTTPException(status_code=503, detail="Migration service not available")
    
    database_url = settings.database_url or "sqlite+aiosqlite:///./archbuilder.db"
    migration_service = DatabaseMigrationService(database_url)
    
    status = await migration_service.check_migration_status()
    
    if "error" in status:
        raise HTTPException(status_code=500, detail=status["error"])
    
    return MigrationStatusResponse(**status)

@router.post("/migrations/run")
async def run_migrations(
    target_revision: str = "head",
    _: bool = Depends(require_admin)
):
    """TR: Migrationları çalıştır"""
    if not SERVICES_AVAILABLE:
        raise HTTPException(status_code=503, detail="Migration service not available")
    
    database_url = settings.database_url or "sqlite+aiosqlite:///./archbuilder.db"
    migration_service = DatabaseMigrationService(database_url)
    
    result = await migration_service.run_migrations(target_revision)
    
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result

@router.post("/migrations/rollback")
async def rollback_migration(
    target_revision: str,
    _: bool = Depends(require_admin)
):
    """TR: Migration rollback"""
    if not SERVICES_AVAILABLE:
        raise HTTPException(status_code=503, detail="Migration service not available")
    
    database_url = settings.database_url or "sqlite+aiosqlite:///./archbuilder.db"
    migration_service = DatabaseMigrationService(database_url)
    
    result = await migration_service.rollback_migration(target_revision)
    
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result

@router.get("/migrations/history")
async def get_migration_history(_: bool = Depends(require_admin)):
    """TR: Migration geçmişi"""
    if not SERVICES_AVAILABLE:
        raise HTTPException(status_code=503, detail="Migration service not available")
    
    database_url = settings.database_url or "sqlite+aiosqlite:///./archbuilder.db"
    migration_service = DatabaseMigrationService(database_url)
    
    history = await migration_service.get_migration_history()
    
    return {
        "history": history,
        "count": len(history),
        "timestamp": datetime.utcnow().isoformat()
    }

@router.post("/backup/create", response_model=BackupResponse)
async def create_backup(
    backup_name: Optional[str] = None,
    _: bool = Depends(require_admin)
):
    """TR: Database backup oluştur"""
    if not SERVICES_AVAILABLE:
        raise HTTPException(status_code=503, detail="Backup service not available")
    
    database_url = settings.database_url or "sqlite+aiosqlite:///./archbuilder.db"
    backup_service = BackupService(database_url)
    
    result = await backup_service.create_backup(backup_name)
    
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    
    return BackupResponse(**result)

@router.get("/backup/list")
async def list_backups(_: bool = Depends(require_admin)):
    """TR: Backup listesi"""
    if not SERVICES_AVAILABLE:
        raise HTTPException(status_code=503, detail="Backup service not available")
    
    database_url = settings.database_url or "sqlite+aiosqlite:///./archbuilder.db"
    backup_service = BackupService(database_url)
    
    backups = await backup_service.list_backups()
    
    return {
        "backups": backups,
        "count": len(backups),
        "timestamp": datetime.utcnow().isoformat()
    }

@router.post("/backup/restore")
async def restore_backup(
    backup_name: str,
    _: bool = Depends(require_admin)
):
    """TR: Backup'tan restore et"""
    if not SERVICES_AVAILABLE:
        raise HTTPException(status_code=503, detail="Backup service not available")
    
    database_url = settings.database_url or "sqlite+aiosqlite:///./archbuilder.db"
    backup_service = BackupService(database_url)
    
    result = await backup_service.restore_backup(backup_name)
    
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result

@router.get("/schema/validate")
async def validate_database_schema(_: bool = Depends(require_admin)):
    """TR: Database schema validation"""
    if not SERVICES_AVAILABLE:
        raise HTTPException(status_code=503, detail="Migration service not available")
    
    database_url = settings.database_url or "sqlite+aiosqlite:///./archbuilder.db"
    migration_service = DatabaseMigrationService(database_url)
    
    validation = await migration_service.validate_database_schema()
    
    if validation["status"] == "error":
        raise HTTPException(status_code=500, detail=validation["error"])
    
    return validation