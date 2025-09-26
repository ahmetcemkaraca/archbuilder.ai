Project-wide Copilot instructions for ArchBuilder.AI autonomous development across desktop/cloud/Revit. Keep answers concise; code complete and runnable.

## 🔧 MANDATORY DEVELOPMENT WORKFLOW

### 🌟 GIT BRANCH WORKFLOW
**ALWAYS** work with feature branches for every task/implementation:

#### Git Branch Strategy:
1. **Create Feature Branch**: Before starting any task, create a new branch from master
   ```bash
   git checkout master
   git pull origin master
   git checkout -b feature/task-name-description
   ```

2. **Branch Naming Convention**:
   - `feature/mainwindow-implementation`
   - `feature/project-management-views`
   - `feature/revit-commands-core`
   - `bugfix/issue-description`
   - `docs/update-instructions`

3. **Work on Feature Branch**: 
   - Make all commits to the feature branch
   - Use descriptive commit messages with conventional commits format
   - Push feature branch to origin regularly

4. **Submit for Review**:
   - When task is complete, push final branch to origin
   - DO NOT merge to master directly
   - Human reviewer will merge after approval

5. **Example Workflow**:
   ```bash
   # Start new task
   git checkout master
   git pull origin master
   git checkout -b feature/project-management-views
   
   # Work and commit
   git add .
   git commit -m "feat: implement project dashboard UI"
   git push origin feature/project-management-views
   
   # Continue until task complete, then wait for merge approval
   ```

### Before ANY Function Implementation or Code Fix:
**ALWAYS** read the relevant `*.instructions.md` files from `.github/instructions/` directory before writing or modifying any code. This is **NON-NEGOTIABLE** and ensures consistency, security, and quality across the entire codebase.

#### Workflow Steps:
1. **Identify the task** - Understand what needs to be implemented or fixed
2. **Read relevant instruction files** - Based on file patterns and technologies involved
3. **Apply the guidelines** - Follow the specific patterns, standards, and best practices
4. **Preserve existing functionality** - Ensure that existing features are not removed, broken, or changed
5. **Check and fix imports** - MANDATORY: Verify all imports are valid and install missing dependencies
6. **Update documentation** - MANDATORY: Document all new modules in corresponding docs/ files
7. **Implement the code** - Write code that adheres to all applicable instructions
8. **Validate compliance** - Ensure the implementation follows all guidelines

### 🚨 CRITICAL: Import Management and Documentation Automation

#### MANDATORY Import Verification Process:
After EVERY code modification or new file creation, you MUST:

1. **Check Import Resolution**: 
   ```bash
   # For Python files
   python -m py_compile path/to/file.py
   # For requirements verification
   pip check
   ```

2. **Install Missing Dependencies**:
   ```bash
   # Cloud server dependencies
   cd src/cloud-server
   pip install -r requirements.txt
   
   # Check for missing packages and add to requirements.txt
   pip freeze > current_requirements.txt
   ```

3. **Verify Import Statements**:
   - Ensure all `import` statements resolve correctly
   - Use absolute imports for clarity
   - Add missing packages to requirements.txt immediately
   - Document import failures and resolution steps

#### MANDATORY Documentation Process:
After creating ANY new module, service, or significant feature, you MUST:

1. **Create Module Documentation**:
   ```
   docs/
   ├── api/                    # API endpoint documentation
   ├── services/               # Service layer documentation  
   ├── modules/               # Individual module documentation
   ├── architecture/          # System architecture docs
   └── setup/                 # Installation and setup guides
   ```

2. **Document in Turkish** (as requested by user):
   - Create `.md` files explaining how each module works
   - Include code examples and usage patterns
   - Document dependencies and requirements
   - Explain integration points and data flows

3. **Auto-Documentation Template**:
   ```markdown
   # [Module Name] Dokumentasyonu
   
   ## Genel Bakış
   [Modülün ne yaptığının açıklaması]
   
   ## Kurulum ve Bağımlılıklar
   ```bash
   pip install [required-packages]
   ```
   
   ## Kullanım
   [Kod örnekleri ve kullanım şekilleri]
   
   ## API Referansı
   [Fonksiyonlar, sınıflar ve metodlar]
   
   ## Konfigürasyon
   [Yapılandırma seçenekleri]
   
   ## Hata Yönetimi
   [Yaygın hatalar ve çözümleri]
   ```

#### Dependency Management Rules:
1. **Always check imports before committing code**
2. **Update requirements.txt immediately when adding new dependencies**  
3. **Use version pinning for production dependencies**
4. **Document why each dependency is needed**
5. **Prefer stable, well-maintained packages**
6. **Test imports in clean virtual environment**

#### Documentation Standards:
1. **Turkish language for user-facing documentation**
2. **English for technical/code documentation**
3. **Include practical examples and code snippets**
4. **Update docs immediately after code changes**
5. **Link related modules and services**
6. **Document error scenarios and troubleshooting**

### 📋 Instruction Files Reference Guide

Quality gates
- Lint/format, unit + integration, smoke/e2e. Ship only when green. Provide rollback steps.

Artifacts to maintain
- README.md (how to run, test, deploy)
- CHANGELOG.md (semantic, user-facing)
- ADRs for significant decisions
- RISKS.md for top risks + mitigations

Security defaults
- Validate inputs (schema), sanitize outputs, authn/authz where relevant, secret hygiene, dependency audits.

When asked for help
- Provide a short analysis, then update the trio, then code edits with tests, then run instructions.

Copilot behavior
- Keep chat replies compact. Prefer bullet lists and fenced code for commands when needed. Cite files you change.
- Use `.github/instructions/*.instructions.md` for role-specific rules, and `.github/prompts/*.prompt.md` for reusable tasks.

Semantic Versioning (SemVer)
- Use SemVer: MAJOR.MINOR.PATCH (e.g., 1.4.2).
- Bump MAJOR for incompatible API/behavior changes, data migrations without backward compatibility, or breaking CLI flags.
- Bump MINOR for backward-compatible feature additions, new endpoints/flags, or deprecations (without removal).
- Bump PATCH for backward-compatible bug fixes, performance tweaks without API change, or doc/CI fixes.
- Keep a CHANGELOG.md with entries grouped by Added/Changed/Fixed/Removed/Deprecated/Security.
- Tie bumps to Conventional Commits: feat → MINOR, fix/perf → PATCH, refactor/docs/chore/test → PATCH (unless breaking), feat! or fix! → MAJOR.
- Tag releases (e.g., v1.5.0) and reference in version.md entries; provide rollback notes for MAJOR changes.

### Language & Output Policy (Project-wide)
This policy is mandatory and overrides any conflicting older statements:

- Code and identifiers: English
- In-code comments and log messages: Turkish
- UI text: English by default via i18n/locale files (Turkish translation optional); never hardcode in components
- Chat responses to the user: Turkish, concise and actionable

Example (frontend i18n):
```json
{
  "common": { "save": "Kaydet", "cancel": "İptal" }
}
```

Example (backend log):
```
// Kullanıcı kaydı başarıyla tamamlandı
logger.info({ userId }, "Kullanıcı oluşturuldu");
```

### Registry & Persistent Context (Mandatory)
To prevent drift and forgetting of contracts across sessions, maintain a project registry and versioned context.

Required files/directories:
- docs/registry/identifiers.json — modules, exports, variables, config keys
- docs/registry/endpoints.json — HTTP/gRPC/GraphQL contracts (method, path, schemas, version, auth)
- docs/registry/schemas.json — data models, DB tables, migrations
- .mds/context/current-context.md — short technical summary of active contracts and critical variables
- .mds/context/history/ — versioned session summaries (e.g., 0001.md, 0002.md)

Rules:
1. After any change that adds/renames/deletes functions, variables, endpoints, or schemas, update the registry JSONs in the same branch and commit.
2. Before starting a new session or after summarizing/clearing context, rehydrate by reading docs/registry/*.json and .mds/context/current-context.md.
3. At session end, append a concise summary to .mds/context/history/<NNNN>.md and refresh .mds/context/current-context.md.
4. Never ship a branch where code changes the public contract without updating the registry and adding at least one test.

Minimal schemas:
```json
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
```
```json
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

### Versioning cadence (local policy)
- Update version.md at the end of every 1 prompts (development cycle).
- Use PowerShell to stamp the date/time: `Get-Date -Format 'yyyy-MM-dd HH:mm:ss'`.
- Each entry must summarize key changes, new features, or bug fixes. Do not delete previous entries.


### AI client gaps
- Implement analyze_project in AI clients; define input/output schemas and add tests.