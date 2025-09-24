from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from app.schemas.ai import AICommandCreateRequest, AICommandResponse
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional
from app.core.ai.validation.schema_validator import validate_schema
from app.core.ai.validation.geometry_validator import validate_geometry
from app.core.ai.validation.building_code_validator import validate_building_code
from app.services.ai_service import AIService
from app.database.session import AsyncSession, get_db
from app.security.authentication import require_api_key


router = APIRouter(prefix="/v1/ai", tags=["ai"], dependencies=[Depends(require_api_key)])
def get_service() -> AIService:
    return AIService()


@router.post("/commands", response_model=AICommandResponse)
async def create_command(body: AICommandCreateRequest, db: AsyncSession = Depends(get_db), svc: AIService = Depends(get_service)):
    res = await svc.create_command(db, body.command, body.input, body.user_id, body.project_id)
    return AICommandResponse(success=True, data=res)


@router.get("/commands/{command_id}", response_model=AICommandResponse)
async def get_command(command_id: str, db: AsyncSession = Depends(get_db), svc: AIService = Depends(get_service)):
    res = await svc.get_command(db, command_id)
    if not res:
        raise HTTPException(status_code=404, detail="command not found")
    return AICommandResponse(success=True, data=res)


class ValidationRequest(BaseModel):
    payload: Dict[str, Any] = Field(default_factory=dict)
    building_type: Optional[str] = Field(default="residential")


class ValidationResponse(BaseModel):
    success: bool
    data: Dict[str, Any]


@router.post("/validate", response_model=ValidationResponse)
async def validate_output(body: ValidationRequest):
    schema_errors = validate_schema(body.payload)
    geometry_errors = validate_geometry(body.payload)
    code_errors = validate_building_code(body.payload, building_type=body.building_type or "residential")
    errors = schema_errors + geometry_errors + code_errors
    status = "valid" if not errors else ("requires_review" if len(errors) <= 3 else "rejected")
    return ValidationResponse(success=True, data={"status": status, "errors": errors})


