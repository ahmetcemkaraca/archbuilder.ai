from __future__ import annotations

import io
from httpx import AsyncClient
from fastapi import FastAPI


async def test_storage_upload_flow(app: FastAPI):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # init
        init = await ac.post("/v1/storage/upload/init", headers={"X-API-Key": "test"})
        assert init.status_code == 200
        # chunk
        files = {"file": ("a.bin", io.BytesIO(b"hello world"), "application/octet-stream")}
        chunk = await ac.post(
            "/v1/storage/upload/chunk",
            headers={"X-API-Key": "test"},
            data={"upload_id": "u1", "index": 0},
            files=files,
        )
        assert chunk.status_code == 200
        # complete
        complete = await ac.post(
            "/v1/storage/upload/complete",
            headers={"X-API-Key": "test"},
            data={"upload_id": "u1", "filename": "a.bin"},
        )
        assert complete.status_code in (200, 413)

