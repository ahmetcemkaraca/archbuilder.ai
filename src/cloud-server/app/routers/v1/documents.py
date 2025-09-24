from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.services.rag_service import RAGService
from sqlalchemy import select
from app.database.models.rag import RAGJob, RAGDocumentLink


router = APIRouter(prefix="/v1/documents", tags=["documents"])


class EnsureDatasetRequest(BaseModel):
    owner_id: str = Field(..., min_length=1)
    project_id: str = Field(..., min_length=1)
    preferred_name: str = Field(..., min_length=1)


class EnsureDatasetResponse(BaseModel):
    success: bool
    data: Dict[str, Any]


def get_service() -> RAGService:
    return RAGService()


@router.post("/rag/ensure-dataset", response_model=EnsureDatasetResponse)
async def ensure_dataset(
    req: EnsureDatasetRequest,
    db: AsyncSession = Depends(get_db),
    svc: RAGService = Depends(get_service),
    request: Request | None = None,
):
    """Kullanıcı/Proje için RAG dataset oluştur veya mevcut olanı getir."""

    try:
        cid = None
        if request is not None:
            headers = request.headers
            cid = headers.get("x-correlation-id") or headers.get("x-request-id")

        dataset_id = await svc.ensure_project_dataset(
            db=db,
            owner_id=req.owner_id,
            project_id=req.project_id,
            preferred_name=req.preferred_name,
            correlation_id=cid,
        )
        return EnsureDatasetResponse(success=True, data={"dataset_id": dataset_id})
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"RAG ensure dataset failed: {exc}") from exc


class UploadParseResponse(BaseModel):
    success: bool
    data: Dict[str, Any]


@router.post("/rag/{dataset_id}/upload-parse", response_model=UploadParseResponse)
async def upload_and_parse(
    dataset_id: str,
    files: List[UploadFile] = File(...),
    parse_strategy: Optional[str] = Form(default=None),
    svc: RAGService = Depends(get_service),
    request: Request | None = None,
):
    """Belge(leri) yükle ve RAGFlow üzerinde parse/index işlemini tetikle."""

    try:
        file_bytes: List[bytes] = [await f.read() for f in files]
        filenames: List[str] = [f.filename or "document" for f in files]
        parse_options: Dict[str, Any] = {"strategy": parse_strategy} if parse_strategy else {}
        cid = None
        if request is not None:
            headers = request.headers
            cid = headers.get("x-correlation-id") or headers.get("x-request-id")
        res = await svc.upload_and_parse(dataset_id, file_bytes, filenames, parse_options or None, correlation_id=cid)
        return UploadParseResponse(success=True, data=res)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"RAG upload/parse failed: {exc}") from exc


class JobAcceptedResponse(BaseModel):
    success: bool
    data: Dict[str, Any]


@router.post("/rag/{dataset_id}/upload-parse/async", status_code=202, response_model=JobAcceptedResponse)
async def upload_and_parse_async(
    dataset_id: str,
    files: List[UploadFile] = File(...),
    parse_strategy: Optional[str] = Form(default=None),
    db: AsyncSession = Depends(get_db),
    svc: RAGService = Depends(get_service),
    request: Request | None = None,
):
    """Upload→parse işlemini asenkron job olarak kuyruğa alır (basit DB queue)."""
    job_id = str(uuid4())
    job = RAGJob(
        id=job_id,
        job_type="upload_parse",
        status="queued",
        dataset_id=dataset_id,
    )
    db.add(job)
    await db.flush()

    # Not: Demo amaçlı arka planı taklit ediyoruz; gerçek kurulumda Redis/RQ/Celery kullanılmalı.
    try:
        file_bytes: List[bytes] = [await f.read() for f in files]
        filenames: List[str] = [f.filename or "document" for f in files]
        parse_options: Dict[str, Any] = {"strategy": parse_strategy} if parse_strategy else {}
        cid = None
        if request is not None:
            headers = request.headers
            cid = headers.get("x-correlation-id") or headers.get("x-request-id")
        res = await svc.upload_and_parse(dataset_id, file_bytes, filenames, parse_options or None, correlation_id=cid)

        # Document id eşlemeleri
        docs = res.get("data") or res
        for i, fname in enumerate(filenames):
            doc_id = None
            try:
                doc_id = docs["documents"][i]["id"]
            except Exception:  # noqa: BLE001
                pass
            if doc_id:
                db.add(RAGDocumentLink(id=str(uuid4()), dataset_id=dataset_id, document_id=doc_id, filename=fname))

        job.status = "succeeded"
        job.result_json = "{}"
    except Exception as exc:  # noqa: BLE001
        job.status = "failed"
        job.error_message = str(exc)
    finally:
        from datetime import datetime
        job.updated_at = datetime.utcnow()
        await db.flush()

    return JobAcceptedResponse(success=True, data={"job_id": job_id})


class JobStatusResponse(BaseModel):
    success: bool
    data: Dict[str, Any]


@router.get("/rag/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(RAGJob).where(RAGJob.id == job_id))
    job = res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return JobStatusResponse(
        success=True,
        data={
            "job_id": job.id,
            "status": job.status,
            "error": job.error_message,
        },
    )


