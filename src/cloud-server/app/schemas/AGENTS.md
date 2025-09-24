# AGENTS.md — Schemas (Pydantic)

Request/response and domain schemas.

## Active Rules (MDc)
- `.cursor/rules/instructions-data-structures.mdc`
- `.cursor/rules/instructions-registry-governance.mdc`
- `.cursor/rules/registry-and-context.mdc`

## When to consult which rules
- New fields or models: Data Structures.
- Public schema changes: Registry Governance; update `docs/registry/schemas.json` and add tests.
