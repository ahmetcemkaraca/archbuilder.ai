# ArchBuilder.AI - Tamamlanmayan Görevler (Mantık Sırasına Göre)

Bu dosya, ArchBuilder.AI projesinde henüz tamamlanmamış olan görevleri mantıksal sıralama ile içermektedir.

## 1. Temel Altyapı Tamamlama ✅ TAMAMLANDI

### 1.1 RAG Foundations (Devam Eden) ✅ TAMAMLANDI
- [x] P13-T2: Embedding provider selection (SBERT/Vertex/OpenAI) (@TODO §62)
- [x] P13-T3: Vector DB abstraction (@TODO §63)
- [x] RAGFlow dataset/document upload & parse akışının UI/desktop ile bağlanması

### 1.2 AI Orchestration Interfaces ✅ TAMAMLANDI
- [x] P16-T1: Common AI client interface (@TODO §72)
- [x] P16-T2: Vertex/OpenAI client skeletons (@TODO §72)
- [x] P16-T3: Confidence scoring fields (@TODO §76)

### 1.3 Model Selector ✅ TAMAMLANDI
- [x] P17-T1: AIModelSelector rules (@TODO §71)
- [x] P17-T2: Dynamic config source (@TODO §71)
- [x] P17-T3: Fallback hierarchy (@TODO §77)

### 1.4 Prompt Templates ✅ TAMAMLANDI
- [x] P19-T1: Versioned prompt templates (@TODO §74)
- [x] P19-T2: Validation prompts (@TODO §75)
- [x] P19-T3: Learn-from-corrections hooks (@TODO §79)

## 2. API ve Endpoints Tamamlama ✅ TAMAMLANDI

### 2.1 AI Endpoints ✅ TAMAMLANDI
- [x] P21-T1: POST /v1/ai/commands (@TODO §81)
- [x] P21-T2: GET /v1/ai/commands/{id} (@TODO §81)
- [x] P21-T3: Correlation ID handling (@TODO §88)

### 2.2 Document Endpoints ✅ TAMAMLANDI
- [x] P22-T1: Upload/list/delete endpoints (@TODO §82)
- [x] P22-T2: Size/type enforcement (@TODO §82)
- [x] P22-T3: Virus scan results handling (@TODO §82)

### 2.3 Projects and States ✅ TAMAMLANDI
- [x] P23-T1: Projects CRUD (@TODO §83)
- [x] P23-T2: State transitions (@TODO §83)
- [x] P23-T3: Audit log hooks (@TODO §83)

### 2.4 Subscription Endpoints ✅ TAMAMLANDI
- [x] P24-T1: /v1/subscriptions (@TODO §84)
- [x] P24-T2: Usage queries (@TODO §84)
- [x] P24-T3: Tier limits integration (@TODO §84)

### 2.5 WebSocket Progress ✅ TAMAMLANDI
- [x] P26-T1: WS server endpoint (@TODO §86)
- [x] P26-T2: Broadcast progress utility (@TODO §86)
- [x] P26-T3: Client message contract (@TODO §86)
- [x] Asenkron parse/index kuyruğu + ilerleme bildirimleri (WS/HTTP)

## 3. Validation ve Doğrulama ✅ TAMAMLANDI

### 3.1 Output Validation ✅ TAMAMLANDI
- [x] P20-T1: JSON schema validation (@TODO §75)
- [x] P20-T2: Geometric + code checks interfaces (@DYNAMO; @REVITAPI; @TODO §103)
- [x] P20-T3: Review queue wiring (@TODO §78)

### 3.2 analyze_project ✅ TAMAMLANDI
- [x] P18-T1: Implement `analyze_project` for both clients (@PROJECT §6.8; @TODO §73)
- [x] P18-T2: Input/output schemas (@TODO §74-75)
- [x] P18-T3: Tests for project analysis (@TODO §80)

### 3.3 RAG Tests and Metrics ✅ TAMAMLANDI
- [x] P15-T1: Recall/precision metrics harness (@TODO §68)
- [x] P15-T2: RAG test scenarios (@TODO §70)
- [x] P15-T3: Regional config and i18n hooks (@TODO §67)

## 4. Desktop ve UI Geliştirme ✅ TAMAMLANDI

### 4.1 Review & Approval ✅ TAMAMLANDI
- [x] P32-T1: Review screen components (@TODO §97)
- [x] P32-T2: Approve/reject actions (@TODO §97)
- [x] P32-T3: Notes feedback loop (@TODO §79)

### 4.2 Settings and Region ✅ TAMAMLANDI
- [x] P33-T1: Settings page (@TODO §98)
- [x] P33-T2: Region/language options (@TODO §67, §98)
- [x] P33-T3: Persist preferences (@TODO §98)

### 4.3 Error Recovery UX ✅ TAMAMLANDI
- [x] P34-T1: Global error boundary (@TODO §99)
- [x] P34-T2: Retry patterns (@TODO §99)
- [x] P34-T3: Telemetry signals (@TODO §100)

### 4.4 Regional Services ✅ TAMAMLANDI
- [x] P25-T1: Building codes endpoints (@TODO §85)
- [x] P25-T2: Regional config reads (@TODO §85)
- [x] P25-T3: Localization plumbing (@TODO §85)
- [x] VAL-03: Regional config/i18n bağları (P15-T3, P25-T2/T3, P33-T2)

## 5. Revit Plugin Geliştirme

### 5.1 Revit Plugin Basics
- [ ] P35-T2: Logging setup (@REVITAPI; @TODO §101)
- [ ] P35-T3: Config file (@REVITAPI; @TODO §109)

### 5.2 Transactions and Elements
- [ ] P36-T1: Transaction helpers (@REVITAPI §Transaction; @TODO §102)
- [ ] P36-T2: Wall/door/window helpers (@REVITAPI §Element Creation; @TODO §103)
- [ ] P36-T3: Parameter utilities (@REVITAPI §Parameters)

### 5.3 Project Analysis Export
- [ ] P37-T1: Extract counts/metrics (@REVITAPI; @TODO §104)
- [ ] P37-T2: Export clash data (@REVITAPI; @TODO §105)
- [ ] P37-T3: Wire to desktop app (@TODO §105)

### 5.4 Local Communication
- [ ] P38-T1: Named Pipes/HTTP client (@PROJECT §2.2.3; @TODO §106)
- [ ] P38-T2: Message contracts (@TODO §106)
- [ ] P38-T3: Error handling (@TODO §107)

### 5.5 Rollback and Safety
- [ ] P39-T1: Rollback helpers (@REVITAPI §Failures; @TODO §107)
- [ ] P39-T2: Validation before commit (@DYNAMO; @TODO §103)
- [ ] P39-T3: Failure paths (@REVITAPI §Error Handling)

## 6. Performans ve Ölçeklenebilirlik

### 6.1 Performance I
- [ ] P40-T1: Redis cache layer (@TODO §111)
- [ ] P40-T2: Query profiling and indexes (@TODO §112)
- [ ] P40-T3: Pool/timeout tuning (@TODO §113)

### 6.2 Performance II
- [ ] P41-T1: Queue for long tasks (@TODO §113)
- [ ] P41-T2: WS scaling (@TODO §114)
- [ ] P41-T3: AI request pool + caps (@TODO §116)

### 6.3 Health and Load
- [ ] P42-T1: Liveness/readiness endpoints (@TODO §117)
- [ ] P42-T2: Load tests setup (@TODO §118)
- [ ] P42-T3: CI perf gates (@TODO §119)

## 7. Güvenlik ve Gözlemlenebilirlik

### 7.1 Security I
- [ ] P43-T1: Input/output sanitization (@TODO §121)
- [ ] P43-T2: PII masking (@TODO §122)
- [ ] P43-T3: Secrets in logs prevention (@TODO §127)

### 7.2 Security II
- [ ] P44-T1: File abuse scenarios (@TODO §125)
- [ ] P44-T2: RAG result filters (@TODO §126)
- [ ] P44-T3: Audit retention policy (@TODO §123)

### 7.3 Observability I
- [ ] P45-T1: Prometheus metrics (@TODO §131)
- [ ] P45-T2: Grafana dashboards (@TODO §132)
- [ ] P45-T3: Error distribution reports (@TODO §136)

### 7.4 Observability II
- [ ] P46-T1: OpenTelemetry tracing (@TODO §134)
- [ ] P46-T2: Alert rules (@TODO §135)
- [ ] P46-T3: Ops runbooks (@TODO §138-140)

## 8. Deployment ve Ürün Hazırlığı

### 8.1 Release I
- [ ] P47-T1: Dockerfile + compose (@TODO §141)
- [ ] P47-T2: Helm/k8s manifests (@TODO §142)
- [ ] P47-T3: Staging environment (@TODO §143)

### 8.2 Release II
- [ ] P48-T1: Blue/green or canary strategy (@TODO §144)
- [ ] P48-T2: Rollback procedures (@TODO §145)
- [ ] P48-T3: Data protection steps (@TODO §145)

### 8.3 Product Readiness
- [ ] P49-T1: Public docs + demos (@TODO §148)
- [ ] P49-T2: Training content (@TODO §149)
- [ ] P49-T3: Sample projects (@TODO §149)

### 8.4 Production Checklist
- [ ] P50-T1: License/subscription checks (@TODO §147, §150)
- [ ] P50-T2: Support workflows (@TODO §146)
- [ ] P50-T3: Production acceptance checklist (@TODO §150)

## 9. Dokümantasyon ve Test

### 9.1 RAGFlow Entegrasyon Görevleri
- [ ] Testler: RAG endpointleri ve client (respx/mock)
- [ ] Dokümantasyon: docs/services, docs/api güncelle
- [ ] Registry: docs/registry/*.json genişletme (tamamlandı: temel)

### 9.2 Cross-Cutting Concerns
- [ ] XCUT-01: Local IPC (Named Pipes/HTTP) + sözleşmeler (P38-T1/T2/T3)
- [ ] XCUT-02: Rollback & safety yolları (P39-T1/T2/T3)
- [ ] XCUT-03: Performans I-II (Redis, profiling, pool/timeout, queue, scaling, pool caps) (P40/P41)
- [ ] XCUT-04: Health & load (liveness/readiness, load tests, CI perf gates) (P42)
- [ ] XCUT-05: Security I-II (sanitization, PII masking, abuse, filters, audit retention, secrets logs) (P43/P44)
- [ ] XCUT-06: Observability I-II (Prometheus, Grafana, tracing, alerts, runbooks, error dist.) (P45/P46)
- [ ] XCUT-07: Release I-II (Docker/compose, Helm/k8s, staging, blue/green, rollback, data protection) (P47/P48)
- [ ] XCUT-08: Product readiness (docs/demos, training, samples) + Production checklist (P49/P50)