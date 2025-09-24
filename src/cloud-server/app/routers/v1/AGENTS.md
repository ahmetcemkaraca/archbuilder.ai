# AGENTS.md — Routers (v1)

Versioned FastAPI endpoints.

## Active Rules (MDc)
- `.cursor/rules/instructions-api-standards.mdc`
- `.cursor/rules/instructions-python-fastapi.mdc`
- `.cursor/rules/instructions-error-handling.mdc`
- `.cursor/rules/instructions-logging-standards.mdc`
- `.cursor/rules/instructions-registry-governance.mdc`

## When to consult which rules
- Adding/changing endpoints: API Standards; update `docs/registry/endpoints.json`.
- Request/response models: Data Structures; update `docs/registry/schemas.json`.
- Auth and headers: Security; API Standards.
- Error responses & correlation: Error Handling, Logging Standards.
