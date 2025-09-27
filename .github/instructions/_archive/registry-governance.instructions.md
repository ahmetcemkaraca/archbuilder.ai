---
applyTo: "docs/registry/**/*.json,.mds/context/**/*.md,.mds/context/**/*.json,**/*.md"
description: Registry Governance — contracts lifecycle for identifiers, endpoints, and schemas with CI enforcement.
---

Scope
- `docs/registry/identifiers.json`: modules, exports, variables, config keys
- `docs/registry/endpoints.json`: HTTP/gRPC contracts (method, path, io schemas, version, auth)
- `docs/registry/schemas.json`: data models, DB tables, migrations

Change Rules
1. Mandatory update: Any add/rename/delete of public functions, endpoints, or schemas must update the registry in the same PR
2. Versioning: Use SemVer; breaking changes require MAJOR bump and migration notes
3. Traceability: Reference issue/ADR in commit description
4. Tests: At least one test per changed contract (unit/integration)

Process
1. Before coding: Rehydrate context from registry; confirm intended diffs
2. During coding: Keep changes small and contract-focused; avoid unrelated edits
3. After coding: Run `scripts/validate-registry.ps1` and fix violations
4. CI: PR is blocked unless registry validation passes

Documentation
- Update related docs under `docs/` (API examples, error codes, migration steps)
- Add `version.md` entry (summary of contract changes)

Acceptance Checklist
- [ ] Registry diffs reflect code changes precisely
- [ ] Backward-compatibility assessed; SemVer bump applied
- [ ] Tests cover contract behaviors and failure modes
- [ ] Docs updated (endpoints, schemas, examples)
- [ ] CI registry validation green

