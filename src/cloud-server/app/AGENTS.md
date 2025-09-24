# AGENTS.md — FastAPI App (Root)

This folder hosts the application modules (routers, services, schemas, security, middleware).

See `.mds/rules.md` for AGENTS.md behavior and nested rules.

## Active Rules (MDc)
- `.cursor/rules/instructions-universal-agent.mdc`
- `.cursor/rules/instructions-python-fastapi.mdc`
- `.cursor/rules/instructions-api-standards.mdc`
- `.cursor/rules/instructions-error-handling.mdc`
- `.cursor/rules/instructions-logging-standards.mdc`
- `.cursor/rules/instructions-registry-governance.mdc`
- `.cursor/rules/registry-and-context.mdc`

## When to consult which rules
- Endpoints (create/update routers): API Standards, Error Handling, Logging Standards, Registry Governance.
- Pydantic models/schemas: Data Structures, Registry Governance.
- Middlewares & security headers: Error Handling, Security, Logging Standards.
- Service logic & integrations: AI Integration, API Standards, Performance Optimization.
- Tests: QA, Registry Governance (contract tests).
