---
applyTo: "**/*.py"
description: Python FastAPI — Pydantic validation, secure headers, pytest tests.
---
As Python FastAPI:
- Use FastAPI + Pydantic for request/response models; strict typing, mypy optional.
- Security: starlette middleware for CORS allowlist, rate limit (proxy/backing), secure cookies, auth schemes.
- Validation: explicit models; 422 on invalid; enum/regex constraints; output models to avoid overexposure.
- Errors: structured error responses; no internal details in prod; logging with request IDs.
- Data: SQLModel/SQLAlchemy + Alembic migrations; transactions; idempotency for POST.
- Tests: pytest + httpx AsyncClient; factory fixtures; coverage thresholds.
- Performance: uvicorn workers tuned; timeouts; caching where safe.
- DX: pip-tools/uv/poetry locked deps; .env.example; Makefile or ps1 helpers.
