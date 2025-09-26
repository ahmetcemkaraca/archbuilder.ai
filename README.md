# ArchBuilder.AI

🏗️ **AI-Powered Architectural Design & BIM Automation Platform**

ArchBuilder.AI, Autodesk Revit entegrasyonu ile AI destekli mimari tasarım ve yapı bilgi modellemesi (BIM) otomasyonu sağlayan kapsamlı bir platformdur.

## 🌟 Özellikler

- **🤖 AI-Powered Design**: Vertex AI (Gemini) ve OpenAI/Azure OpenAI ile akıllı mimari tasarım
- **🏠 Revit Integration**: Autodesk Revit plugin ile doğrudan BIM entegrasyonu  
- **☁️ Cloud Processing**: Scalable Python FastAPI backend
- **🖥️ Desktop App**: WPF tabanlı masaüstü uygulaması
- **📊 Multi-Format Support**: DWG/DXF, IFC, PDF dosya formatları
- **🌍 Multi-Language**: Türkçe ve İngilizce desteği
- **🔐 Enterprise Security**: JWT authentication, role-based access control
- **📈 Performance Monitoring**: Comprehensive monitoring ve analytics

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Desktop App   │    │   Cloud Server   │    │  Revit Plugin   │
│     (WPF)       │◄──►│   (FastAPI)      │◄──►│     (.NET)      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                       ┌────────▼────────┐
                       │  AI Services    │
                       │ (Vertex/OpenAI) │
                       └─────────────────┘
```

## 🚀 Hızlı Başlangıç

### Gereksinimler
- **Python 3.12+** (Cloud server)
- **NET 8.0+** (Desktop app & Revit plugin)
- **Autodesk Revit 2024+** (Plugin)
- **Docker** (Opsiyonel deployment)

### Kurulum

#### 1. Repository Klonlama
```bash
git clone https://github.com/ahmetcemkaraca/archbuilder.ai.git
cd archbuilder.ai
```

#### 2. Cloud Server Setup
```bash
cd src/cloud-server
pip install -r requirements.txt

# Environment konfigürasyonu
cp .env.example .env
# .env dosyasını düzenleyin (AI API keys, database config)

# Veritabanı migration
alembic upgrade head

# Sunucuyu başlatma
uvicorn app.main:app --reload
```

#### 3. Desktop App Setup
```bash
cd src/desktop-app
dotnet restore
dotnet build
dotnet run
```

#### 4. Revit Plugin Setup
```bash
cd src/revit-plugin
dotnet build
# Plugin'i Revit'e yüklemek için ArchBuilderRevit.addin dosyasını Revit AddIns klasörüne kopyalayın
```

## 🌳 Git Workflow

Bu proje **GitFlow** branching modelini kullanır:

### Branch Yapısı
- **`main`**: Production releases (protected)
- **`develop`**: Integration branch (default, protected)
- **`feature/*`**: New features (`feature/123-add-authentication`)
- **`release/*`**: Release preparation (`release/1.2.0`)
- **`hotfix/*`**: Critical fixes (`hotfix/456-security-fix`)

### Geliştirme Workflow'u
```bash
# Feature development
git checkout develop
git pull origin develop
git checkout -b feature/123-your-feature

# Development...
git add .
git commit -m "feat(scope): your changes"

# Create PR to develop
git push origin feature/123-your-feature
```

📚 **Detaylı Bilgi**: [Git Workflow Documentation](docs/git-workflow.md)

## 🛠️ Geliştirme

### Code Standards
- **Python**: Black, isort, flake8, mypy
- **NET**: dotnet format, EditorConfig
- **Commit**: Conventional Commits format
- **Comments**: Turkish comments, English code
- **UI**: i18n support (no hardcoded strings)

### Registry Management
Bu proje **Registry & Context Management** sistemi kullanır:
- `docs/registry/identifiers.json`: Module exports
- `docs/registry/endpoints.json`: API contracts  
- `docs/registry/schemas.json`: Data models

#### Validation Scripts
```bash
# Registry validation
powershell -File scripts/validate-registry.ps1

# Context rehydration
powershell -File scripts/rehydrate-context.ps1
```

### Testing
```bash
# Python tests
cd src/cloud-server
pytest -v

# NET tests
cd src/desktop-app
dotnet test

cd src/revit-plugin  
dotnet test
```

## 🚦 CI/CD Pipeline

### Status Checks
- **`lint`**: Code formatting ve quality checks
- **`validate`**: GitFlow compliance, registry validation
- **Performance Gates**: Load testing ve performance monitoring

### Branch Protection
- **Main**: Admin-only, PR required, status checks
- **Develop**: PR required, status checks, auto-delete branches
- **Feature**: Temporary, no protection

## 📊 Monitoring & Observability

### Metrics & Monitoring
- **Prometheus**: Metrics collection
- **Grafana**: Dashboards ve alerting
- **Structured Logging**: Correlation ID tracking
- **Performance Monitoring**: Response times, error rates

### Health Checks
```bash
# Application health
curl http://localhost:8000/v1/health

# Registry health
powershell -File scripts/validate-registry.ps1
```

## 🔐 Security

### Authentication & Authorization
- **JWT** tokens with refresh mechanism
- **Role-based** access control (RBAC)
- **API Key** authentication for integrations
- **Rate limiting** ve abuse protection

### Security Features
- Input validation ve sanitization
- SQL injection protection
- XSS prevention
- Secrets management (Azure Key Vault)
- Audit logging

## 📚 Documentation

### User Documentation
- [API Documentation](docs/api/) - REST API reference
- [Desktop App Guide](docs/desktop-app/) - User interface guide
- [Revit Plugin Guide](docs/revit-plugin/) - Plugin usage

### Developer Documentation
- [Architecture Overview](docs/architecture/) - System design
- [Contributing Guide](CONTRIBUTING.md) - Development guidelines
- [Git Workflow](docs/git-workflow.md) - Branching strategy  
- [Registry Documentation](docs/registry/) - Contract management

### Governance
- [Code Style](/.github/instructions/code-style.instructions.md)
- [Security Guidelines](/.github/instructions/security.instructions.md)
- [API Standards](/.github/instructions/api-standards.instructions.md)

## 🤝 Contributing

Katkıda bulunmak için lütfen [CONTRIBUTING.md](CONTRIBUTING.md) dokümantasyonunu okuyun.

### Quick Start
1. Fork the repository
2. Create feature branch: `git checkout -b feature/123-your-feature`
3. Follow code standards ve commit conventions
4. Update registry files if needed
5. Add tests for new functionality
6. Create pull request to `develop` branch

## 📄 License

Bu proje [MIT License](LICENSE) altında lisanslanmıştır.

## 🆘 Support

- **GitHub Issues**: Bug reports ve feature requests
- **Documentation**: [docs/](docs/) klasörü
- **Email**: support@archbuilder.ai

## 🏗️ Roadmap

### Phase 1: Core Platform ✅
- [x] FastAPI backend
- [x] Basic AI integration  
- [x] Desktop app foundation
- [x] Revit plugin structure

### Phase 2: Advanced Features 🔄  
- [ ] Advanced AI prompting
- [ ] Multi-format CAD support
- [ ] Performance optimization
- [ ] Enhanced monitoring

### Phase 3: Enterprise 📅
- [ ] Multi-tenant architecture
- [ ] Advanced security features
- [ ] White-label solutions
- [ ] Enterprise integrations

---

**Built with ❤️ by the ArchBuilder.AI Team**