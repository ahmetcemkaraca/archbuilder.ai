from __future__ import annotations

from datetime import datetime
from typing import Any, Dict
from uuid import uuid4

from sqlalchemy import Column, String, JSON, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database.base import Base


class ValidationResult(Base):
    """TR: Validation sonuçları için veritabanı modeli"""
    
    __tablename__ = "validation_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    payload = Column(JSON, nullable=False, comment="TR: Validation edilen payload")
    building_type = Column(String(50), nullable=False, comment="TR: Bina tipi")
    results = Column(JSON, nullable=False, comment="TR: Validation sonuçları")
    overall_success = Column(Boolean, nullable=False, default=False, comment="TR: Genel başarı durumu")
    correlation_id = Column(String(100), nullable=True, comment="TR: Correlation ID")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """TR: Model'i dictionary'ye çevir"""
        return {
            "id": str(self.id),
            "payload": self.payload,
            "building_type": self.building_type,
            "results": self.results,
            "overall_success": self.overall_success,
            "correlation_id": self.correlation_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
