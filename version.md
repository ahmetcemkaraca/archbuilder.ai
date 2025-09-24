## Phase 9 – Revit Add-in (Build Phases)

- Added `PhaseManager` for robust phase operations (create/list/set).
- Implemented `InitializePhaseNineCommand` with correlation ID journaling.
- Wired Ribbon button (AutoPlan AI → Phase 9).
- i18n resources for all UI texts (TR), removed hardcoded strings.
- Revit 2026 compatibility checks and safe null-guards.
- Smoke test doc: `docs/services/project-service.md`.

Timestamp: (to be set via PowerShell `Get-Date -Format 'yyyy-MM-dd HH:mm:ss'` during release)

## 0.1.0 — Initialized governance and memory (date pending)

- Added registry (identifiers/endpoints/schemas) and versioned context files
- Updated Copilot and Universal Agent instructions for language, registry, and cadence (2 prompts)
- Added validation scripts and Windows CI to enforce registry/context
- Added new prompts: integrate-new-feature, extend-api-contract, persist-context, refactor-with-contracts, conflict-resolution

## 0.1.1  Rules updated and roadmap added (2025-09-24 11:37:37)
- Synced legacy instructions into .github/instructions
- Updated copilot-instructions (provider naming, Python 3.12, anti-bloat) 
- Expanded CI with Python tests/lint/coverage
- Added .mds/Roadmap.md, .mds/Todo.md (150 steps), .mds/todoprompt.md (50 prompts)
- Archived .github/eski into .github/_archive

## 0.1.2  Pruned unused instructions (2025-09-24 11:52:07)
- Removed platform-agnostic/mobile/web backends not used (android, ios, flutter, go, node, maui, prisma)
- Kept WPF/FastAPI/Revit-focused instructions only

- 2025-09-24 14:18:52 Structure docs added: docs/structure/project-structure-planned.md, .mds/context/project-structure.mdc

## 0.1.3  Project structure scope aligned (2025-09-24 14:33:06)
- Removed website subtree from planned structure and goal list
- Consolidated governance/workflow, registry notes, env matrix, API URL, and Revit 2026 notes in `docs/structure/project-structure-planned.md`- 2025-09-24 15:49:44 | Added cursortodo.md aligned with .mds docs and prompts
## auto  completed P01-T3, P02-T3, P03-T3 2025-09-24 17:08:13
- Python 3.12 pinned; context snapshot; prompt library organized
## auto  completed P04-P06 step1 2025-09-24 17:12:41
- FastAPI app + /health; logging+exceptions; auth foundations
## auto  P04-P06 finalized 2025-09-24 17:13:37
- Rehydrate fix; JWT cfg; registry health schema
## auto  rehydrate fixed 2025-09-24 17:14:43
- context snapshot ok
## auto  rehydrate markers adjusted 2025-09-24 17:15:23
- context snapshot ok
## auto  rehydrate root fixed 2025-09-24 17:15:49
- context snapshot ok
## auto  snapshot ok 2025-09-24 17:15:58
## auto  completed P07-P09 2025-09-24 17:20:56
- RBAC, rate limit, security headers, DB+Alembic + tables/migrations
## auto  completed P06-T2/T3 and P10 2025-09-24 17:27:50
- Auth endpoints; storage + chunked upload
## auto  completed P11-P12 2025-09-24 17:30:56
- Virus scan + validation + metadata; PDF/CAD preprocess; signed URL
- 2025-09-24 19:40:40 - TODO reordered into Pyramid Execution Order; removed Prompt sections; kept Cross-References and Done Log.
## 0.1.4  Phase 1 completed (2025-09-24 20:03:51)
## 0.1.5  Phase 2 completed (2025-09-24 20:20:20)
## 0.1.6  Phase 3 completed (2025-09-24 20:26:19)
## 0.1.7  Phase 4 completed (2025-09-24 20:31:00)
## 0.1.8  Phase 5 completed (2025-09-24 20:35:37)
## 0.1.9  Phase 6 completed (2025-09-24 20:40:04)
## 0.1.10  Phase 7 completed (2025-09-24 20:44:44)
## 0.1.11  Fixes & optional improvements (2025-09-24 20:55:18)
- AI router included in app; AI endpoints now require API key
- Registry headers added for AI endpoints (correlation headers)
- RAGFlow client: basic retry/backoff on 429/503
- README: added env keys guidance (since .env.example is ignored)
- Validation: Added /v1/ai/validate endpoint (schema/geometry/building-code)
- Registry updated for ValidationRequest/Response; tests added
- Context rehydrated; registry validation OK
- AI Endpoints: Added POST /v1/ai/commands and GET /v1/ai/commands/{id}
- Schemas/Identifiers/Endpoints updated; simple DB-backed storage via AIService
- Tests for AI commands (smoke) added; context rehydrated; validation OK
- RAG Base: Added text chunking utility (`app.ai.chunking`) with tests
- Registry: identifiers updated; `ChunkingConfig` schema added
- Context rehydrated; registry validation OK
- Storage APIs: tests added for upload init/chunk/complete
- Registry identifiers: added `app.routers.v1.storage`
- Context rehydrated; registry validation OK
- Registry: Documented DB schemas (users, projects, ai_commands, subscriptions, usage)
- Registry: Added RAG tables (rag_dataset_links, rag_jobs, rag_document_links)
- Tests: Registry contracts assert DB schemas presence
- Context: Rehydrated snapshots
- Correlation ID: Middleware sets X-Correlation-ID/X-Request-ID on responses
- Logging: structlog contextvars merge + correlation_id binding
- RAGFlow: Propagate X-Correlation-ID to upstream requests
- Registry: Endpoints document correlation headers; tests added
- Docs: Provider naming normalized (GitHub Models → OpenAI/Azure OpenAI)
- Security docs: Defaults/gaps section added (sanitization, PII masking, secrets in logs)
- Performance docs: Targets aligned with architecture (p50/p95/p99, AI/complex)
- Registry/context: Rehydrate executed; validation script reviewed

## 0.1.12  Cloud API refinements (2025-09-24 22:32:12)
- Fixed RAG router Request typing and storage auth dependency
- Added WebSocket manager utilities; progress broadcast helpers
- Updated chunking to support small max_chars for tests
- Requirements: added slowapi, python-multipart, pytest, pytest-asyncio
- Tests: smoke green (3 passed, 9 skipped); registry validation OK

## 0.1.13  Validation & Analysis Systems (2025-09-24 22:57:22)
- JSON Schema Validation: Comprehensive validation service with geometric/code checks
- Geometric Validator: Revit API integration for room/dimension/structure validation
- Code Validator: Regional building codes (TR/US/EU) with compliance scoring
- Review Queue System: Complete workflow for approve/reject/feedback loops
- RAG Metrics Service: Precision/recall/F1 metrics harness with test scenarios
- Regional Config Service: i18n support (TR/EN) with building codes and units
- Validation Router: RESTful endpoints for all validation types
- Database Models: ValidationResult and ReviewItem with proper indexing
- Registry Updates: Added 10 new modules, 8 endpoints, 4 schemas
- Requirements: Added jsonschema, sqlalchemy, asyncpg for validation support

## 0.1.14  Desktop UI & Settings Enhancement (2025-09-24 23:15:45)
- Review Window: Complete XAML UI with validation results display and action buttons
- Review ViewModel: Full MVVM implementation with approve/reject/revision commands
- Settings Window: Advanced tabbed interface with General/UI/Advanced sections
- Settings ViewModel: Comprehensive settings management with regional/language support
- Regional Configuration: TR/US/EU building codes with localized building types
- Language Support: TR/EN localization with dynamic building type updates
- Validation Integration: Settings for geometric/code validation preferences
- Performance Settings: Cache size, concurrent requests, monitoring options
- Debug Settings: Log levels, debug mode, telemetry configuration
- UI Settings: Theme selection, animations, window behavior preferences