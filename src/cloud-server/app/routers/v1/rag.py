from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
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
    rag_service: RAGService = Depends(get_service),
):
    """Proxy RAGFlow retrieval with ArchBuilder schema.

    Notlar (TR): RAGFlow `/api/v1/retrieval` uç noktasına uygun veri aktarımı
    yapar, dönen yanıtı standard envelope içine sarar.
    """

    try:
        res = await rag_service.retrieval(
            question=request.query,
            dataset_ids=request.dataset_ids,
            document_ids=request.document_ids,
            top_k=request.top_k or request.max_results,
            vector_similarity_weight=request.vector_similarity_weight,
            extra={"filters": request.filters} if request.filters else None,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"RAGFlow upstream error: {exc}") from exc

    return RAGQueryResponse(success=True, data=res, error=None)


