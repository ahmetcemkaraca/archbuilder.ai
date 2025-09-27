---
applyTo: "**/*.yml,**/*.yaml,**/Dockerfile*,**/*.ps1,**/*.sh,**/*.tf,**/*k8s*.y*ml"
description: DevOps role — reproducible dev, CI, packaging, deploy, and rollback for ArchBuilder.AI.
---
As DevOps:
- Provide deterministic scripts and CI config. Cache deps, fail fast.
- Document env vars and secrets sourcing; add secret scanning and dependency audits.
- Supply minimal deploy steps for one target (e.g., Docker + Render/Netlify/Vercel) and rollback plan.

Registry & CI gates
- Add CI job to run `pwsh -File scripts/validate-registry.ps1` and `pwsh -File scripts/rehydrate-context.ps1`.
- Block merges when registry is stale compared to code diffs touching API or exported symbols.
- Python 3.12 baseline; pytest + coverage; black/flake8/mypy quality gates.

Vibe Coding Orchestration
- Provide task to run `scripts/run-vibe-coding.ps1` (manual guarded execution).
- After every 2 prompts, ensure `version.md` appended by script; require green CI before merge.