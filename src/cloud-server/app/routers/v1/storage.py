from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.core.exceptions import envelope
from app.security.authentication import require_api_key
from app.services.storage_service import StorageService


router = APIRouter(prefix="/v1/storage", tags=["storage"], dependencies=[require_api_key])
storage = StorageService()


class UploadInitResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    error: Optional[Dict[str, Any]] = None


@router.post("/upload/init", response_model=UploadInitResponse)
async def upload_init() -> Dict[str, Any]:
    # TR: Basit upload id üretimi (örn. client oluşturur), burada sabit kabul edelim
    return envelope(True, {"message": "provide a unique upload_id on chunk calls"})


@router.post("/upload/chunk")
async def upload_chunk(upload_id: str = Form(...), index: int = Form(...), file: UploadFile = File(...)) -> Dict[str, Any]:
    content = await file.read()
    storage.write_chunk(upload_id, index, content)
    return envelope(True, {"received": index})


@router.post("/upload/complete")
async def upload_complete(upload_id: str = Form(...), filename: str = Form(...)) -> Dict[str, Any]:
    try:
        path = storage.assemble(upload_id, filename)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return envelope(True, {"path": str(path)})


