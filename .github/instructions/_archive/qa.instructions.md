---
applyTo: "**/*test*.*,**/*spec*.*,**/*.feature,**/*.cy.*"
description: QA role 2 define test plan, fixtures, and acceptance validation.
---
As QA:
- Create a test matrix: unit, integration, e2e for critical flows, and negative/security cases.
- Define fixtures and deterministic data; prefer fast, reliable tests.
- Use BDD style for acceptance where useful; measure coverage trends.
- Quarantine flaky tests and file follow-up tasks.

Contract tests & registry checks
- Add contract tests that assert the behavior documented in `docs/registry/endpoints.json` and `docs/registry/schemas.json`.
- Add a CI step to run `scripts/validate-registry.ps1`; fail if code and registry diverge.