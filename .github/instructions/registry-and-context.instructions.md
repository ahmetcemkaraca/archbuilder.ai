---
applyTo: "docs/registry/**/*.json,.mds/context/**/*.md,.mds/context/**/*.json,**/*.md"
description: Registry and Context Management — contract lifecycle for identifiers, endpoints, and schemas with CI enforcement.
---

# Registry & Context Management

## Registry Maintenance
After any changes to public contracts, identifiers, or system interfaces, you MUST update the following registry files:

### Registry Files
- `docs/registry/identifiers.json` - modules, exports, variables, config keys
- `docs/registry/endpoints.json` - HTTP/gRPC/GraphQL contracts (method, path, schemas, version, auth)
- `docs/registry/schemas.json` - data models, DB tables, migrations

### Context Management  
- `.mds/context/current-context.md` - active summary of key contracts and variables
- `.mds/context/history/NNNN.md` - append per-session summaries before context clearing

## Validation Commands
After registry updates, run validation scripts:
```powershell
pwsh -File scripts/validate-registry.ps1
pwsh -File scripts/rehydrate-context.ps1
```

## Versioning Cadence
- Update `version.md` every 2 prompts with PowerShell timestamp
- Use: `Get-Date -Format 'yyyy-MM-dd HH:mm:ss'`
- Include summary of key changes, new features, or bug fixes

## Context Rehydration Rules
Before starting new work:
1. Read `.mds/context/current-context.md` 
2. Read `docs/registry/*.json` files
3. Confirm open contracts (functions/endpoints/schemas)
4. Run context rehydration script

## Contract Change Requirements
- Never change public contracts without updating registry
- Add at least one test covering new/changed contracts
- Maintain backward compatibility unless version bump justified
- Document breaking changes in CHANGELOG.md

## Session Management
- One session should handle ~3 related tasks
- Commit registry changes with corresponding code changes
- Use correlation IDs in commit messages for traceability
- Ensure CI passes before moving to next prompt batch