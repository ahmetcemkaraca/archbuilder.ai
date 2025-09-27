# ArchBuilder.AI

**AI-Powered Architectural Design System** - A comprehensive platform combining Cloud-based AI processing with Desktop applications and Revit plugin integration for intelligent architectural design and building analysis.

## 🏗️ System Architecture

ArchBuilder.AI is a hybrid system featuring:

- **🌐 Cloud Server**: FastAPI-based Python backend with AI processing capabilities
- **🖥️ Desktop Application**: WPF-based Windows desktop interface 
- **📐 Revit Plugin**: Autodesk Revit integration for BIM workflows
- **🤖 AI Integration**: Multi-model AI support (OpenAI GPT-4, Vertex AI Gemini) for architectural analysis

## 🚀 Quick Start

### Prerequisites
- Python 3.12+ for cloud server
- .NET Framework 4.8+ for desktop application
- Autodesk Revit 2024+ for plugin integration
- PostgreSQL 15+ database (production) / SQLite (development)

### Cloud Server Setup

1. **Install Dependencies**
   ```bash
   cd src/cloud-server
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   Create a `.env` file in `src/cloud-server/`:
   ```env
   JWT_SECRET=your_secure_jwt_secret_here
   
   # Database Configuration - Production PostgreSQL
   DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/archbuilder
   DB_POOL_SIZE=20
   DB_MAX_OVERFLOW=30
   DB_POOL_TIMEOUT=30
   DB_POOL_RECYCLE=3600
   DB_ECHO=false
   
   # Optional read replica for scaling
   DATABASE_REPLICA_URL=postgresql+asyncpg://user:pass@replica:5432/archbuilder
   
   # RAG Service Configuration
   RAGFLOW_BASE_URL=http://localhost:12345
   RAGFLOW_API_KEY=your_ragflow_api_key
   RAGFLOW_API_VERSION=v1
   RAGFLOW_TIMEOUT_SECONDS=30
   
   LOG_LEVEL=INFO
   ```

3. **Run the Server**
   ```bash
   cd src/cloud-server
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Access API Documentation**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Desktop Application Setup

1. **Build the Application**
   ```bash
   cd src/desktop-app/ArchBuilder.Desktop
   dotnet build
   ```

2. **Run the Application**
   ```bash
   cd src/desktop-app/ArchBuilder.Desktop
   dotnet run
   ```

### Revit Plugin Installation

1. **Build the Plugin**
   ```bash
   cd src/revit-plugin
   dotnet build
   ```

2. **Install in Revit**
   - Copy the built files to Revit's add-ins directory
   - Follow the installation guide in `docs/development/revit-plugin-setup.md`

## 📚 Documentation

### Core Documentation
- **[Project Structure](docs/structure/project-structure-planned.md)** - Complete project organization
- **[API Documentation](docs/api/)** - REST API endpoints and schemas
- **[Registry System](docs/registry/README.md)** - Contract and schema management
- **[Governance](docs/governance.md)** - Development policies and workflows

### Development Guides
- **[Development Setup](docs/development/)** - Local development environment
- **[Architecture Decisions](docs/architecture/)** - ADRs and design decisions
- **[Security Guidelines](docs/security/)** - Security policies and implementation

### Service Documentation
- **[AI Services](docs/services/)** - AI integration and processing
- **[Validation Services](docs/services/validation-service.md)** - Data validation systems
- **[RAG Services](docs/services/rag-service.md)** - Document processing and retrieval

## 🔧 Core Features

### AI-Powered Architecture Analysis
- **Multi-format CAD Analysis**: Support for DWG/DXF, IFC, PDF files
- **Building Code Compliance**: Automated checking against regional regulations
- **Space Optimization**: AI-driven layout generation and improvement suggestions
- **Existing Project Analysis**: Comprehensive BIM project evaluation

### Production-Ready Database Infrastructure ✨ NEW
- **PostgreSQL Connection Pooling**: Optimized for high-concurrency workloads
- **Real-time Performance Monitoring**: Database health and slow query tracking
- **Automated Backup & Recovery**: Point-in-time recovery capabilities
- **Migration Management**: Alembic-based schema versioning with rollback
- **Connection Leak Detection**: Proactive monitoring and alerting

### Cloud-First SaaS Platform
- **Multi-tenant Architecture**: Scalable cloud deployment
- **Subscription Management**: Flexible pricing tiers and usage tracking
- **Real-time Collaboration**: WebSocket-based live updates
- **Enterprise Security**: Role-based access control and audit trails

### Professional Integration
- **Revit API Integration**: Direct BIM model manipulation
- **Dynamo Support**: Complex geometry generation
- **Export Capabilities**: Multiple output formats
- **Progress Tracking**: Real-time processing updates

## 📋 API Endpoints Overview

### Core APIs
- `GET /health` - Service health check
- `POST /v1/auth/login` - User authentication
- `POST /v1/ai/commands` - AI processing requests
- `POST /v1/validation/validate` - Data validation

### Database Administration (Admin Only)
- `GET /v1/database/health` - Database health monitoring
- `POST /v1/database/monitoring/start` - Start performance monitoring
- `GET /v1/database/monitoring/summary` - Get monitoring summary
- `POST /v1/database/migrations/upgrade` - Run database migrations
- `POST /v1/database/backup/create` - Create database backup

### Document Processing
- `POST /v1/documents/rag/ensure-dataset` - Dataset management
- `POST /v1/documents/rag/{dataset_id}/upload-parse` - Document upload
- `POST /v1/rag/query` - RAG-based document querying

### Real-time Features
- `WebSocket /v1/ws` - Live progress updates
- `POST /v1/storage/upload/init` - File upload initialization

## 🗄️ Database Schema

### Core Tables
- **users** - User accounts and authentication
- **projects** - Architectural projects
- **ai_commands** - AI processing history
- **subscriptions** - User subscription plans
- **usage** - Usage tracking and billing

### Document Management
- **rag_dataset_links** - Document dataset associations
- **rag_jobs** - Background processing jobs
- **validation_results** - Validation outcomes

## 🧪 Testing

### Run All Tests
```bash
# Cloud server tests
cd src/cloud-server
python -m pytest -v

# Registry validation
cd ../..
pwsh -File scripts/validate-registry.ps1

# Context rehydration
pwsh -File scripts/rehydrate-context.ps1
```

### Test Categories
- **Registry Contracts**: API schema validation
- **Database Models**: Data model integrity
- **Service Integration**: AI and external service tests

## 🚢 Deployment

### Production Deployment
1. **Environment Configuration**
   - Set production environment variables
   - Configure database connections
   - Set up external service credentials

2. **Database Migration**
   ```bash
   cd src/cloud-server
   alembic upgrade head
   ```

3. **Service Deployment**
   - Deploy cloud server to your preferred platform
   - Configure load balancing and scaling
   - Set up monitoring and logging

### Development Workflow
1. **Registry-First Development**: Update registry files before code changes
2. **Correlation ID Tracking**: All operations include correlation IDs
3. **Multi-language Support**: Turkish comments, English code
4. **Version Management**: Automated versioning every 2 prompts

## 🌍 Internationalization

### Language Policy
- **Code & Identifiers**: English only
- **Comments & Logs**: Turkish (Türkçe)
- **UI Text**: i18n support (English default, Turkish available)
- **API Responses**: Language-specific formatting

### Regional Support
- **Building Codes**: Turkish İmar Yönetmeliği compliance
- **Measurement Systems**: Metric (default) and Imperial support
- **Cultural Context**: Region-specific architectural patterns

## 🔒 Security

### Security Features
- **JWT Authentication**: Secure token-based auth
- **API Key Management**: Per-user API key generation
- **Rate Limiting**: Request throttling and abuse prevention
- **Data Encryption**: TLS encryption for all communications
- **Audit Logging**: Comprehensive operation tracking

### Compliance
- **GDPR Ready**: Data privacy and user rights
- **Building Code Compliance**: Regional regulation checking
- **Professional Standards**: Architect workflow integration

## 📈 Monitoring & Analytics

### Performance Monitoring
- **Response Time Tracking**: API endpoint performance
- **Database Performance**: Connection pool metrics, slow query analysis
- **Resource Usage**: CPU, memory, and storage monitoring
- **Connection Health**: Real-time database connection monitoring
- **Error Tracking**: Comprehensive error logging and alerting
- **User Analytics**: Usage patterns and feature adoption

### Business Intelligence
- **Subscription Metrics**: Revenue and user growth tracking
- **AI Usage Analytics**: Model performance and cost optimization
- **Project Success Rates**: Validation and completion metrics

## 🤝 Contributing

### Development Process
1. **Registry Updates**: Always update registry files with code changes
2. **Test Coverage**: Maintain comprehensive test coverage
3. **Documentation**: Keep documentation current with changes
4. **Code Review**: All changes require review and approval

### Code Standards
- **TypeScript/JavaScript**: ESLint + Prettier
- **Python**: Black + flake8 + mypy
- **C#**: EditorConfig + StyleCop
- **PowerShell**: PSScriptAnalyzer

## 📞 Support

### Documentation Resources
- **[Technical Documentation](docs/)** - Complete technical guides
- **[API Reference](docs/api/)** - Detailed API documentation
- **[Troubleshooting](docs/development/troubleshooting.md)** - Common issues and solutions

### Development Support
- **Registry System**: Contract and schema management
- **Validation Scripts**: Automated quality checking
- **Context Management**: Development state tracking

## 📄 License

This project is proprietary software. All rights reserved.

---

**Built with ❤️ for Architects, by Architects**

*Empowering architectural design through intelligent AI integration and seamless workflow automation.*


