# Cursor TODO — ArchBuilder.AI (Checkable)

Bu dosya, Cursor içinde işaretlenebilir (checkbox) görev listesi olarak kullanılacaktır. Kod/identifier İngilizce; yorum/log Türkçe; UI metinleri i18n. Her görev CI kalite kapılarına ve güvenlik kurallarına uygun ilerlemelidir.

- Legend: [ ] pending, [x] done
- ID format: PXX-TY (örn. P04-T2)
- Doküman referansları:
  - @DYNAMO: `.mds/DYNAMO_DOCUMENTATION.md`
  - @REVITAPI: `.mds/REVIT_API_DOCUMENTATION.md`
  - @PROJECT: `.mds/project.md`
  - @ROADMAP: `.mds/Roadmap.md`
  - @TODO: `.mds/Todo.md`
  - @PROMPTS: `.mds/todoprompt.md`
- CI Gating: Lint/test/coverage yeşil; registry doğrulama; secrets yok; `version.md` 2 promptta bir güncellenecek.

---

## Entrypoint (Next Actions)
- [ ] P04-T1: Create FastAPI app `src/cloud-server/app/main.py` (+ /health) (@PROMPTS §Prompt 04; @TODO §21-22)
- [ ] P05-T1: Add `pydantic-settings` config `app/core/config.py` (@PROMPTS §Prompt 05; @TODO §25)
- [ ] P06-T1: Implement password hashing (bcrypt) `app/core/security/` (@PROMPTS §Prompt 06; @TODO §41)

---

## Prompt 01 — Standards and Providers (@PROMPTS)
- [ ] P01-T1: Sync `.github/instructions/*` and fill gaps (@PROJECT §6.1-6.10; @ROADMAP §Faz 0)
- [ ] P01-T2: Fix AI provider naming (replace ambiguous "GitHub Models") in docs (@PROJECT §6.2)
- [ ] P01-T3: Pin Python to 3.12 in docs and CI (@ROADMAP §Faz 0; @PROMPTS §Prompt 01)

## Prompt 02 — Versioning and Registry (@PROMPTS)
- [ ] P02-T1: Align versioning cadence with `version.md` process (@ROADMAP §Faz 0)
- [ ] P02-T2: Review `scripts/validate-registry.ps1` and registry JSONs (@docs/registry)
- [ ] P02-T3: Initialize `.mds/context/*` snapshot update flow (@PROJECT §Governance)

## Prompt 03 — Security & Performance Baselines (@PROMPTS)
- [ ] P03-T1: Review security defaults and list gaps (@PROJECT §8; @ROADMAP §Faz 6)
- [ ] P03-T2: Update performance targets to realistic bounds (@PROJECT §9)
- [ ] P03-T3: Organize prompt library `app/core/ai/prompts/*` (@PROMPTS §Prompt 03)

## Prompt 04 — FastAPI App Basics (@PROMPTS)
- [ ] P04-T1: Create FastAPI app `app/main.py` with `/health` (@TODO §21-22)
- [ ] P04-T2: Set structlog JSON logging `app/core/logging.py` (@TODO §26)
- [ ] P04-T3: Global exception handler + standard response schema (@TODO §27)

## Prompt 05 — Config and Exceptions (@PROMPTS)
- [ ] P05-T1: `pydantic-settings` config `core/config.py` (@TODO §25)
- [ ] P05-T2: Implement global error handler (@TODO §27)
- [ ] P05-T3: Standardize response envelopes (@TODO §27, §87)

## Prompt 06 — Auth Foundations (@PROMPTS)
- [ ] P06-T1: Password hashing (bcrypt) and validator (@TODO §41)
- [ ] P06-T2: JWT issuance/refresh flow (@TODO §42)
- [ ] P06-T3: API Key issuance/validation (@TODO §43)

## Prompt 07 — RBAC and Rate Limits (@PROMPTS)
- [ ] P07-T1: RBAC roles + decorators (@TODO §44)
- [ ] P07-T2: slowapi rate limiting (@TODO §45)
- [ ] P07-T3: Security headers (CSP/HSTS) middleware (@TODO §46)

## Prompt 08 — Database Setup (@PROMPTS)
- [ ] P08-T1: SQLAlchemy + Alembic bootstrap (@TODO §31)
- [ ] P08-T2: Users table + migration (@TODO §32)
- [ ] P08-T3: Projects table + migration (@TODO §33)

## Prompt 09 — Command History and Usage (@PROMPTS)
- [ ] P09-T1: AI command history table + migration (@TODO §34)
- [ ] P09-T2: Subscriptions/usage tables + migration (@TODO §35)
- [ ] P09-T3: Indexes and foreign keys (@TODO §36)

## Prompt 10 — Storage Strategy (@PROMPTS)
- [ ] P10-T1: Temp/persistent storage layout (@TODO §53)
- [ ] P10-T2: Chunked upload support (@TODO §54)
- [ ] P10-T3: File lifecycle policies (@TODO §58)

## Prompt 11 — Virus Scanning & Validation (@PROMPTS)
- [ ] P11-T1: Integrate ClamAV/alt. API in upload pipeline (@PROJECT §6.5; @TODO §52)
- [ ] P11-T2: Size/type validation (@TODO §51)
- [ ] P11-T3: Content metadata extraction (@TODO §57)

## Prompt 12 — PDF/OCR & CAD Preprocess (@PROMPTS)
- [ ] P12-T1: PDF/OCR pipeline interface (@TODO §55)
- [ ] P12-T2: DWG/DXF/IFC preprocess interface (@TODO §56)
- [ ] P12-T3: Signed URL (optional) (@TODO §59)

## Prompt 13 — RAG Foundations (@PROMPTS)
- [ ] P13-T1: Text chunking strategy (@TODO §61)
- [ ] P13-T2: Embedding provider selection (SBERT/Vertex/OpenAI) (@TODO §62)
- [ ] P13-T3: Vector DB abstraction (@TODO §63)

## Prompt 14 — Indexing and Search (@PROMPTS)
- [ ] P14-T1: Index build/update flow (@TODO §64)
- [ ] P14-T2: Hybrid search API (keyword+dense) (@TODO §65)
- [ ] P14-T3: Missing-data handling (@TODO §69)

## Prompt 15 — RAG Tests and Metrics (@PROMPTS)
- [ ] P15-T1: Recall/precision metrics harness (@TODO §68)
- [ ] P15-T2: RAG test scenarios (@TODO §70)
- [ ] P15-T3: Regional config and i18n hooks (@TODO §67)

## Prompt 16 — AI Orchestration Interfaces (@PROMPTS)
- [ ] P16-T1: Common AI client interface (@TODO §72)
- [ ] P16-T2: Vertex/OpenAI client skeletons (@TODO §72)
- [ ] P16-T3: Confidence scoring fields (@TODO §76)

## Prompt 17 — Model Selector (@PROMPTS)
- [ ] P17-T1: AIModelSelector rules (@TODO §71)
- [ ] P17-T2: Dynamic config source (@TODO §71)
- [ ] P17-T3: Fallback hierarchy (@TODO §77)

## Prompt 18 — analyze_project (@PROMPTS)
- [ ] P18-T1: Implement `analyze_project` for both clients (@PROJECT §6.8; @TODO §73)
- [ ] P18-T2: Input/output schemas (@TODO §74-75)
- [ ] P18-T3: Tests for project analysis (@TODO §80)

## Prompt 19 — Prompt Templates (@PROMPTS)
- [ ] P19-T1: Versioned prompt templates (@TODO §74)
- [ ] P19-T2: Validation prompts (@TODO §75)
- [ ] P19-T3: Learn-from-corrections hooks (@TODO §79)

## Prompt 20 — Output Validation (@PROMPTS)
- [ ] P20-T1: JSON schema validation (@TODO §75)
- [ ] P20-T2: Geometric + code checks interfaces (@DYNAMO; @REVITAPI; @TODO §103)
- [ ] P20-T3: Review queue wiring (@TODO §78)

## Prompt 21 — AI Endpoints (@PROMPTS)
- [ ] P21-T1: POST /v1/ai/commands (@TODO §81)
- [ ] P21-T2: GET /v1/ai/commands/{id} (@TODO §81)
- [ ] P21-T3: Correlation ID handling (@TODO §88)

## Prompt 22 — Document Endpoints (@PROMPTS)
- [ ] P22-T1: Upload/list/delete endpoints (@TODO §82)
- [ ] P22-T2: Size/type enforcement (@TODO §82)
- [ ] P22-T3: Virus scan results handling (@TODO §82)

## Prompt 23 — Projects and States (@PROMPTS)
- [ ] P23-T1: Projects CRUD (@TODO §83)
- [ ] P23-T2: State transitions (@TODO §83)
- [ ] P23-T3: Audit log hooks (@TODO §83)

## Prompt 24 — Subscription Endpoints (@PROMPTS)
- [ ] P24-T1: /v1/subscriptions (@TODO §84)
- [ ] P24-T2: Usage queries (@TODO §84)
- [ ] P24-T3: Tier limits integration (@TODO §84)

## Prompt 25 — Regional Services (@PROMPTS)
- [ ] P25-T1: Building codes endpoints (@TODO §85)
- [ ] P25-T2: Regional config reads (@TODO §85)
- [ ] P25-T3: Localization plumbing (@TODO §85)

## Prompt 26 — WebSocket Progress (@PROMPTS)
- [ ] P26-T1: WS server endpoint (@TODO §86)
- [ ] P26-T2: Broadcast progress utility (@TODO §86)
- [ ] P26-T3: Client message contract (@TODO §86)

## Prompt 27 — Desktop App Skeleton (@PROMPTS)
- [ ] P27-T1: Solution + MVVM setup (@TODO §91)
- [ ] P27-T2: Theming (accessible, modern Windows) (@TODO §92)
- [ ] P27-T3: Logging integration (@TODO §100)

## Prompt 28 — Desktop Auth (@PROMPTS)
- [ ] P28-T1: Auth flow UI + storage (@TODO §93-95)
- [ ] P28-T2: API token wiring (@TODO §93)
- [ ] P28-T3: Error feedback (@TODO §99)

## Prompt 29 — Desktop Projects (@PROMPTS)
- [ ] P29-T1: List/create projects UI (@TODO §94)
- [ ] P29-T2: Project detail view stub (@TODO §94)
- [ ] P29-T3: Loading states and errors (@TODO §99)

## Prompt 30 — Desktop Files (@PROMPTS)
- [ ] P30-T1: File picker + validations (@TODO §95-96)
- [ ] P30-T2: Upload progress UI (@TODO §95)
- [ ] P30-T3: Result notifications (@TODO §99)

## Prompt 31 — Desktop AI Command (@PROMPTS)
- [ ] P31-T1: Command input and run (@TODO §96)
- [ ] P31-T2: WS progress display (@TODO §96)
- [ ] P31-T3: Result viewer stub (@TODO §96)

## Prompt 32 — Review & Approval (@PROMPTS)
- [ ] P32-T1: Review screen components (@TODO §97)
- [ ] P32-T2: Approve/reject actions (@TODO §97)
- [ ] P32-T3: Notes feedback loop (@TODO §79)

## Prompt 33 — Settings and Region (@PROMPTS)
- [ ] P33-T1: Settings page (@TODO §98)
- [ ] P33-T2: Region/language options (@TODO §67, §98)
- [ ] P33-T3: Persist preferences (@TODO §98)

## Prompt 34 — Error Recovery UX (@PROMPTS)
- [ ] P34-T1: Global error boundary (@TODO §99)
- [ ] P34-T2: Retry patterns (@TODO §99)
- [ ] P34-T3: Telemetry signals (@TODO §100)

## Prompt 35 — Revit Plugin Basics (@PROMPTS)
- [ ] P35-T1: Ribbon + command skeleton (@REVITAPI; @TODO §101)
- [ ] P35-T2: Logging setup (@REVITAPI; @TODO §101)
- [ ] P35-T3: Config file (@REVITAPI; @TODO §109)

## Prompt 36 — Transactions and Elements (@PROMPTS)
- [ ] P36-T1: Transaction helpers (@REVITAPI §Transaction; @TODO §102)
- [ ] P36-T2: Wall/door/window helpers (@REVITAPI §Element Creation; @TODO §103)
- [ ] P36-T3: Parameter utilities (@REVITAPI §Parameters)

## Prompt 37 — Project Analysis Export (@PROMPTS)
- [ ] P37-T1: Extract counts/metrics (@REVITAPI; @TODO §104)
- [ ] P37-T2: Export clash data (@REVITAPI; @TODO §105)
- [ ] P37-T3: Wire to desktop app (@TODO §105)

## Prompt 38 — Local Communication (@PROMPTS)
- [ ] P38-T1: Named Pipes/HTTP client (@PROJECT §2.2.3; @TODO §106)
- [ ] P38-T2: Message contracts (@TODO §106)
- [ ] P38-T3: Error handling (@TODO §107)

## Prompt 39 — Rollback and Safety (@PROMPTS)
- [ ] P39-T1: Rollback helpers (@REVITAPI §Failures; @TODO §107)
- [ ] P39-T2: Validation before commit (@DYNAMO; @TODO §103)
- [ ] P39-T3: Failure paths (@REVITAPI §Error Handling)

## Prompt 40 — Performance I (@PROMPTS)
- [ ] P40-T1: Redis cache layer (@TODO §111)
- [ ] P40-T2: Query profiling and indexes (@TODO §112)
- [ ] P40-T3: Pool/timeout tuning (@TODO §113)

## Prompt 41 — Performance II (@PROMPTS)
- [ ] P41-T1: Queue for long tasks (@TODO §113)
- [ ] P41-T2: WS scaling (@TODO §114)
- [ ] P41-T3: AI request pool + caps (@TODO §116)

## Prompt 42 — Health and Load (@PROMPTS)
- [ ] P42-T1: Liveness/readiness endpoints (@TODO §117)
- [ ] P42-T2: Load tests setup (@TODO §118)
- [ ] P42-T3: CI perf gates (@TODO §119)

## Prompt 43 — Security I (@PROMPTS)
- [ ] P43-T1: Input/output sanitization (@TODO §121)
- [ ] P43-T2: PII masking (@TODO §122)
- [ ] P43-T3: Secrets in logs prevention (@TODO §127)

## Prompt 44 — Security II (@PROMPTS)
- [ ] P44-T1: File abuse scenarios (@TODO §125)
- [ ] P44-T2: RAG result filters (@TODO §126)
- [ ] P44-T3: Audit retention policy (@TODO §123)

## Prompt 45 — Observability I (@PROMPTS)
- [ ] P45-T1: Prometheus metrics (@TODO §131)
- [ ] P45-T2: Grafana dashboards (@TODO §132)
- [ ] P45-T3: Error distribution reports (@TODO §136)

## Prompt 46 — Observability II (@PROMPTS)
- [ ] P46-T1: OpenTelemetry tracing (@TODO §134)
- [ ] P46-T2: Alert rules (@TODO §135)
- [ ] P46-T3: Ops runbooks (@TODO §138-140)

## Prompt 47 — Release I (@PROMPTS)
- [ ] P47-T1: Dockerfile + compose (@TODO §141)
- [ ] P47-T2: Helm/k8s manifests (@TODO §142)
- [ ] P47-T3: Staging environment (@TODO §143)

## Prompt 48 — Release II (@PROMPTS)
- [ ] P48-T1: Blue/green or canary strategy (@TODO §144)
- [ ] P48-T2: Rollback procedures (@TODO §145)
- [ ] P48-T3: Data protection steps (@TODO §145)

## Prompt 49 — Product Readiness (@PROMPTS)
- [ ] P49-T1: Public docs + demos (@TODO §148)
- [ ] P49-T2: Training content (@TODO §149)
- [ ] P49-T3: Sample projects (@TODO §149)

## Prompt 50 — Production Checklist (@PROMPTS)
- [ ] P50-T1: License/subscription checks (@TODO §147, §150)
- [ ] P50-T2: Support workflows (@TODO §146)
- [ ] P50-T3: Production acceptance checklist (@TODO §150)

---

## Cross-References (Hızlı Erişim)
- DYNAMO kritik kalıplar: Parametrik geometri, Unit dönüşümleri, Data-Shapes UI (@DYNAMO)
- Revit API kritik kalıplar: Transaction, Element creation, Failure handling, Selection (@REVITAPI)
- Mimari kararlar ve açıklamalar: @PROJECT §6.x; Performans §9; Güvenlik §8
- Yol haritası fazları ve sırası: @ROADMAP
- Ayrıntılı 150 adım: @TODO
- Prompt odak özetleri: @PROMPTS

---

## Done Log (kısa not)
- [ ] 2025-09-24: cursortodo.md oluşturuldu; giriş görevleri eklendi (Entrypoint)
