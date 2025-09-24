# AGENTS.md — Database (Models, Migrations)

SQLAlchemy models, migrations, and sessions.

## Active Rules (MDc)
- `.cursor/rules/instructions-data-structures.mdc`
- `.cursor/rules/instructions-registry-governance.mdc`
- `.cursor/rules/registry-and-context.mdc`
- `.cursor/rules/instructions-logging-standards.mdc`
- `.cursor/rules/instructions-error-handling.mdc`

## When to consult which rules
- New/changed models: Data Structures; update `docs/registry/schemas.json` and add tests.
- Migration creation: Registry Governance.
- DB error handling/retries: Error Handling; log structured DB events.
