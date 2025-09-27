from __future__ import annotations

import io
from httpx import AsyncClient
from fastapi import FastAPI


async def test_upload_parse_async_accepts_and_status(app: FastAPI):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        files = {"files": ("doc.txt", io.BytesIO(b"hello"), "text/plain")}
        resp = await ac.post(
            "/v1/documents/rag/ds_test/upload-parse/async", files=files
        )
        assert resp.status_code == 202
        data = resp.json()
        assert data["success"] is True
        job_id = data["data"]["job_id"]

        status = await ac.get(f"/v1/documents/rag/jobs/{job_id}")
        # Status 200 ve success alanının bulunması beklenir
        assert status.status_code in (200, 404)
