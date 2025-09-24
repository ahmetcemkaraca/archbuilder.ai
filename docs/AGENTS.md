# AGENTS.md — Documentation & Registry

This folder holds architecture docs, registries, and guides. Maintain registry-first governance.

Read `.mds/rules.md` for details on AGENTS.md and how rules apply.

## Active Rules to Consult (MDc locations)
- `.cursor/rules/instructions-universal-agent.mdc`
- `.cursor/rules/instructions-architect.mdc`
- `.cursor/rules/instructions-architecture-decisions.mdc`
- `.cursor/rules/instructions-api-standards.mdc`
- `.cursor/rules/instructions-registry-governance.mdc`
- `.cursor/rules/registry-and-context.mdc`

## Documentation Checklist
- Update `docs/registry/identifiers.json`, `endpoints.json`, `schemas.json` with public contract changes.
- Run `pwsh -File scripts/validate-registry.ps1` and `pwsh -File scripts/rehydrate-context.ps1` after edits.
- Append `version.md` every 2 prompts.
