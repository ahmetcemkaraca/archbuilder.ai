from __future__ import annotations

import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

try:
    from alembic import command
    from alembic.config import Config
    from alembic.runtime.migration import MigrationContext
    from alembic.operations import Operations
    from sqlalchemy import create_engine, MetaData, text
    from sqlalchemy.engine import Engine
    ALEMBIC_AVAILABLE = True
except ImportError:
    ALEMBIC_AVAILABLE = False

logger = logging.getLogger(__name__)

class DatabaseMigrationService:
    """TR: Alembic migration management ve best practices"""
    
    def __init__(self, database_url: str, alembic_config_path: str = "alembic.ini"):
        if not ALEMBIC_AVAILABLE:
            raise ImportError("Alembic is not available")
        
        self.database_url = database_url
        self.alembic_config_path = alembic_config_path
        self._config: Optional[Config] = None
        self._engine: Optional[Engine] = None
    
    def _get_alembic_config(self) -> Config:
        """TR: Alembic configuration"""
        if self._config is None:
            self._config = Config(self.alembic_config_path)
            self._config.set_main_option("sqlalchemy.url", self.database_url)
        return self._config
    
    def _get_engine(self) -> Engine:
        """TR: Synchronous engine for migrations"""
        if self._engine is None:
            # TR: Async URL'i sync'e çevir
            sync_url = self.database_url.replace("+asyncpg", "")
            self._engine = create_engine(sync_url)
        return self._engine
    
    async def get_current_revision(self) -> Optional[str]:
        """TR: Mevcut database revision"""
        try:
            engine = self._get_engine()
            with engine.connect() as conn:
                context = MigrationContext.configure(conn)
                return context.get_current_revision()
        except Exception as e:
            logger.error(f"Failed to get current revision: {e}")
            return None
    
    async def get_migration_history(self) -> List[Dict[str, Any]]:
        """TR: Migration geçmişi"""
        try:
            config = self._get_alembic_config()
            
            # TR: Alembic history command equivalent
            script = command.ScriptDirectory.from_config(config)
            
            history = []
            for revision in script.walk_revisions():
                history.append({
                    "revision": revision.revision,
                    "down_revision": revision.down_revision,
                    "branch_labels": revision.branch_labels,
                    "depends_on": revision.depends_on,
                    "doc": revision.doc,
                    "is_head": revision.is_head,
                    "is_merge_point": revision.is_merge_point,
                    "is_branch_point": revision.is_branch_point
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Failed to get migration history: {e}")
            return []
    
    async def check_migration_status(self) -> Dict[str, Any]:
        """TR: Migration durumunu kontrol et"""
        try:
            config = self._get_alembic_config()
            engine = self._get_engine()
            
            with engine.connect() as conn:
                context = MigrationContext.configure(conn)
                current_rev = context.get_current_revision()
                
                script = command.ScriptDirectory.from_config(config)
                head_rev = script.get_current_head()
                
                # TR: Pending migrations
                pending_upgrades = []
                if current_rev != head_rev:
                    for rev in script.iterate_revisions(current_rev, head_rev):
                        if rev.revision != current_rev:
                            pending_upgrades.append({
                                "revision": rev.revision,
                                "message": rev.doc,
                                "down_revision": rev.down_revision
                            })
                
                return {
                    "current_revision": current_rev,
                    "head_revision": head_rev,
                    "is_up_to_date": current_rev == head_rev,
                    "pending_upgrades": pending_upgrades,
                    "pending_count": len(pending_upgrades)
                }
                
        except Exception as e:
            logger.error(f"Failed to check migration status: {e}")
            return {"error": str(e)}
    
    async def run_migrations(self, target_revision: str = "head") -> Dict[str, Any]:
        """TR: Migrationları çalıştır"""
        try:
            config = self._get_alembic_config()
            
            logger.info(f"Running migrations to {target_revision}")
            command.upgrade(config, target_revision)
            
            return {
                "status": "success",
                "target_revision": target_revision,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def rollback_migration(self, target_revision: str) -> Dict[str, Any]:
        """TR: Migration rollback"""
        try:
            config = self._get_alembic_config()
            
            logger.warning(f"Rolling back to {target_revision}")
            command.downgrade(config, target_revision)
            
            return {
                "status": "success",
                "target_revision": target_revision,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def create_migration(
        self, 
        message: str, 
        auto_generate: bool = True
    ) -> Dict[str, Any]:
        """TR: Yeni migration oluştur"""
        try:
            config = self._get_alembic_config()
            
            if auto_generate:
                # TR: Auto-generate migration
                command.revision(
                    config, 
                    message=message, 
                    autogenerate=True
                )
            else:
                # TR: Empty migration
                command.revision(config, message=message)
            
            return {
                "status": "success",
                "message": message,
                "auto_generate": auto_generate,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Migration creation failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def validate_database_schema(self) -> Dict[str, Any]:
        """TR: Database schema validation"""
        try:
            engine = self._get_engine()
            
            with engine.connect() as conn:
                # TR: Basic schema validation
                metadata = MetaData()
                metadata.reflect(bind=conn)
                
                tables = list(metadata.tables.keys())
                
                # TR: Check for required tables
                required_tables = ["users", "projects", "alembic_version"]
                missing_tables = [t for t in required_tables if t not in tables]
                
                # TR: Check alembic version table
                try:
                    result = conn.execute(text("SELECT version_num FROM alembic_version"))
                    version = result.scalar()
                except Exception:
                    version = None
                
                return {
                    "status": "success",
                    "tables_count": len(tables),
                    "tables": tables,
                    "missing_required_tables": missing_tables,
                    "alembic_version": version,
                    "is_valid": len(missing_tables) == 0 and version is not None,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Schema validation failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

class BackupService:
    """TR: Database backup ve recovery servisi"""
    
    def __init__(self, database_url: str, backup_dir: str = "backups"):
        self.database_url = database_url
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
    
    async def create_backup(self, backup_name: Optional[str] = None) -> Dict[str, Any]:
        """TR: Database backup oluştur"""
        try:
            if backup_name is None:
                backup_name = f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            # TR: PostgreSQL için pg_dump kullan
            if "postgresql" in self.database_url:
                return await self._create_postgresql_backup(backup_name)
            else:
                return {"status": "error", "error": "Backup not supported for this database type"}
                
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _create_postgresql_backup(self, backup_name: str) -> Dict[str, Any]:
        """TR: PostgreSQL backup"""
        import subprocess
        
        backup_file = self.backup_dir / f"{backup_name}.sql"
        
        # TR: Database URL'den connection bilgilerini çıkar
        # postgresql://user:pass@host:port/dbname
        url_parts = self.database_url.replace("postgresql://", "").replace("postgresql+asyncpg://", "")
        
        try:
            # TR: pg_dump komutu
            cmd = [
                "pg_dump",
                "--no-password",
                "--format=plain",
                "--file", str(backup_file),
                self.database_url.replace("+asyncpg", "")
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # TR: Backup file bilgileri
            file_size = backup_file.stat().st_size if backup_file.exists() else 0
            
            return {
                "status": "success",
                "backup_name": backup_name,
                "backup_file": str(backup_file),
                "file_size_bytes": file_size,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except subprocess.CalledProcessError as e:
            logger.error(f"pg_dump failed: {e.stderr}")
            return {
                "status": "error",
                "error": f"pg_dump failed: {e.stderr}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def list_backups(self) -> List[Dict[str, Any]]:
        """TR: Mevcut backupları listele"""
        backups = []
        
        for backup_file in self.backup_dir.glob("*.sql"):
            stat = backup_file.stat()
            
            backups.append({
                "name": backup_file.stem,
                "file": backup_file.name,
                "path": str(backup_file),
                "size_bytes": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
        
        # TR: En yeni backuplar önce
        backups.sort(key=lambda x: x["created_at"], reverse=True)
        
        return backups
    
    async def restore_backup(self, backup_name: str) -> Dict[str, Any]:
        """TR: Backup'tan restore et"""
        try:
            backup_file = self.backup_dir / f"{backup_name}.sql"
            
            if not backup_file.exists():
                return {
                    "status": "error",
                    "error": f"Backup file not found: {backup_name}",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            if "postgresql" in self.database_url:
                return await self._restore_postgresql_backup(backup_file)
            else:
                return {"status": "error", "error": "Restore not supported for this database type"}
                
        except Exception as e:
            logger.error(f"Backup restore failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _restore_postgresql_backup(self, backup_file: Path) -> Dict[str, Any]:
        """TR: PostgreSQL restore"""
        import subprocess
        
        try:
            # TR: psql komutu
            cmd = [
                "psql",
                "--no-password",
                "--file", str(backup_file),
                self.database_url.replace("+asyncpg", "")
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            return {
                "status": "success",
                "backup_file": str(backup_file),
                "restored_at": datetime.utcnow().isoformat()
            }
            
        except subprocess.CalledProcessError as e:
            logger.error(f"psql restore failed: {e.stderr}")
            return {
                "status": "error",
                "error": f"psql restore failed: {e.stderr}",
                "timestamp": datetime.utcnow().isoformat()
            }