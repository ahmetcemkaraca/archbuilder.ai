---
applyTo: "**/*"
description: Vibe Coding Checkpointing — checkpoints, rollback/rollforward, context rehydration, and session hygiene.
---

As Vibe Coding Operator:
- Maintain checkpoints at deterministic cadence (every 2 prompts or after risky edits)
- Rehydrate context before starting new work units
- Ensure reversible changes (commit small, isolate vertical slices)

Checkpoint Rules
1. Cadence: After every 2 prompts, update `version.md` with timestamp + summary
2. Artifacts: Commit `.mds/context/history/*`, `docs/registry/*.json`, changed sources
3. Consistency: CI must be green (lint/tests) before new prompt batch
4. Correlation: Include correlation ID or prompt index in commit message

Rollback / Rollforward
- Rollback: Use git revert for last faulty commit; never force-push in shared branches
- Hotfix path: Create `hotfix/<short-desc>` if recovery exceeds 15 minutes
- Data safety: For destructive migrations, require a dry-run and backup plan

Context Rehydration
1. Read `.mds/context/current-context.md` and `docs/registry/*.json`
2. Run `scripts/rehydrate-context.ps1`
3. Confirm open contracts (functions/endpoints/schemas) before coding

Session Hygiene
- One prompt = ~3 tasks; avoid scope creep
- Prefer JSON-only responses for machine-consumed outputs
- Never hardcode secrets; use `.env` and secret stores

Acceptance Checklist per Prompt Batch
- [ ] Lint/tests pass locally and in CI
- [ ] Registry updated for public contract changes
- [ ] `version.md` appended (2-prompt cadence)
- [ ] Context/state files updated in `.mds/context`

