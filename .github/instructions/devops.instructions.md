---
applyTo: "**/*.yml,**/*.yaml,**/Dockerfile*,**/*.ps1,**/*.sh,**/*.tf,**/*k8s*.y*ml"
description: DevOps role — reproducible dev, CI, packaging, deploy, and rollback for ArchBuilder.AI.
---
As DevOps:
- Provide deterministic scripts and CI config. Cache deps, fail fast.

# ArchBuilder.AI DevOps Standards- Document env vars and secrets sourcing; add secret scanning and dependency audits.

- Supply minimal deploy steps for one target (e.g., Docker + Render/Netlify/Vercel) and rollback plan.

## Overview

As DevOps Engineer for ArchBuilder.AI, provide reliable, scalable, and secure infrastructure for multi-service architecture including desktop app distribution, cloud API deployment, and monitoring systems.Registry & CI gates

- Add CI job to run `pwsh -File scripts/validate-registry.ps1` and `pwsh -File scripts/rehydrate-context.ps1`.

## CI/CD Pipeline Requirements- Block merges when registry is stale compared to code diffs touching API or exported symbols.

- Python 3.12 baseline; pytest + coverage; black/flake8/mypy quality gates.

### GitHub Actions Workflow

```yamlVibe Coding Orchestration

# .github/workflows/ci-cd.yml- Provide task to run `scripts/run-vibe-coding.ps1` (manual guarded execution).

name: ArchBuilder.AI CI/CD Pipeline- After every 2 prompts, ensure `version.md` appended by script; require green CI before merge.

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]
  workflow_dispatch:

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: archbuilder-ai

jobs:
  validate-registry:
    name: Validate Registry Consistency
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup PowerShell
        uses: microsoft/setup-msbuild@v1
        
      - name: Validate Registry Files
        shell: pwsh
        run: |
          pwsh -File scripts/validate-registry.ps1 -Verbose
          
      - name: Rehydrate Context
        shell: pwsh
        run: |
          pwsh -File scripts/rehydrate-context.ps1
          
      - name: Check Registry vs Code Consistency
        shell: pwsh
        run: |
          # Block merges when registry is stale
          $changedFiles = git diff --name-only origin/main...HEAD
          $hasApiChanges = $changedFiles | Where-Object { $_ -match "src/.*\.(cs|py|ts|tsx)$" }
          $hasRegistryChanges = $changedFiles | Where-Object { $_ -match "docs/registry/.*\.json$" }
          
          if ($hasApiChanges -and -not $hasRegistryChanges) {
            Write-Error "API changes detected without registry updates. Please update registry files."
            exit 1
          }

  test-python:
    name: Test Python Cloud Server
    runs-on: ubuntu-latest
    needs: validate-registry
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: archbuilder_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python 3.12
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
          
      - name: Cache Python dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}
          
      - name: Install dependencies
        run: |
          cd src/cloud-server
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
          
      - name: Run linting
        run: |
          cd src/cloud-server
          black --check .
          flake8 .
          mypy .
          
      - name: Run tests with coverage
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/archbuilder_test
          REDIS_URL: redis://localhost:6379
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY_TEST }}
          VERTEX_AI_PROJECT_ID: ${{ secrets.VERTEX_AI_PROJECT_ID_TEST }}
        run: |
          cd src/cloud-server
          pytest --cov=. --cov-report=xml --cov-report=html
          
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./src/cloud-server/coverage.xml

  test-dotnet:
    name: Test .NET Desktop & Revit Plugin
    runs-on: windows-latest
    needs: validate-registry
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup .NET
        uses: actions/setup-dotnet@v3
        with:
          dotnet-version: '8.x'
          
      - name: Cache NuGet packages
        uses: actions/cache@v3
        with:
          path: ~/.nuget/packages
          key: ${{ runner.os }}-nuget-${{ hashFiles('**/*.csproj') }}
          
      - name: Restore dependencies
        run: |
          dotnet restore src/desktop-app/DesktopApp.sln
          dotnet restore src/revit-plugin/RevitPlugin.sln
          
      - name: Build solution
        run: |
          dotnet build src/desktop-app/DesktopApp.sln --no-restore --configuration Release
          dotnet build src/revit-plugin/RevitPlugin.sln --no-restore --configuration Release
          
      - name: Run tests
        run: |
          dotnet test src/desktop-app/DesktopApp.sln --no-build --configuration Release --collect:"XPlat Code Coverage"
          dotnet test src/revit-plugin/RevitPlugin.sln --no-build --configuration Release --collect:"XPlat Code Coverage"

  build-docker:
    name: Build and Push Docker Images
    runs-on: ubuntu-latest
    needs: [test-python, test-dotnet]
    if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/develop'
    
    outputs:
      image-tag: ${{ steps.meta.outputs.tags }}
      image-digest: ${{ steps.build.outputs.digest }}
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
        
      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
          
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ github.repository }}
          tags: |
            type=ref,event=branch
            type=sha,prefix={{branch}}-
            type=raw,value=latest,enable={{is_default_branch}}
            
      - name: Build and push
        id: build
        uses: docker/build-push-action@v5
        with:
          context: ./src/cloud-server
          file: ./src/cloud-server/Dockerfile
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    needs: build-docker
    if: github.ref == 'refs/heads/develop'
    environment: staging
    
    steps:
      - name: Deploy to staging environment
        run: |
          echo "Deploying ${{ needs.build-docker.outputs.image-tag }} to staging"

  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: build-docker
    if: github.ref == 'refs/heads/main'
    environment: production
    
    steps:
      - name: Deploy to production environment
        run: |
          echo "Deploying ${{ needs.build-docker.outputs.image-tag }} to production"
```

### Docker Configuration
```dockerfile
# src/cloud-server/Dockerfile
FROM python:3.12-slim

LABEL org.opencontainers.image.title="ArchBuilder.AI Cloud Server"
LABEL org.opencontainers.image.description="AI-powered architectural layout generation service"
LABEL org.opencontainers.image.source="https://github.com/ahmetcemkaraca/archbuilder.ai"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt requirements-prod.txt ./
RUN pip install --no-cache-dir -r requirements-prod.txt

# Copy application code
COPY . .

# Create non-root user
RUN groupadd -r archbuilder && useradd -r -g archbuilder archbuilder
RUN chown -R archbuilder:archbuilder /app
USER archbuilder

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Start application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

## Deployment Scripts

### Production Deployment Script
```powershell
# scripts/deploy-production.ps1
param(
    [Parameter(Mandatory=$true)]
    [string]$ImageTag,
    
    [Parameter(Mandatory=$false)]
    [switch]$DryRun = $false
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting ArchBuilder.AI Production Deployment" -ForegroundColor Green
Write-Host "Image Tag: $ImageTag" -ForegroundColor Yellow

# Validate prerequisites
Write-Host "📋 Validating prerequisites..."

# Check kubectl connection
try {
    kubectl cluster-info | Out-Null
    Write-Host "✅ Kubernetes cluster connection verified" -ForegroundColor Green
}
catch {
    Write-Error "❌ Cannot connect to Kubernetes cluster"
    exit 1
}

# Check Docker image exists
try {
    docker manifest inspect "ghcr.io/ahmetcemkaraca/archbuilder.ai:$ImageTag" | Out-Null
    Write-Host "✅ Docker image verified" -ForegroundColor Green
}
catch {
    Write-Error "❌ Docker image not found: $ImageTag"
    exit 1
}

# Backup current deployment
Write-Host "💾 Creating backup of current deployment..."
kubectl get deployment archbuilder-cloud-server -n archbuilder-ai -o yaml > "backup/deployment-$(Get-Date -Format 'yyyyMMdd-HHmmss').yaml"

# Update deployment with new image
if ($DryRun) {
    Write-Host "🔍 DRY RUN: Would update deployment with image: $ImageTag" -ForegroundColor Yellow
    kubectl set image deployment/archbuilder-cloud-server cloud-server="ghcr.io/ahmetcemkaraca/archbuilder.ai:$ImageTag" -n archbuilder-ai --dry-run=client
}
else {
    Write-Host "🔄 Updating deployment with new image..."
    kubectl set image deployment/archbuilder-cloud-server cloud-server="ghcr.io/ahmetcemkaraca/archbuilder.ai:$ImageTag" -n archbuilder-ai
    
    # Wait for rollout to complete
    Write-Host "⏳ Waiting for rollout to complete..."
    kubectl rollout status deployment/archbuilder-cloud-server -n archbuilder-ai --timeout=600s
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Deployment completed successfully" -ForegroundColor Green
        
        # Verify health check
        Write-Host "🔍 Verifying health check..."
        Start-Sleep -Seconds 30
        
        $healthCheck = curl -f https://api.archbuilder.app/health -s
        if ($healthCheck) {
            Write-Host "✅ Health check passed" -ForegroundColor Green
        }
        else {
            Write-Warning "⚠️ Health check failed - manual verification required"
        }
    }
    else {
        Write-Error "❌ Deployment failed"
        Write-Host "🔄 Starting automatic rollback..."
        kubectl rollout undo deployment/archbuilder-cloud-server -n archbuilder-ai
        exit 1
    }
}

Write-Host "🎉 Production deployment completed successfully!" -ForegroundColor Green
```

### Rollback Script
```powershell
# scripts/rollback-production.ps1
param(
    [Parameter(Mandatory=$false)]
    [int]$RevisionNumber = 0,
    
    [Parameter(Mandatory=$false)]
    [switch]$Force = $false
)

$ErrorActionPreference = "Stop"

Write-Host "🔄 Starting ArchBuilder.AI Production Rollback" -ForegroundColor Yellow

if (-not $Force) {
    $confirmation = Read-Host "Are you sure you want to rollback production? (yes/no)"
    if ($confirmation -ne "yes") {
        Write-Host "❌ Rollback cancelled" -ForegroundColor Red
        exit 0
    }
}

# Show rollout history
Write-Host "📋 Current rollout history:"
kubectl rollout history deployment/archbuilder-cloud-server -n archbuilder-ai

# Perform rollback
if ($RevisionNumber -gt 0) {
    Write-Host "🔄 Rolling back to revision $RevisionNumber..."
    kubectl rollout undo deployment/archbuilder-cloud-server -n archbuilder-ai --to-revision=$RevisionNumber
}
else {
    Write-Host "🔄 Rolling back to previous revision..."
    kubectl rollout undo deployment/archbuilder-cloud-server -n archbuilder-ai
}

# Wait for rollback to complete
Write-Host "⏳ Waiting for rollback to complete..."
kubectl rollout status deployment/archbuilder-cloud-server -n archbuilder-ai --timeout=300s

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Rollback completed successfully" -ForegroundColor Green
    
    # Verify health
    Write-Host "🔍 Verifying service health..."
    Start-Sleep -Seconds 30
    
    $healthCheck = curl -f https://api.archbuilder.app/health -s
    if ($healthCheck) {
        Write-Host "✅ Service is healthy after rollback" -ForegroundColor Green
    }
    else {
        Write-Warning "⚠️ Service health check failed - manual intervention required"
    }
}
else {
    Write-Error "❌ Rollback failed"
    exit 1
}
```

## Environment Management

### Environment Configuration
```yaml
# environments/production.yml
apiVersion: v1
kind: ConfigMap
metadata:
  name: archbuilder-config
  namespace: archbuilder-ai
data:
  ENVIRONMENT: "production"
  LOG_LEVEL: "INFO"
  CORS_ORIGINS: "https://app.archbuilder.ai,https://archbuilder.ai"
  MAX_WORKERS: "4"
  AI_MODEL_TIMEOUT: "30"
  RATE_LIMIT_REQUESTS: "100"
  RATE_LIMIT_WINDOW: "60"
  CACHE_TTL_SECONDS: "3600"
  
---
apiVersion: v1
kind: Secret
metadata:
  name: archbuilder-secrets
  namespace: archbuilder-ai
type: Opaque
stringData:
  DATABASE_URL: "postgresql://user:pass@archbuilder-db-prod:5432/archbuilder"
  REDIS_URL: "redis://archbuilder-cache-prod:6379"
  OPENAI_API_KEY: "${OPENAI_API_KEY}"
  VERTEX_AI_PROJECT_ID: "${VERTEX_AI_PROJECT_ID}"
  STRIPE_API_KEY: "${STRIPE_API_KEY}"
  JWT_SECRET_KEY: "${JWT_SECRET_KEY}"
```

Always ensure reproducible deployments, implement proper monitoring, provide rollback procedures, and maintain infrastructure as code for all environments.

````