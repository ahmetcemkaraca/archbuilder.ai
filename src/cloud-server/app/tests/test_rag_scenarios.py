from __future__ import annotations

import uuid
from httpx import AsyncClient
from fastapi import FastAPI
from app.ai.chunking import chunk_text


async def test_hybrid_search_minimal(app: FastAPI):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.post(
            "/v1/rag/hybrid-search",
            json={
                "query": "example",
                "dataset_ids": ["ds_test"],
                "max_results": 5,
                "keyword_boost": 0.4,
                "dense_boost": 0.6,
            },
        )
        assert resp.status_code in (200, 502)


async def test_strict_query_missing_dataset(app: FastAPI):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.post(
            "/v1/rag/query/strict",
            json={"query": "oops"},
        )
        assert resp.status_code == 400


async def test_rag_query_propagates_correlation_id(app: FastAPI):
    cid = str(uuid.uuid4())
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.post("/v1/rag/query", json={"query": "hello"}, headers={"X-Correlation-ID": cid})
        assert resp.status_code in (200, 502)
        # TR: Middleware yanıt başlıklarını kontrol edelim
        assert resp.headers.get("x-request-id")
        assert resp.headers.get("x-correlation-id")


def test_chunk_text_basic():
    text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Vestibulum."
    chunks = chunk_text(text, max_chars=20, overlap=5)
    assert len(chunks) >= 3
    for c in chunks:
        assert len(c) <= 20


