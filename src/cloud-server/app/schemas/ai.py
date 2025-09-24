from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class AICommandCreateRequest(BaseModel):
    command: str = Field(..., min_length=1, max_length=100)
    input: Dict[str, Any] = Field(default_factory=dict)
    user_id: Optional[str] = Field(default=None, min_length=1, max_length=36)
    project_id: Optional[str] = Field(default=None, min_length=1, max_length=36)


class AICommandItem(BaseModel):
    id: str
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    command: str
    input: Dict[str, Any]
    output: Optional[Dict[str, Any]] = None
    created_at: datetime


class AICommandResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    error: Optional[Dict[str, Any]] = None


