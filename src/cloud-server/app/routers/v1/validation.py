from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from app.database.session import get_db
from app.services.validation_service import ValidationService
from app.database.models.validation_result import ValidationResult
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/validation", tags=["validation"])


@router.post("/validate")
async def validate_comprehensive(
    request: Request,
    payload: Dict[str, Any],
    building_type: str = "residential",
    validation_types: str = "schema,geometric,code",
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """TR: Kapsamlı validation endpoint'i - P20-T1, P20-T2, P20-T3"""
    try:
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid4()))
        
        # TR: Validation types'ı parse et
        types_list = [t.strip() for t in validation_types.split(",")]
        
        validation_service = ValidationService()
        
        result = await validation_service.validate_comprehensive(
            db=db,
            payload=payload,
            building_type=building_type,
            validation_types=types_list
        )
        
        response = JSONResponse(
            content=result,
            headers={
                "X-Correlation-ID": correlation_id,
                "X-Request-ID": str(uuid4())
            }
        )
        
        return response
        
    except Exception as e:
        logger.error(f"TR: Validation endpoint hatası: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"TR: Validation hatası: {str(e)}"
        )


@router.post("/validate/schema")
async def validate_schema(
    request: Request,
    data: Dict[str, Any],
    schema_name: str,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """TR: JSON schema validation endpoint'i - P20-T1"""
    try:
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid4()))
        
        validation_service = ValidationService()
        
        result = await validation_service.validate_json_schema(data, schema_name)
        
        response = JSONResponse(
            content=result,
            headers={
                "X-Correlation-ID": correlation_id,
                "X-Request-ID": str(uuid4())
            }
        )
        
        return response
        
    except Exception as e:
        logger.error(f"TR: Schema validation endpoint hatası: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"TR: Schema validation hatası: {str(e)}"
        )


@router.post("/validate/geometric")
async def validate_geometric(
    request: Request,
    payload: Dict[str, Any],
    building_type: str = "residential",
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """TR: Geometric validation endpoint'i - P20-T2"""
    try:
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid4()))
        
        validation_service = ValidationService()
        
        result = await validation_service.validate_geometric(payload, building_type)
        
        response = JSONResponse(
            content=result,
            headers={
                "X-Correlation-ID": correlation_id,
                "X-Request-ID": str(uuid4())
            }
        )
        
        return response
        
    except Exception as e:
        logger.error(f"TR: Geometric validation endpoint hatası: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"TR: Geometric validation hatası: {str(e)}"
        )


@router.post("/validate/code")
async def validate_code(
    request: Request,
    payload: Dict[str, Any],
    building_type: str = "residential",
    region: str = "TR",
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """TR: Building code validation endpoint'i - P20-T2"""
    try:
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid4()))
        
        validation_service = ValidationService()
        
        result = await validation_service.validate_code(payload, building_type)
        
        response = JSONResponse(
            content=result,
            headers={
                "X-Correlation-ID": correlation_id,
                "X-Request-ID": str(uuid4())
            }
        )
        
        return response
        
    except Exception as e:
        logger.error(f"TR: Code validation endpoint hatası: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"TR: Code validation hatası: {str(e)}"
        )


@router.post("/analyze/project")
async def analyze_project(
    request: Request,
    project_id: str,
    analysis_type: str = "both",
    options: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """TR: Proje analizi endpoint'i - P18-T1, P18-T2, P18-T3"""
    try:
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid4()))
        
        validation_service = ValidationService()
        
        result = await validation_service.analyze_project(
            db=db,
            project_id=project_id,
            analysis_type=analysis_type,
            options=options or {}
        )
        
        response = JSONResponse(
            content=result,
            headers={
                "X-Correlation-ID": correlation_id,
                "X-Request-ID": str(uuid4())
            }
        )
        
        return response
        
    except Exception as e:
        logger.error(f"TR: Proje analizi endpoint hatası: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"TR: Proje analizi hatası: {str(e)}"
        )


@router.get("/results/{validation_id}")
async def get_validation_result(
    request: Request,
    validation_id: str,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """TR: Validation sonucu getir"""
    try:
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid4()))
        
        result = await db.get(ValidationResult, validation_id)
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail="TR: Validation sonucu bulunamadı"
            )
        
        response_data = result.to_dict()
        
        response = JSONResponse(
            content={
                "success": True,
                "data": response_data
            },
            headers={
                "X-Correlation-ID": correlation_id,
                "X-Request-ID": str(uuid4())
            }
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TR: Validation sonucu getirme hatası: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"TR: Validation sonucu getirme hatası: {str(e)}"
        )


@router.get("/schemas")
async def list_available_schemas(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """TR: Mevcut schema'ları listele"""
    try:
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid4()))
        
        validation_service = ValidationService()
        
        schemas = list(validation_service._validators.keys())
        
        response = JSONResponse(
            content={
                "success": True,
                "data": {
                    "schemas": schemas,
                    "count": len(schemas)
                }
            },
            headers={
                "X-Correlation-ID": correlation_id,
                "X-Request-ID": str(uuid4())
            }
        )
        
        return response
        
    except Exception as e:
        logger.error(f"TR: Schema listesi hatası: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"TR: Schema listesi hatası: {str(e)}"
        )
