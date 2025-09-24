from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.ai.ragflow.client import RAGFlowClient
from app.core.config import settings
from app.database.session import AsyncSession, get_db
from sqlalchemy import select
from app.database.models.project import RAGDatasetLink


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

    async def ensure_dataset(self, name: str, correlation_id: Optional[str] = None) -> str:
        return await self._client.ensure_dataset(name, correlation_id=correlation_id)

    async def ensure_project_dataset(
        self,
        db: AsyncSession,
        owner_id: str,
        project_id: str,
        preferred_name: str,
        correlation_id: Optional[str] = None,
    ) -> str:
        """Proje için RAGFlow dataset ID'sini getir veya oluştur.

        Notlar (TR): Önce yerel eşleme tablosuna bakarız; yoksa RAGFlow'ta
        dataset oluşturup eşlemeyi kaydederiz.
        """

        res = await db.execute(
            select(RAGDatasetLink).where(
                RAGDatasetLink.owner_id == owner_id,
                RAGDatasetLink.project_id == project_id,
            )
        )
        link = res.scalar_one_or_none()
        if link:
            return link.dataset_id

        dataset_id = await self.ensure_dataset(preferred_name, correlation_id=correlation_id)
        link = RAGDatasetLink(
            id=str(uuid4()),
            owner_id=owner_id,
            project_id=project_id,
            dataset_id=dataset_id,
        )
        db.add(link)
        await db.flush()
        return dataset_id

    async def upload_and_parse(
        self,
        dataset_id: str,
        files: List[bytes],
        filenames: List[str],
        parse_options: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Belge yükle ve RAGFlow içinde parse/index işlemini başlat."""

        upload_res = await self._client.upload_documents(dataset_id, files, filenames, correlation_id=correlation_id)
        document_ids = [d["id"] for d in upload_res.get("data", []) if isinstance(d, dict) and "id" in d]
        return await self._client.parse_documents(
            dataset_id,
            document_ids=document_ids,
            options=parse_options,
            correlation_id=correlation_id,
        )

    async def retrieval(
        self,
        question: str,
        dataset_ids: Optional[List[str]] = None,
        document_ids: Optional[List[str]] = None,
        top_k: Optional[int] = None,
        vector_similarity_weight: Optional[float] = None,
        extra: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return await self._client.retrieval(
            question=question,
            dataset_ids=dataset_ids,
            document_ids=document_ids,
            top_k=top_k,
            vector_similarity_weight=vector_similarity_weight,
            extra=extra,
            correlation_id=correlation_id,
        )

    async def build_index(self, dataset_id: str, rebuild: bool = False, correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """RAGFlow tarafında index build/update tetikle.

        Notlar (TR): RAGFlow `parse_documents` endpointi dataset bazında yeniden
        chunking/index başlatır. `rebuild=True` gönderirsek tam yeniden kurulum
        beklentisini işaretleriz (uygulama-spesifik, opsiyonel).
        """
        options: Dict[str, Any] = {"rebuild": rebuild}
        return await self._client.parse_documents(dataset_id, document_ids=None, options=options, correlation_id=correlation_id)

    async def hybrid_search(
        self,
        query: str,
        dataset_ids: Optional[List[str]],
        keyword_boost: float = 0.5,
        dense_boost: float = 0.5,
        max_results: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Anahtar kelime + dense (vektör) hibrit arama proxy.

        Notlar (TR): RAGFlow `retrieval` için ek alanlara hibrit parametreleri
        geçiriyoruz. Sağlayıcı bu alanları desteklemiyorsa backend tarafında
        görmezden gelinebilir.
        """
        extra: Dict[str, Any] = {
            "hybrid": True,
            "keyword_boost": keyword_boost,
            "dense_boost": dense_boost,
        }
        if filters:
            extra["filters"] = filters
        return await self._client.retrieval(
            question=query,
            dataset_ids=dataset_ids,
            top_k=max_results,
            extra=extra,
        )


