from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.core.exceptions import envelope
from app.security.authentication import require_api_key
from app.services.storage_service import StorageService
from app.services.virus_scanner import VirusScanner
from app.services.metadata_extractor import extract_basic_metadata
from app.services.preprocess.pdf_preprocess import preprocess_pdf
from app.services.preprocess.cad_preprocess import preprocess_cad


router = APIRouter(prefix="/v1/storage", tags=["storage"], dependencies=[require_api_key])
storage = StorageService()
scanner = VirusScanner()


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
        # Virus scan
        result = await scanner.scan_bytes(path.read_bytes())
        if result.infected:
            path.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail=f"Infected file: {result.reason or 'unknown'}")
        # Metadata extract
        meta = extract_basic_metadata(path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc
    # Optional preprocess hints
    extra: Dict[str, Any] = {}
    if meta.get("extension") == ".pdf":
        extra["preprocess"] = preprocess_pdf(path)
    elif meta.get("extension") in {".dxf", ".ifc"}:
        extra["preprocess"] = preprocess_cad(path)
    return envelope(True, {"path": str(path), "metadata": meta, **extra})


