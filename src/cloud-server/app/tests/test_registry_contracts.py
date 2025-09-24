from __future__ import annotations

import json
from pathlib import Path


def test_endpoints_document_headers():
    root = Path(__file__).resolve().parents[4]
    endpoints = json.loads((root / "docs/registry/endpoints.json").read_text(encoding="utf-8"))
    # Ensure RAG endpoints have correlation headers documented
    paths = {e["path"]: e for e in endpoints["endpoints"]}
    for p in [
        "/v1/rag/query",
        "/v1/documents/rag/ensure-dataset",
        "/v1/documents/rag/{dataset_id}/upload-parse",
        "/v1/documents/rag/{dataset_id}/upload-parse/async",
        "/v1/rag/index/build",
        "/v1/rag/hybrid-search",
    ]:
        assert "headers" in paths[p]
        hdrs = paths[p]["headers"]
        assert "request" in hdrs and "response" in hdrs
        assert "X-Correlation-ID?" in hdrs["request"]
        assert "X-Correlation-ID" in hdrs["response"]
        assert "X-Request-ID" in hdrs["response"]


def test_db_tables_documented_in_schemas():
    root = Path(__file__).resolve().parents[4]
    schemas = json.loads((root / "docs/registry/schemas.json").read_text(encoding="utf-8"))
    names = {s["name"] for s in schemas["schemas"]}
    expected = {
        "DB.users",
        "DB.projects",
        "DB.ai_commands",
        "DB.subscriptions",
        "DB.usage",
        "DB.rag_dataset_links",
        "DB.rag_jobs",
        "DB.rag_document_links",
    }
    missing = expected - names
    assert not missing, f"Missing schemas: {missing}"


