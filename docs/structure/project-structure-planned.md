# ArchBuilder.AI – Planned Project Structure (Cloud + Desktop + Revit)

Bu doküman mevcut Docs içeriği ve yol haritasına göre tam üretim yapısını planlar. Kod/identifier İngilizce; yorum/log Türkçe; UI metinleri i18n.

## Goals
- Cloud Server (FastAPI, Python 3.12)
- Desktop App (WPF .NET Framework 4.8, MVVM)
- Revit Plugin (Command + Transaction)
- Registry-first (docs/registry/*.json) + tests
- Güvenlik, loglama, metrik, rate limit, human review


## Directory Tree (Planned)
```text
/                               # Repo root
├─ docs/
│  ├─ api/
│  ├─ architecture/
│  ├─ development/
│  ├─ modules/
│  ├─ registry/
│  ├─ services/
│  ├─ structure/
│  │  └─ project-structure-planned.md   # (this file)
│  └─ ...
│
├─ .mds/
│  ├─ context/
│  │  ├─ current-context.md
│  │  └─ project-structure.mdc          # structure context snapshot
│  └─ ...
│
├─ scripts/
│  ├─ validate-registry.ps1
│  ├─ rehydrate-context.ps1
│  ├─ run-vibe-coding.ps1
│  └─ generate-cursor-rules.ps1
│
├─ src/
│  ├─ cloud-server/
│  │  ├─ app/
│  │  │  ├─ main.py
│  │  │  ├─ core/
│  │  │  │  ├─ config.py
│  │  │  │  ├─ logging.py
│  │  │  │  ├─ exceptions.py
│  │  │  │  ├─ security/
│  │  │  │  │  ├─ auth.py
│  │  │  │  │  ├─ jwt.py
│  │  │  │  │  ├─ api_key.py
│  │  │  │  │  ├─ rate_limiter.py
│  │  │  │  │  └─ headers.py
│  │  │  │  ├─ ai/
│  │  │  │  │  ├─ interfaces.py
│  │  │  │  │  ├─ model_selector.py
│  │  │  │  │  ├─ prompts/
│  │  │  │  │  │  ├─ templates/
│  │  │  │  │  │  │  ├─ layout_generation_v1.md
│  │  │  │  │  │  │  └─ validation_v1.md
│  │  │  │  │  └─ validation/
│  │  │  │  │     ├─ schema_validator.py
│  │  │  │  │     ├─ geometry_validator.py
│  │  │  │  │     └─ building_code_validator.py
│  │  │  │  ├─ database/
│  │  │  │  │  ├─ base.py
│  │  │  │  │  ├─ session.py
│  │  │  │  │  ├─ models/
│  │  │  │  │  │  ├─ user.py
│  │  │  │  │  │  ├─ project.py
│  │  │  │  │  │  ├─ ai_command.py
│  │  │  │  │  │  ├─ subscription.py
│  │  │  │  │  │  └─ usage.py
│  │  │  │  │  └─ migrations/
│  │  │  │  │     ├─ env.py
│  │  │  │  │     └─ versions/
│  │  │  ├─ services/
│  │  │  │  ├─ ai_service.py
│  │  │  │  ├─ document_service.py
│  │  │  │  ├─ project_service.py
│  │  │  │  └─ rag_service.py
│  │  │  ├─ ai/
│  │  │  │  ├─ openai/
│  │  │  │  │  └─ client.py
│  │  │  │  └─ vertex/
│  │  │  │     └─ client.py
│  │  │  ├─ routers/
│  │  │  │  └─ v1/
│  │  │  │     ├─ ai.py
│  │  │  │     ├─ documents.py
│  │  │  │     ├─ projects.py
│  │  │  │     ├─ subscriptions.py
│  │  │  │     ├─ health.py
│  │  │  │     └─ websocket.py
│  │  │  ├─ middleware/
│  │  │  │  ├─ correlation.py
│  │  │  │  ├─ error_handler.py
│  │  │  │  └─ security_headers.py
│  │  │  ├─ schemas/
│  │  │  │  ├─ ai.py
│  │  │  │  ├─ documents.py
│  │  │  │  ├─ projects.py
│  │  │  │  ├─ subscriptions.py
│  │  │  │  └─ common.py
│  │  │  ├─ utils/
│  │  │  │  ├─ cache.py
│  │  │  │  ├─ websocket.py
│  │  │  │  └─ metrics.py
│  │  │  ├─ tests/
│  │  │  │  ├─ conftest.py
│  │  │  │  ├─ test_ai_endpoints.py
│  │  │  │  ├─ test_documents_endpoints.py
│  │  │  │  ├─ test_projects_endpoints.py
│  │  │  │  └─ test_registry_contracts.py
│  │  │  └─ __init__.py
│  │  ├─ requirements.txt
│  │  └─ pyproject.toml (optional)
│  │
│  ├─ desktop-app/
│  │  ├─ ArchBuilder.Desktop.sln
│  │  └─ ArchBuilder.Desktop/
│  │     ├─ ArchBuilder.Desktop.csproj
│  │     ├─ App.xaml
│  │     ├─ App.xaml.cs
│  │     ├─ Views/
│  │     │  ├─ MainWindow.xaml
│  │     │  └─ SettingsWindow.xaml
│  │     ├─ ViewModels/
│  │     │  ├─ MainViewModel.cs
│  │     │  └─ SettingsViewModel.cs
│  │     ├─ Services/
│  │     │  ├─ ApiClient.cs
│  │     │  ├─ WebSocketClient.cs
│  │     │  └─ LoggingService.cs
│  │     ├─ Models/
│  │     │  ├─ LayoutResult.cs
│  │     │  └─ ValidationResult.cs
│  │     ├─ Resources/
│  │     │  └─ Localization/
│  │     │     ├─ Strings.en.resx
│  │     │     └─ Strings.tr.resx
│  │     └─ Properties/
│  │        └─ AssemblyInfo.cs
│  │
│  └─ revit-plugin/
│     ├─ ArchBuilder.RevitAddin.sln
│     └─ ArchBuilder.RevitAddin/
│        ├─ ArchBuilder.RevitAddin.csproj
│        ├─ ArchBuilder.Revit.addin
│        ├─ Commands/
│        │  ├─ AILayoutCommand.cs
│        │  └─ ReviewQueueCommand.cs
│        ├─ Services/
│        │  ├─ LayoutExecutor.cs
│        │  ├─ DynamoGeometryEngine.cs
│        │  └─ FamilyManager.cs
│        ├─ Validation/
│        │  └─ GeometricValidator.cs
│        ├─ UI/
│        │  └─ AutoPlanRibbonPanel.cs
│        └─ Properties/
│           └─ AssemblyInfo.cs
│
├─ .github/
│  ├─ instructions/
│  └─ workflows/
│     └─ ci.yml
│
├─ project.md
├─ version.md
└─ vibecoding.md
```

## Governance & Workflow
- Branching: Her iş için feature branch açın; `master` korumalıdır. PR ile merge edin.
- Conventional Commits: feat, fix, docs, chore, refactor, test, perf, build, ci, revert.
- Rehydrate: Kodlamadan önce `.mds/context/current-context.md` ve `docs/registry/*.json` okuyun.
- Registry-first: Public contract değişiminde registry + en az 1 test güncelleyin.
- Versioning cadence: Her 2 promptta `version.md` güncelleyin (PowerShell: `Get-Date -Format 'yyyy-MM-dd HH:mm:ss'`). `scripts/run-vibe-coding.ps1` tercih edilir.
- Security: Secrets koda yazılmaz; `.env.example` ile belgeleyin.
- CI kalite kapıları: Lint/format + unit/integration + smoke/e2e yeşil olmadan sevkiyat yok.
- Takip: GitHub Projects panosu (Backlog → In Progress → Review → Done) ve PR bağlantıları.

## Registry Plan
- identifiers.json: module/exports listeleri (core, services, routers)
- endpoints.json: /v1/ai/commands, /v1/documents, /v1/projects, /v1/subscriptions, /v1/health, /v1/ws
- schemas.json: AICommandRequest/Response, LayoutResult, ValidationResult, Project, User, Subscription, Usage

Uygulama Notları:
- Doğrulama: `scripts/validate-registry.ps1` ile registry tutarlılığını CI içinde doğrulayın.
- Testler: Sözleşme değişiminde `src/cloud-server/app/tests/test_registry_contracts.py` altında test ekleyin/güncelleyin.
- Bağlam: `.mds/context/current-context.md` snapshot’ını güncel tutun.
- Mevcut durum: `docs/registry/*.json` şu an boş iskelet; feature sevkiyatlarıyla doldurulacaktır.

## Env Vars (Cloud)
OPENAI_API_KEY | OPENAI_BASE_URL (opsiyonel)
AZURE_OPENAI_API_KEY | AZURE_OPENAI_ENDPOINT | AZURE_OPENAI_API_VERSION | AZURE_OPENAI_DEPLOYMENT_TEXT | AZURE_OPENAI_DEPLOYMENT_CHAT
VERTEX_AI_PROJECT_ID | VERTEX_AI_LOCATION | GOOGLE_APPLICATION_CREDENTIALS (opsiyonel)
DATABASE_URL | REDIS_HOST | REDIS_PORT (opsiyonel) | SECRET_KEY | RATE_LIMIT_POLICIES | LOG_LEVEL | OTEL_EXPORTER_OTLP_ENDPOINT (opsiyonel)

## API Base URL
- Production: `https://api.archbuilder.app/v1`
- Not: Versiyonlu patika zorunludur (`/v1`).

## Revit 2026 Notları
- Hedef çatı: .NET Framework 4.8 (Revit 2026 desteği doğrultusunda). Yeni hedefler duyurulursa proje ayarları güncellenecek.
- Transaction yönetimi: Komutlar kısa ve idempotent olmalı; `Transaction` kapsamları sınırlı tutulmalı.
- Dynamo entegrasyonu: `DynamoGeometryEngine` içinde geometrik dönüşümler izole edilmeli.
- Ribbon/UI: `AutoPlanRibbonPanel` erişilebilir ve yalın; human review kuyruğu ile tamamlanır.

## Notes
- Secrets asla koda; .env.example ile belgeleyin.
- Contract değişince registry + test güncelleyin.
- structlog JSON log, Prometheus metrik, OTel izleme.
- Redis cache, connection pool, timeouts.
