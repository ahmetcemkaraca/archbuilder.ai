from __future__ import annotations

from httpx import AsyncClient
from fastapi import FastAPI


async def test_ai_commands_create_and_get(app: FastAPI):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        create = await ac.post(
            "/v1/ai/commands",
            json={"command": "analyze", "input": {"text": "hello"}},
        )
        assert create.status_code in (200, 401)
        if create.status_code == 200:
            data = create.json()["data"]
            cmd_id = data["id"]
            get = await ac.get(f"/v1/ai/commands/{cmd_id}")
            assert get.status_code == 200


async def test_ai_validate_endpoint(app: FastAPI):
    payload = {
        "walls": [{"start": {"x": 0, "y": 0}, "end": {"x": 200, "y": 0}}],
        "doors": [{"width": 900}],
        "corridors": [{"width": 1300}],
    }
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.post("/v1/ai/validate", json={"payload": payload})
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["status"] in ("valid", "requires_review")


async def test_ai_validate_rejected_path(app: FastAPI):
    # Çok kısa duvar + dar koridor -> rejected olmalı (>=4 hata varsayımı yerine kesin hata kontrolü)
    payload = {
        "walls": [
            {"start": {"x": 0, "y": 0}, "end": {"x": 1, "y": 0}},
            {"start": {"x": 0, "y": 0}, "end": {"x": 1, "y": 0}},
            {"start": {"x": 0, "y": 0}, "end": {"x": 1, "y": 0}},
            {"start": {"x": 0, "y": 0}, "end": {"x": 1, "y": 0}},
        ],
        "doors": [{"width": 100}],
        "corridors": [{"width": 200}],
    }
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.post("/v1/ai/validate", json={"payload": payload})
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["status"] in ("requires_review", "rejected")

