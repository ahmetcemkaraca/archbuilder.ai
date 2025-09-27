---
applyTo: "**"
description: Universal agent operating rules for autonomous, Lovable-style delivery.
---
Use the Universal Agent steering files as the operating system:
- Rehydrate context from `.mds/context/current-context.md` and `docs/registry/*.json` first.
- Plan → Validate → Implement → Test → Ship (2-prompt cadence for `version.md`).
- Prefer vertical slices with tests. Keep CI green. No secrets in code.
- Document env vars in `.env.example` and reference in README.
- Summarize changes and next TODOs in `.mds/Todo.md` each session.
- File operations: Prefer agent tools for file/dir edits and creation; avoid manual/prompt-only steps.

Registry & Persistent Context (Mandatory)
- Maintain a project registry under `docs/registry/`:
  - `identifiers.json` for modules/exports/variables/config keys
  - `endpoints.json` for API contracts (method, path, schemas, auth, version)
  - `schemas.json` for data models, DB tables, migrations
- Maintain versioned context under `.mds/context/`:
  - `current-context.md` — active summary of key contracts and variables
  - `history/NNNN.md` — append a per-session summary before summarizing/clearing context
- Before coding or after context reset: rehydrate by reading `docs/registry/*.json` and `.mds/context/current-context.md`.
- Use `scripts/run-vibe-coding.ps1` to orchestrate prompts; it updates context and `version.md` automatically every 2 prompts.
- Do not change public contracts without updating the registry and adding at least one test.

When starting from natural language
- Synthesize EARS-style requirements within `.mds/Todo.md` tasks.
- Target stack is fixed for this project: Desktop (WPF), Cloud (FastAPI Py 3.12), Revit Plugin.
- Create an ordered, dependency-aware task list with verifiable outcomes (ensure registry updates).

Security and quality
- Apply OWASP basics; input validation; structured logs; error taxonomy; feature flags as needed.
- Provide minimal deploy + rollback instructions for local and one cloud target.

Teach/Coach mode
- Kullanıcının yanlış varsayımlarını nazikçe işaretle, kısa nedenini açıkla ve güvenli/uygulanabilir 2–3 alternatif yol öner.
- Alternatifler için beklenen fayda/riski ve karmaşıklığı kısaca belirt; bir “önerilen yol” seç.

Language & output policy
- Code and identifiers must be in English.
- In-code comments and log messages must be in English.
- UI text must be provided via i18n (default English then Turkish). Do not hardcode strings in components.
- Chat responses to the user must be in Turkish, concise and practical.

Versioning cadence
- Local override: After every 2 prompts/sessions of significant work, update `version.md` (PowerShell stamp: `Get-Date -Format 'yyyy-MM-dd HH:mm:ss'`). Prefer `scripts/run-vibe-coding.ps1`.

Error log (hata.md)
- If the user proposes an incorrect/unsafe/illogical idea, append a new entry to `hata.md` with: date/time, the mistaken idea (verbatim), the short diagnosis (why it’s wrong), and the recommended correct solution.

As Security:
- Map trust boundaries; add STRIDE notes; enforce input validation and output encoding.
- Ensure no secrets in code; document rotation and vault usage; run dependency audits.
- Recommend authn/authz patterns; add rate limiting and abuse controls where relevant.
