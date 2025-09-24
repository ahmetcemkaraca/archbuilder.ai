from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from sqlalchemy import Column, String, JSON, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database.base import Base


class ReviewItem(Base):
    """TR: Review items için veritabanı modeli"""
    
    __tablename__ = "review_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    item_type = Column(String(50), nullable=False, comment="TR: Review item tipi")
    item_data = Column(JSON, nullable=False, comment="TR: Review edilecek veri")
    status = Column(String(20), nullable=False, default="pending", comment="TR: Review durumu")
    priority = Column(String(20), nullable=False, default="medium", comment="TR: Review önceliği")
    
    # TR: Atama bilgileri
    assigned_to = Column(String(100), nullable=True, comment="TR: Atanan reviewer")
    assigned_at = Column(DateTime(timezone=True), nullable=True, comment="TR: Atama tarihi")
    assigned_by = Column(String(100), nullable=True, comment="TR: Atayan kişi")
    
    # TR: Review bilgileri
    reviewed_by = Column(String(100), nullable=True, comment="TR: Review yapan kişi")
    reviewed_at = Column(DateTime(timezone=True), nullable=True, comment="TR: Review tarihi")
    comments = Column(Text, nullable=True, comment="TR: Review yorumları")
    feedback_data = Column(JSON, nullable=True, comment="TR: Feedback verileri")
    
    # TR: Proje ve oluşturucu bilgileri
    project_id = Column(String(100), nullable=True, comment="TR: Proje ID")
    created_by = Column(String(100), nullable=True, comment="TR: Oluşturan kişi")
    
    # TR: Timestamp'ler
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """TR: Model'i dictionary'ye çevir"""
        return {
            "id": str(self.id),
            "item_type": self.item_type,
            "item_data": self.item_data,
            "status": self.status,
            "priority": self.priority,
            "assigned_to": self.assigned_to,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "assigned_by": self.assigned_by,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "comments": self.comments,
            "feedback_data": self.feedback_data,
            "project_id": self.project_id,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
