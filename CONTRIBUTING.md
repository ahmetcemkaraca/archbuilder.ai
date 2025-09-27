# Contributing to ArchBuilder.AI

Projeye katkıda bulunduğunuz için teşekkür ederiz! Bu rehber, kod katkılarınızın kaliteli ve tutarlı olmasını sağlamak için hazırlanmıştır.

## 📋 İçindekiler

- [GitFlow Branching Model](#gitflow-branching-model)
- [Geliştirme Süreci](#geliştirme-süreci)
- [Code Review Süreci](#code-review-süreci)
- [Commit Mesaj Kuralları](#commit-mesaj-kuralları)
- [Registry ve Context Yönetimi](#registry-ve-context-yönetimi)
- [Test Gereksinimleri](#test-gereksinimleri)

## 🌳 GitFlow Branching Model

Projede **GitFlow** branching model kullanıyoruz:

### Branch Yapısı
- **`main`**: Production releases (protected, admin-only)
- **`develop`**: Integration branch (protected, default for PRs)
- **`feature/*`**: Yeni özellik geliştirme (from develop → to develop)
- **`release/*`**: Release hazırlığı (from develop → to main + develop)  
- **`hotfix/*`**: Kritik hata düzeltmeleri (from main → to main + develop)

### Feature Development Workflow

```bash
# 1. Develop branch'den başla
git checkout develop
git pull origin develop

# 2. Feature branch oluştur
git checkout -b feature/123-add-user-authentication

# 3. Geliştirme yap
git add .
git commit -m "feat(auth): add JWT authentication middleware"

# 4. PR oluştur: feature/123-add-user-authentication → develop
# 5. Review sonrası merge, feature branch silinir
```

### Release Process

```bash
# 1. Release branch oluştur
git checkout develop
git pull origin develop
git checkout -b release/1.2.0

# 2. Version bump ve changelog güncellemesi
git add .
git commit -m "chore(release): prepare version 1.2.0"

# 3. PR oluştur: release/1.2.0 → main
# 4. Main'e merge sonrası, main → develop merge
```

### Hotfix Process

```bash
# 1. Main'den hotfix branch oluştur
git checkout main
git pull origin main
git checkout -b hotfix/456-critical-security-fix

# 2. Kritik sorunu düzelt
git add .
git commit -m "fix(security): resolve authentication bypass vulnerability"

# 3. PR oluştur: hotfix/456-critical-security-fix → main
# 4. Main'e merge sonrası, main → develop merge
```

## 🚀 Geliştirme Süreci

### Başlamadan Önce

1. **Issue kontrol et**: GitHub Issues'da ilgili task var mı?
2. **Registry oku**: `docs/registry/*.json` dosyalarını kontrol et
3. **Context rehydrate et**: `.mds/context/current-context.md` oku
4. **Instructions oku**: İlgili `.github/instructions/*.instructions.md` dosyalarını oku

### Geliştirme Adımları

1. **Feature branch oluştur**:
   ```bash
   git checkout -b feature/issue-number-short-description
   ```

2. **Registry güncellemelerini planla**:
   - Yeni function/endpoint/schema eklerken registry güncellemesi gerekir
   - `docs/registry/*.json` dosyalarını güncellemeyi unutma

3. **Kod yaz**:
   - İlgili instruction dosyalarına uygun kod yaz
   - Türkçe comment'ler, İngilizce kod/değişken isimleri
   - UI metinleri için i18n kullan (hardcode etme)

4. **Test ekle**:
   - En az bir test eklenmeli
   - Registry contract'larını test et

5. **Validation çalıştır**:
   ```bash
   # Registry validation
   powershell -File scripts/validate-registry.ps1
   
   # Context rehydration  
   powershell -File scripts/rehydrate-context.ps1
   
   # Import checks
   pip check
   python -m py_compile src/cloud-server/app/*.py
   ```

### Geliştirme Sonrası

1. **Registry güncelle**: `docs/registry/*.json` dosyalarını güncelle
2. **Context güncelle**: `.mds/context/current-context.md` güncellemesi gerekirse yap
3. **Version.md güncellemesi**: Her 2 prompt'ta bir güncellenir
4. **Tests çalıştır**: CI pipeline'ın yerel olarak çalıştığını doğrula

## 👥 Code Review Süreci

### PR Gereksinimleri

- ✅ **Minimum 1 reviewer** gerekli
- ✅ **CI checks** geçmeli (`lint`, `validate`)
- ✅ **Conversation resolution** gerekli
- ✅ **Up-to-date branch** gerekli

### Review Checklist

#### Reviewer İçin:
- [ ] **Kod kalitesi**: Instruction dosyalarına uygun mu?
- [ ] **Registry güncellemeleri**: Yeni contract'lar registry'de var mı?
- [ ] **Test coverage**: Yeni kod test edilmiş mi?
- [ ] **Documentation**: Türkçe dokümantasyon var mı?
- [ ] **Security**: Güvenlik kurallarına uygun mu?
- [ ] **Performance**: Performance impact'i değerlendirilmiş mi?

#### Author İçin:
- [ ] **Self-review yapıldı**: Kendi kodunu gözden geçirdin mi?
- [ ] **Registry updated**: Registry dosyları güncel mi?
- [ ] **Tests added**: Yeni functionality test edildi mi?
- [ ] **CI passing**: Tüm CI check'ler geçiyor mu?
- [ ] **Breaking changes**: Breaking change varsa dokümante edildi mi?

## 📝 Commit Mesaj Kuralları

**Conventional Commits** formatı kullanıyoruz:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Commit Types:
- **feat**: Yeni özellik
- **fix**: Bug düzeltmesi  
- **docs**: Dokümantasyon değişiklikleri
- **style**: Kod formatı (logic değişikliği yok)
- **refactor**: Kod refactoring
- **test**: Test ekleme/düzeltme
- **chore**: Build process, tool konfigürasyonu

### Örnekler:
```bash
feat(auth): add JWT authentication middleware
fix(validation): resolve geometry validation edge case
docs(api): update authentication endpoints documentation
chore(deps): update fastapi to v0.104.1
refactor(services): extract validation logic to separate service
```

### Scope Önerileri:
- **auth**: Authentication/authorization
- **validation**: Validation services
- **ai**: AI integration
- **revit**: Revit plugin
- **desktop**: Desktop app
- **api**: API endpoints
- **db**: Database changes
- **ci**: CI/CD changes

## 📊 Registry ve Context Yönetimi

### Registry Dosyları
Aşağıdaki dosyalar **her contract değişikliğinde** güncellenmeli:

- `docs/registry/identifiers.json`: Modules, exports, variables
- `docs/registry/endpoints.json`: API contracts
- `docs/registry/schemas.json`: Data models, DB schemas

### Context Yönetimi
- `.mds/context/current-context.md`: Aktif contracts özeti
- `.mds/context/history/NNNN.md`: Session summary'leri

### Validation Scripts
```bash
# Registry validation
powershell -File scripts/validate-registry.ps1

# Context rehydration
powershell -File scripts/rehydrate-context.ps1

# Context snapshot
powershell -File scripts/snapshot-context.ps1
```

## 🧪 Test Gereksinimleri

### Minimum Test Gereksinimleri
- **Unit tests**: Yeni function'lar için
- **Integration tests**: API endpoint'ler için
- **Contract tests**: Registry contract'ları için

### Test Komutları
```bash
# Python tests
cd src/cloud-server
pytest -v

# Registry contract tests
powershell -File scripts/validate-registry.ps1

# Import/dependency tests
pip check
python -m py_compile src/cloud-server/app/*.py
```

## 🚫 Yasaklı Practices

### ❌ Yapılmaması Gerekenler:
- Direct push to `main` or `develop`
- Hardcoded strings in UI (i18n kullan)
- Registry güncellemeden contract değişikliği
- Test olmadan yeni functionality
- Force push to protected branches
- Secret values in code (environment variables kullan)
- Breaking changes without migration plan

### ⚠️ Dikkat Edilmesi Gerekenler:
- Registry consistency
- Context rehydration
- Turkish comments, English code
- Performance impact
- Security implications
- Backward compatibility

## 🆘 Yardım ve Destek

### Sorun Yaşadığında:
1. **Documentation kontrol et**: `docs/` klasöründeki dokümanları oku
2. **Registry validation çalıştır**: `scripts/validate-registry.ps1`
3. **GitHub Issues**: Yeni issue oluştur
4. **Code review**: Maintainer'lardan yardım iste

### Useful Commands:
```bash
# Registry ve context setup
powershell -File scripts/validate-registry.ps1
powershell -File scripts/rehydrate-context.ps1

# Development setup
pip install -r src/cloud-server/requirements.txt
pip check

# Git flow helpers
git checkout develop && git pull origin develop
git checkout -b feature/your-feature-name
```

## 📚 İlgili Dokümantasyon

- [Branch Protection Setup](.mds/BRANCH_PROTECTION_SETUP.md)
- [GitFlow Guide](.mds/GITFLOW_GUIDE.md)
- [Architecture Documentation](docs/architecture/)
- [API Documentation](docs/api/)
- [Registry Documentation](docs/registry/)

---

Katkılarınız için teşekkür ederiz! Herhangi bir sorunuz varsa GitHub Issues üzerinden iletişime geçebilirsiniz.