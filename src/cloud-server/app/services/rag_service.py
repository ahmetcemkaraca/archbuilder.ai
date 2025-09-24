from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.ai.ragflow.client import RAGFlowClient
from app.core.config import settings


class RAGService:
    """Service orchestrating interactions with external RAGFlow.

    Notlar (TR): Bu servis RAGFlow istemcisi ile veri seti oluşturma, belge
    yükleme, parse etme ve retrieval için basit yardımcılar sağlar.
    """

    def __init__(self) -> None:
        self._client = RAGFlowClient(
            base_url=str(settings.ragflow_base_url),
            api_key=settings.ragflow_api_key,
            version=settings.ragflow_api_version,
            timeout_seconds=settings.ragflow_timeout_seconds,
        )

    async def ensure_dataset(self, name: str) -> str:
        return await self._client.ensure_dataset(name)

    async def upload_and_parse(
        self,
        dataset_id: str,
        files: List[bytes],
        filenames: List[str],
        parse_options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Belge yükle ve RAGFlow içinde parse/index işlemini başlat."""

        upload_res = await self._client.upload_documents(dataset_id, files, filenames)
        document_ids = [d["id"] for d in upload_res.get("data", []) if isinstance(d, dict) and "id" in d]
        return await self._client.parse_documents(dataset_id, document_ids=document_ids, options=parse_options)

    async def retrieval(
        self,
        question: str,
        dataset_ids: Optional[List[str]] = None,
        document_ids: Optional[List[str]] = None,
        top_k: Optional[int] = None,
        vector_similarity_weight: Optional[float] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return await self._client.retrieval(
            question=question,
            dataset_ids=dataset_ids,
            document_ids=document_ids,
            top_k=top_k,
            vector_similarity_weight=vector_similarity_weight,
            extra=extra,
        )


