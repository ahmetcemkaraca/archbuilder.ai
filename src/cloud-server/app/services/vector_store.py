from __future__ import annotations

from typing import List, Dict, Any, Protocol, Optional


class VectorStore(Protocol):
    async def index_documents(self, dataset_id: str, embeddings: List[List[float]], metadatas: List[Dict[str, Any]]) -> None: ...
    async def hybrid_search(self, query_embedding: List[float], k: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]: ...


class InMemoryVectorStore:
    """Basit in-memory vektör mağazası (demo/stub).

    TR: Üretimde FAISS/PGVector/Elastic+KNN gibi bir çözüm tercih edilmelidir.
    """

    def __init__(self) -> None:
        self._items: List[Dict[str, Any]] = []

    async def index_documents(self, dataset_id: str, embeddings: List[List[float]], metadatas: List[Dict[str, Any]]) -> None:
        for emb, meta in zip(embeddings, metadatas):
            self._items.append({"dataset_id": dataset_id, "embedding": emb, "meta": meta})

    async def hybrid_search(self, query_embedding: List[float], k: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        # TR: Saf kosinüs benzerliği yerine çok basit dot-product yaklaşımı
        def score(a: List[float], b: List[float]) -> float:
            return float(sum(x * y for x, y in zip(a, b)))

        candidates = self._items
        if filters:
            for key, val in filters.items():
                candidates = [c for c in candidates if c["meta"].get(key) == val]
        ranked = sorted(candidates, key=lambda c: score(query_embedding, c["embedding"]), reverse=True)
        return ranked[:k]




