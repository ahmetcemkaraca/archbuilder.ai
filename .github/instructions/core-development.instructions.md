---
applyTo: "**/*"
description: Core Development Rules — unified workflow, registry management, context handling, and quality standards.
---

# ArchBuilder.AI Core Development Standards

## 🔧 Development Workflow (Universal)

### MANDATORY Issue-First Workflow:
**Every task MUST start with an issue and follow GitFlow**

1. **Create GitHub Issue First**:
   ```bash
   # Create issue via GitHub CLI or web interface
   gh issue create --title "feat: PostgreSQL connection pool optimization" --body "Implement connection pooling optimization as per TODO.md task 5"
   ```

2. **Commit Current State**:
   ```bash
   # Always commit current state before starting new work
   git add .
   git commit -m "checkpoint: save current progress before task #<issue-number>"
   git push origin <current-branch>
   ```

3. **Create Feature Branch**:
   ```bash
   # GitFlow pattern: feature/<issue-number>-<kebab-title>
   git checkout develop
   git pull origin develop
   git checkout -b feature/<issue-number>-postgresql-connection-optimization
   ```

### Before ANY Implementation:
1. **Issue Assignment** - Assign the GitHub issue to yourself
2. **Context Rehydration** - Read `.mds/context/current-context.md` and `docs/registry/*.json` first
3. **Plan → Validate → Implement → Test → Ship** (1-2 prompt cadence)
4. **Vertical Slices** - Prefer small, testable implementations with clear boundaries
5. **Registry Updates** - Plan contract changes before coding

### Registry & Persistent Context (Mandatory)

#### Required Files/Directories:
```
docs/registry/
├── identifiers.json        # modules, exports, variables, config keys
├── endpoints.json         # API contracts (method, path, schemas, auth, version)
├── schemas.json          # data models, DB tables, migrations
├── permissions.json      # access control policies, roles, permissions
├── hooks.json           # webhooks, event subscriptions
├── secrets.json         # sensitive information management
├── configuration.json   # application configuration settings
└── logging.json        # logging formats and levels

.mds/
├── Todo.md                # task list with EARS-style requirements
└── context/
    ├── current-context.md    # short technical summary of active contracts
    └── history/             # versioned session summaries (0001.md, 0002.md)
```

#### Registry Management Rules:
1. **After any change** that adds/renames/deletes functions, variables, endpoints, or schemas → update registry JSONs in same commit
2. **Before coding** or after context reset → rehydrate by reading registry files + current-context.md
3. **At session end** → append summary to `.mds/context/history/<NNNN>.md` and refresh `current-context.md`
4. **Never ship** code that changes public contracts without updating registry + adding tests

#### Minimal Schema Examples:
```json
// identifiers.json
{
  "modules": [
    {
      "name": "user.service",
      "exports": ["createUser", "getUserById"],
      "variables": ["USER_CACHE_TTL"],
      "configKeys": ["USER_SERVICE_URL"]
    }
  ]
}

// endpoints.json
{
  "endpoints": [
    {
      "name": "CreateUser",
      "method": "POST", 
      "path": "/api/users",
      "inputSchema": "CreateUserRequest@v1",
      "outputSchema": "User@v1",
      "auth": "required"
    }
  ]
}
```

### Version Management & Checkpointing

#### Checkpoint Rules:
- **Cadence**: After every 1-2 prompts, update `version.md` with timestamp + summary
- **Artifacts**: Commit `.mds/context/history/*`, `docs/registry/*.json`, changed sources
- **Consistency**: CI must be green (lint/tests) before new prompt batch
- **Correlation**: Include correlation ID or prompt index in commit message

#### PowerShell Commands:
```powershell
# Update version.md with timestamp
Get-Date -Format 'yyyy-MM-dd HH:mm:ss'

# Validate registry and rehydrate context
pwsh -File scripts/validate-registry.ps1
pwsh -File scripts/rehydrate-context.ps1
pwsh -File scripts/run-vibe-coding.ps1  # Orchestrates prompts + updates
```

#### Rollback/Rollforward:
- **Rollback**: Use `git revert` for faulty commits (never force-push on shared branches)
- **Hotfix**: Create `hotfix/<short-desc>` if recovery > 15 minutes
- **Data Safety**: Require dry-run + backup plan for destructive migrations

### Language & Output Policy (Project-wide)

This policy overrides any conflicting statements:

- **Code and identifiers**: English
- **In-code comments and log messages**: English
- **UI text**: English by default via i18n/locale files (Turkish translation optional); never hardcode in components
- **Chat responses**: Turkish, concise and actionable

#### Examples:
```json
// Frontend i18n
{
  "common": { "save": "Kaydet", "cancel": "İptal" }
}
```

```python
# Backend logging
# Kullanıcı kaydı başarıyla tamamlandı
logger.info({"userId": user_id}, "Kullanıcı oluşturuldu")
```

### Quality & Security Standards

#### Before Coding Checklist:
- [ ] Read relevant instruction files based on file patterns
- [ ] Rehydrate context from registry + current-context.md
- [ ] Plan registry updates for contract changes
- [ ] Add/modify i18n resources for UI text (no hardcoding)

#### After Coding Checklist:
- [ ] Update registry files (`identifiers.json`, `endpoints.json`, `schemas.json`)
- [ ] Refresh `.mds/context/current-context.md`
- [ ] Add at least one test covering new/changed contract
- [ ] Run validation scripts
- [ ] Lint/tests pass locally and in CI
- [ ] Update `version.md` (1-2 prompt cadence)

#### Security Defaults:
- **Input Validation**: Schema validation, sanitize outputs
- **Authentication/Authorization**: Implement where relevant
- **Secret Hygiene**: No secrets in code, use `.env` and secret stores
- **Dependency Audits**: Regular security checks
- **OWASP Basics**: Apply security fundamentals

#### Session Hygiene:
- **Scope**: One prompt = ~3-7 tasks; avoid scope creep
- **Responses**: Prefer JSON-only for machine-consumed outputs
- **Secrets**: Never hardcode; use `.env` and secret stores
- **Error Handling**: Handle errors cleanly; avoid leaky abstractions

### Environment Targets
- **Cloud server**: Python 3.12 (pin in CI and docs)
- **Desktop**: WPF on .NET (target Revit-supported runtime)
- **Target Stack**: Desktop (WPF), Cloud (FastAPI Py 3.12), Revit Plugin

### Documentation Standards
- **Module Documentation**: Turkish language for user-facing docs, English for technical/code docs
- **Change Summaries**: Major changes, restructuring, or process updates must be documented in `.mds/outputs/` with dated filename
- **Auto-Documentation Template**:
```markdown
# [Module Name] Dokümantasyonu

## Genel Bakış
[Modülün ne yaptığının açıklaması]

## Kurulum ve Bağımlılıklar
pip install [required-packages]

## Kullanım  
[Kod örnekleri ve kullanım şekilleri]

## API Referansı
[Fonksiyonlar, sınıflar ve metodlar]

## Konfigürasyon
[Yapılandırma seçenekleri]

## Hata Yönetimi
[Yaygın hatalar ve çözümleri]
```

- **Summary Documentation Template**:
```markdown
# [Process/Change Name] Özeti
**Tarih:** YYYY-MM-DD  
**İşlem:** [Brief description]

## 🎯 Ana Hedef
[What was accomplished]

## 📁 Changes Made
[Detailed changes]

## ✅ Benefits
[Benefits achieved]

## 🎯 Usage/Next Steps
[How to use or follow up]
```

### Artifacts to Maintain
- **README.md**: How to run, test, deploy
- **CHANGELOG.md**: Semantic, user-facing changes
- **ADRs**: Significant architectural decisions
- **RISKS.md**: Top risks + mitigations
- **.env.example**: Document environment variables

### Error Log Management
If user proposes incorrect/unsafe/illogical ideas:
- Append entry to `hata.md` with: date/time, mistaken idea (verbatim), diagnosis (why wrong), recommended solution

### Teach/Coach Mode
- Kullanıcının yanlış varsayımlarını nazikçe işaretle
- Kısa nedenini açıkla ve güvenli/uygulanabilir 2–3 alternatif yol öner
- Alternatifler için beklenen fayda/riski ve karmaşıklığı belirt
- Bir "önerilen yol" seç