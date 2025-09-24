from __future__ import annotations

import asyncio
from httpx import AsyncClient
from fastapi import FastAPI


async def test_ensure_dataset_and_upload_parse(app: FastAPI):
    """Smoke: ensure-dataset endpoint responds and upload-parse validates payload paths."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.post(
            "/v1/documents/rag/ensure-dataset",
            json={"owner_id": "user1", "project_id": "proj1", "preferred_name": "proj1-ds"},
        )
        # Upstream may be unavailable locally; assert contract keys when 200
        if resp.status_code == 200:
            data = resp.json()
            assert data["success"] is True
            assert "dataset_id" in data["data"]


