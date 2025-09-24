# AGENTS.md — Cloud Server (FastAPI)

This folder hosts the Python FastAPI cloud server. When coding here, consult the rule files below for standards, contracts, and workflows.

How AGENTS.md works: see `.mds/rules.md` for Cursor rule mechanics, nested AGENTS.md behavior, and best practices.

## Active Rules to Consult (MDc locations)
- `.cursor/rules/instructions-universal-agent.mdc`
- `.cursor/rules/instructions-python-fastapi.mdc`
- `.cursor/rules/instructions-api-standards.mdc`
- `.cursor/rules/instructions-error-handling.mdc`
- `.cursor/rules/instructions-logging-standards.mdc`
- `.cursor/rules/instructions-ai-integration.mdc`
- `.cursor/rules/instructions-ai-prompt-standards.mdc`
- `.cursor/rules/instructions-data-structures.mdc`
- `.cursor/rules/instructions-performance-optimization.mdc`
- `.cursor/rules/instructions-qa.mdc`
- `.cursor/rules/instructions-security.mdc`
- `.cursor/rules/instructions-registry-governance.mdc`
- `.cursor/rules/registry-and-context.mdc`

## Coding-time Checklist
- Rehydrate context: read `docs/registry/*.json` and `.mds/context/current-context.md` before edits.
- Keep public contracts in sync with registry; add at least one test per change.
- Python 3.12 target; run `python -m py_compile` and `pip check` on changes.
- Structure errors with standard taxonomy; add structured logging with correlation IDs.
- No secrets in code. Document env vars in `.env.example`.
- Update `version.md` every 2 prompts (PowerShell timestamp), prefer `scripts/run-vibe-coding.ps1`.


