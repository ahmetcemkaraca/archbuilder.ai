from __future__ import annotations

from datetime import datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Usage(Base):
    __tablename__ = "usage"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    usage_type: Mapped[str] = mapped_column(String(50), index=True)
    units: Mapped[int] = mapped_column(Integer, default=0)
    date: Mapped[datetime] = mapped_column(Date, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# Usage Model
# Bu dosya kullanım veritabanı modelini içerir
