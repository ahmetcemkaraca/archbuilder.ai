from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any, Dict, List, Optional

import httpx


class RAGFlowClient:
    """Thin async HTTP client for RAGFlow HTTP API.

    Notlar (TR): Bu istemci RAGFlow'un HTTP uç noktalarına bağlanır. Kimlik
    doğrulama için `Authorization: Bearer <token>` başlığı kullanılır. Zaman
    aşımları ve temel hata işleme dahil edilmiştir.
    """

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        version: str = "v1",
        timeout_seconds: int = 30,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._version = version
        self._timeout = timeout_seconds
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "RAGFlowClient":
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=httpx.Timeout(self._timeout),
            headers=self._default_headers(),
        )
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    def _default_headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    def with_correlation(self, correlation_id: Optional[str]) -> Dict[str, str]:
        """TR: Çağrı bazında correlation ID header ekle."""
        headers = {}
        if correlation_id:
            headers["X-Correlation-ID"] = correlation_id
        return headers

    @property
    def _api(self) -> httpx.AsyncClient:
        if self._client is None:
            # Notlar (TR): Context manager kullanılmamışsa lazy init yap.
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=httpx.Timeout(self._timeout),
                headers=self._default_headers(),
            )
        return self._client

    # ----------------------------- Core endpoints ----------------------------
    async def create_dataset(
        self, name: str, correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """POST /api/{version}/datasets"""
        url = f"/api/{self._version}/datasets"
        resp = await self._api.post(
            url, json={"name": name}, headers=self.with_correlation(correlation_id)
        )
        resp.raise_for_status()
        return resp.json()

    async def upload_documents(
        self,
        dataset_id: str,
        files: List[bytes],
        filenames: List[str],
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """POST /api/{version}/datasets/{dataset_id}/documents multipart upload.

        Notlar (TR): Çoklu dosya desteği sağlanır; RAGFlow `file` alan adını
        bekler. httpx `files` parametresi ile gönderilir.
        """

        url = f"/api/{self._version}/datasets/{dataset_id}/documents"
        files_payload = [("file", (filenames[i], files[i])) for i in range(len(files))]
        # httpx `files` kullandığımız için Content-Type otomatik ayarlanır
        resp = await self._api.post(
            url, files=files_payload, headers=self.with_correlation(correlation_id)
        )
        resp.raise_for_status()
        return resp.json()

    async def parse_documents(
        self,
        dataset_id: str,
        document_ids: Optional[List[str]] = None,
        options: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """POST /api/{version}/datasets/{dataset_id}/chunks -> parse/index"""
        url = f"/api/{self._version}/datasets/{dataset_id}/chunks"
        payload: Dict[str, Any] = options.copy() if options else {}
        if document_ids is not None:
            payload["document_ids"] = document_ids
        # Basit retry/backoff: 429/503 durumlarında iki kez daha dene
        attempts = 0
        while True:
            resp = await self._api.post(
                url, json=payload, headers=self.with_correlation(correlation_id)
            )
            if resp.status_code not in (429, 503) or attempts >= 2:
                break
            await asyncio.sleep(0.5 * (attempts + 1))
            attempts += 1
        resp.raise_for_status()
        return resp.json()

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
        """POST /api/v1/retrieval

        RAGFlow testlerinde kullanılan genel retrieval uç noktası.
        """

        url = "/api/v1/retrieval"
        payload: Dict[str, Any] = {"question": question}
        if dataset_ids is not None:
            payload["dataset_ids"] = dataset_ids
        if document_ids is not None:
            payload["document_ids"] = document_ids
        if top_k is not None:
            payload["top_k"] = top_k
        if vector_similarity_weight is not None:
            payload["vector_similarity_weight"] = vector_similarity_weight
        if extra:
            payload.update(extra)

        resp = await self._api.post(
            url, json=payload, headers=self.with_correlation(correlation_id)
        )
        resp.raise_for_status()
        return resp.json()

    # ------------------------------ Utilities --------------------------------
    async def ensure_dataset(
        self, preferred_name: str, correlation_id: Optional[str] = None
    ) -> str:
        """Create dataset if not exists (best-effort).

        Notlar (TR): RAGFlow doğrudan "get by name" sağlamadığından, oluşturulan
        ID'yi döneriz. Var olanı yönetmek üst süreçlerin sorumluluğundadır.
        """

        res = await self.create_dataset(preferred_name, correlation_id=correlation_id)
        return res["data"]["id"]

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None


async def _quick_selfcheck() -> None:
    """Hızlı yerel doğrulama (isteğe bağlı)."""
    client = RAGFlowClient("http://localhost")
    try:
        # Bu yalnızca bağlantı/timeout hatası yakalamak içindir.
        await client.retrieval("ping", dataset_ids=["ds_test"])
    except Exception:  # noqa: BLE001
        pass
    finally:
        await client.aclose()


if __name__ == "__main__":
    asyncio.run(_quick_selfcheck())
