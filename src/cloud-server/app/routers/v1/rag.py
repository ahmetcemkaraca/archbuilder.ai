from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.services.rag_service import RAGService


router = APIRouter(prefix="/v1/rag", tags=["rag"])


class RAGQueryRequest(BaseModel):
    query: str = Field(..., min_length=1)
    document_types: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    max_results: int = Field(10, ge=1, le=100)
    similarity_threshold: float = Field(0.3, ge=0.0, le=1.0)
    filters: Optional[Dict[str, Any]] = None
    dataset_ids: Optional[List[str]] = None
    document_ids: Optional[List[str]] = None
    top_k: Optional[int] = Field(default=None, ge=1, le=100)
    vector_similarity_weight: Optional[float] = Field(default=None, ge=0.0)


class RAGQueryResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    error: Dict[str, Any] | None = None


def get_service() -> RAGService:
    return RAGService()


@router.post("/query", response_model=RAGQueryResponse)
async def query_knowledge_base(
    request: RAGQueryRequest,
    req: Request,
    rag_service: RAGService = Depends(get_service),
):
    """Proxy RAGFlow retrieval with ArchBuilder schema.

    Notlar (TR): RAGFlow `/api/v1/retrieval` uç noktasına uygun veri aktarımı
    yapar, dönen yanıtı standard envelope içine sarar.
    """

    try:
        # TR: Basit PII maskeleme (e-posta ve 32+ char tokenları gizle)
        def _mask_pii(text: str) -> str:
            import re

            text = re.sub(
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
                "[EMAIL_REDACTED]",
                text,
            )
            text = re.sub(r"\b[A-Za-z0-9]{32,}\b", "[TOKEN_REDACTED]", text)
            return text

        safe_query = _mask_pii(request.query)
        cid = None
        if req is not None:
            headers = req.headers
            cid = headers.get("x-correlation-id") or headers.get("x-request-id")

        res = await rag_service.retrieval(
            question=safe_query,
            dataset_ids=request.dataset_ids,
            document_ids=request.document_ids,
            top_k=request.top_k or request.max_results,
            vector_similarity_weight=request.vector_similarity_weight,
            extra={"filters": request.filters} if request.filters else None,
            correlation_id=cid,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=502, detail=f"RAGFlow upstream error: {exc}"
        ) from exc

    return RAGQueryResponse(success=True, data=res, error=None)


class StrictQueryError(BaseModel):
    detail: str


@router.post(
    "/query/strict",
    response_model=RAGQueryResponse,
    responses={400: {"model": StrictQueryError}, 404: {"model": StrictQueryError}},
)
async def query_knowledge_base_strict(
    request: RAGQueryRequest,
    req: Request,
    rag_service: RAGService = Depends(get_service),
):
    """Eksik veri ve boş sonuç durumlarını anlamlı hatalarla döndürür."""
    if not request.dataset_ids:
        raise HTTPException(
            status_code=400, detail="dataset_ids is required for strict query"
        )

    try:

        def _mask_pii(text: str) -> str:
            import re

            text = re.sub(
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
                "[EMAIL_REDACTED]",
                text,
            )
            text = re.sub(r"\b[A-Za-z0-9]{32,}\b", "[TOKEN_REDACTED]", text)
            return text

        cid = None
        if req is not None:
            headers = req.headers
            cid = headers.get("x-correlation-id") or headers.get("x-request-id")

        res = await rag_service.retrieval(
            question=_mask_pii(request.query),
            dataset_ids=request.dataset_ids,
            document_ids=request.document_ids,
            top_k=request.top_k or request.max_results,
            vector_similarity_weight=request.vector_similarity_weight,
            extra={"filters": request.filters} if request.filters else None,
            correlation_id=cid,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=502, detail=f"RAGFlow upstream error: {exc}"
        ) from exc

    if not res or not res.get("data"):
        raise HTTPException(
            status_code=404,
            detail="No results found for the given datasets and filters",
        )

    return RAGQueryResponse(success=True, data=res)


class IndexBuildRequest(BaseModel):
    dataset_id: str = Field(..., min_length=1)
    rebuild: bool = Field(default=False)


class StandardResponse(BaseModel):
    success: bool
    data: Dict[str, Any]


@router.post("/index/build", response_model=StandardResponse)
async def build_index(
    body: IndexBuildRequest,
    req: Request,
    svc: RAGService = Depends(get_service),
):
    try:
        cid = None
        if req is not None:
            headers = req.headers
            cid = headers.get("x-correlation-id") or headers.get("x-request-id")
        res = await svc.build_index(body.dataset_id, body.rebuild, correlation_id=cid)
        return StandardResponse(success=True, data=res)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=502, detail=f"Index build failed: {exc}"
        ) from exc


class HybridSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    dataset_ids: Optional[List[str]] = None
    max_results: int = Field(10, ge=1, le=100)
    keyword_boost: float = Field(0.5, ge=0.0, le=1.0)
    dense_boost: float = Field(0.5, ge=0.0, le=1.0)
    filters: Optional[Dict[str, Any]] = None


@router.post("/hybrid-search", response_model=RAGQueryResponse)
async def hybrid_search(
    body: HybridSearchRequest,
    req: Request,
    svc: RAGService = Depends(get_service),
):
    try:
        cid = None
        if req is not None:
            headers = req.headers
            cid = headers.get("x-correlation-id") or headers.get("x-request-id")

        res = await svc.hybrid_search(
            query=body.query,
            dataset_ids=body.dataset_ids,
            keyword_boost=body.keyword_boost,
            dense_boost=body.dense_boost,
            max_results=body.max_results,
            filters=body.filters,
        )
        return RAGQueryResponse(success=True, data=res)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=502, detail=f"Hybrid search failed: {exc}"
        ) from exc
