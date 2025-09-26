---
applyTo: "docs/registry/**/*.json,.mds/context/**/*.md,.mds/context/**/*.json,**/*.md"
description: Registry and Context Management — contract lifecycle for identifiers, endpoints, and schemas with CI enforcement.
---

# Registry & Context Management for ArchBuilder.AI

## Overview
The ArchBuilder.AI registry system provides a central registration system for consistent contract management and persistent context across all services. This system guarantees data integrity and API compatibility between the desktop app, cloud server, and Revit plugin.

## Registry Maintenance Rules
After any changes to public contracts, identifiers, or system interfaces, you MUST update the following registry files:

### Required Registry Files

#### 1. `docs/registry/identifiers.json` - Module and Service Registry
```json
{
  "modules": [
    {
      "name": "ai.service",
      "namespace": "RevitAutoPlan.Services.AI",
      "exports": ["GenerateLayoutAsync", "ValidateOutputAsync", "ProcessPromptAsync"], 
      "variables": ["AI_MODEL_TIMEOUT", "MAX_RETRY_ATTEMPTS"],
      "configKeys": ["OpenAI:ApiKey", "VertexAI:ProjectId", "AI:ModelSelector"],
      "version": "1.2.0",
      "lastUpdated": "2025-09-26T10:30:00Z",
      "dependencies": ["validation.service", "prompt.engine"],
      "description": "AI integration service for layout generation and validation"
    },
    {
      "name": "revit.api.service", 
      "namespace": "RevitAutoPlan.Revit",
      "exports": ["CreateWallsAsync", "PlaceDoorsAsync", "ValidateGeometryAsync"],
      "variables": ["DEFAULT_WALL_HEIGHT", "MIN_ROOM_AREA"],
      "configKeys": ["Revit:TransactionMode", "Revit:ErrorHandling"],
      "version": "1.1.5",
      "lastUpdated": "2025-09-26T09:15:00Z",
      "dependencies": ["geometry.validation"],
      "description": "Revit API integration for element creation and manipulation"
    },
    {
      "name": "cloud.client",
      "namespace": "RevitAutoPlan.Cloud",
      "exports": ["SendCommandAsync", "ReceiveResultAsync", "WebSocketConnect"],
      "variables": ["API_BASE_URL", "WEBSOCKET_TIMEOUT"],
      "configKeys": ["CloudAPI:BaseUrl", "CloudAPI:ApiKey", "CloudAPI:Region"],
      "version": "1.0.8",
      "lastUpdated": "2025-09-26T08:45:00Z",
      "dependencies": ["http.client", "websocket.manager"],
      "description": "Cloud service client for desktop-cloud communication"
    }
  ],
  "globals": {
    "correlation_id_format": "AI_{timestamp}_{guid}",
    "supported_languages": ["en", "tr", "de", "fr", "es"],
    "supported_file_formats": ["dwg", "dxf", "ifc", "rvt", "pdf"],
    "api_version": "v1",
    "last_schema_update": "2025-09-26T10:30:00Z"
  }
}
```

#### 2. `docs/registry/endpoints.json` - API Contract Registry
```json
{
  "endpoints": [
    {
      "name": "CreateAICommand",
      "method": "POST",
      "path": "/v1/ai/commands",
      "service": "cloud-server",
      "inputSchema": "AICommandRequest@v1.2",
      "outputSchema": "AICommandResponse@v1.2", 
      "auth": "required",
      "rateLimit": "10/minute",
      "version": "1.2.0",
      "deprecated": false,
      "description": "Process new AI command from user prompt with usage tracking",
      "headers": {
        "required": ["X-API-Key", "X-Correlation-ID"],
        "optional": ["Accept-Language", "X-Region"]
      },
      "responses": {
        "201": "Command created successfully",
        "400": "Invalid request parameters", 
        "401": "Authentication required",
        "402": "Usage limit exceeded",
        "500": "Internal server error"
      },
      "lastUpdated": "2025-09-26T10:30:00Z"
    },
    {
      "name": "WebSocketConnection",
      "method": "WS",
      "path": "/v1/ws",
      "service": "cloud-server", 
      "inputSchema": "WebSocketConnectionRequest@v1.0",
      "outputSchema": "WebSocketMessage@v1.0",
      "auth": "required",
      "description": "Real-time communication for progress updates and results",
      "queryParams": ["api_key", "correlation_id"],
      "messageTypes": [
        "connection_established",
        "progress_update", 
        "command_completed",
        "error_occurred"
      ],
      "lastUpdated": "2025-09-26T09:30:00Z"
    }
  ],
  "internal_apis": [
    {
      "name": "RevitAPITransaction",
      "method": "REVIT_API",
      "service": "revit-plugin",
      "inputSchema": "RevitTransactionRequest@v1.0",
      "outputSchema": "RevitTransactionResponse@v1.0",
      "description": "Internal Revit API calls within plugin context",
      "operations": ["CreateWalls", "PlaceDoors", "ValidateGeometry"]
    }
  ]
}
```

#### 3. `docs/registry/schemas.json` - Data Model Registry
```json
{
  "schemas": [
    {
      "name": "AICommandRequest",
      "version": "1.2",
      "type": "input",
      "description": "Request for AI-powered layout generation",
      "properties": {
        "user_prompt": {
          "type": "string",
          "required": true,
          "minLength": 10,
          "maxLength": 5000,
          "description": "Natural language description of desired layout"
        },
        "total_area_m2": {
          "type": "number",
          "required": true,
          "minimum": 5,
          "maximum": 10000,
          "description": "Total area in square meters"
        },
        "building_type": {
          "type": "string",
          "required": true,
          "enum": ["residential", "office", "retail", "industrial"],
          "description": "Type of building for context-specific rules"
        },
        "language": {
          "type": "string", 
          "required": false,
          "enum": ["en", "tr", "de", "fr", "es"],
          "default": "en",
          "description": "Language for AI processing and responses"
        },
        "region": {
          "type": "string",
          "required": false,
          "enum": ["tr", "eu", "us", "asia"],
          "default": "eu",
          "description": "Region for building codes and regulations"
        }
      },
      "lastUpdated": "2025-09-26T10:30:00Z"
    }
  ],
  "migrations": [
    {
      "from_version": "1.1",
      "to_version": "1.2", 
      "schema": "AICommandRequest",
      "changes": [
        "Added 'region' field for localization",
        "Added 'context.analysis_type' for existing project analysis"
      ],
      "migration_date": "2025-09-26T10:30:00Z",
      "backward_compatible": true
    }
  ]
}
```

### Context Management System

#### `.mds/context/current-context.md` Template
```markdown
# ArchBuilder.AI Current Context

## Active Contracts & Variables
**Last Updated:** 2025-09-26T10:30:00Z  
**Session ID:** dev-session-20250926-103000

### Critical System Variables
- API Version: v1.2.0
- Active AI Models: GPT-4.1, Gemini-2.5-Flash-Lite
- Current Build: feature/ai-integration-v1.2
- Registry Schema Version: 1.2.0

### Open Contracts
1. **AI Service Integration** (correlation: AI_20250926103000_a1b2c3d4)
   - Status: In Development
   - API Endpoints: /v1/ai/commands (POST, GET)
   - Schema: AICommandRequest@v1.2, AICommandResponse@v1.2
   - Dependencies: OpenAI client, Vertex AI client, Validation service

### Recent Changes
- **2025-09-26 10:30**: Added region-specific AI model selection
- **2025-09-26 10:15**: Extended AI command response schema with usage tracking

### Pending Tasks
1. Complete validation service integration with Turkish building codes
2. Implement existing project analysis AI prompts  
3. Add comprehensive error handling for all API endpoints

### Known Issues
- Correlation ID format validation needs improvement
- WebSocket reconnection logic incomplete
```

## Validation Commands and Scripts

### Registry Validation Script (`scripts/validate-registry.ps1`)
```powershell
# Registry validation must run after every registry update
param(
    [switch]$Fix,
    [switch]$Verbose
)

Write-Host "Validating ArchBuilder.AI Registry..." -ForegroundColor Green

# Validate JSON syntax
$registryFiles = @(
    "docs/registry/identifiers.json",
    "docs/registry/endpoints.json", 
    "docs/registry/schemas.json"
)

$errors = @()

foreach ($file in $registryFiles) {
    if (Test-Path $file) {
        try {
            $content = Get-Content $file -Raw | ConvertFrom-Json
            Write-Host "✓ $file - Valid JSON" -ForegroundColor Green
            
            # Validate required fields
            if ($file -match "identifiers.json") {
                if (-not $content.modules -or -not $content.globals) {
                    $errors += "$file: Missing required fields 'modules' or 'globals'"
                }
            }
        }
        catch {
            $errors += "$file: Invalid JSON - $($_.Exception.Message)"
        }
    }
    else {
        $errors += "$file: File not found"
    }
}

if ($errors.Count -gt 0) {
    Write-Host "Registry validation failed:" -ForegroundColor Red
    foreach ($error in $errors) {
        Write-Host "  ❌ $error" -ForegroundColor Red
    }
    exit 1
}
else {
    Write-Host "✅ Registry validation successful" -ForegroundColor Green
    
    # Update validation timestamp
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    Add-Content -Path ".mds/context/validation-log.md" -Value "- $timestamp : Registry validation passed"
}
```

### Context Rehydration Script (`scripts/rehydrate-context.ps1`)
```powershell
# Context rehydration script for session start
Write-Host "Rehydrating ArchBuilder.AI Context..." -ForegroundColor Green

# Read current context
if (Test-Path ".mds/context/current-context.md") {
    $currentContext = Get-Content ".mds/context/current-context.md" -Raw
    Write-Host "✓ Current context loaded" -ForegroundColor Green
}
else {
    Write-Host "⚠️  No current context found - starting fresh" -ForegroundColor Yellow
}

# Read registry files
$registryData = @{}
$registryFiles = @("identifiers", "endpoints", "schemas")

foreach ($file in $registryFiles) {
    $path = "docs/registry/$file.json"
    if (Test-Path $path) {
        $registryData[$file] = Get-Content $path -Raw | ConvertFrom-Json
        Write-Host "✓ Loaded $file registry" -ForegroundColor Green
    }
}

Write-Host "✅ Context rehydration complete" -ForegroundColor Green

# Generate session summary
$sessionId = "dev-session-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
$timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'

$summary = @"
# Session Context Summary

**Session ID:** $sessionId  
**Started:** $timestamp  
**Registry Status:** Valid  
**Active Modules:** $($registryData.identifiers.modules.Count)  
**Active Endpoints:** $($registryData.endpoints.endpoints.Count)  
**Schema Versions:** $($registryData.schemas.schemas.Count)
"@

Write-Output $summary | Out-File -FilePath ".mds/context/session-$sessionId.md" -Encoding UTF8
```

## Contract Change Management

### Version Management
```powershell
# Auto-update version.md every 2 prompts
$timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
$version = "1.2.$(Get-Date -Format 'yyyyMMdd')"

$versionEntry = @"

## Version $version - $timestamp

### Changes
- Enhanced registry management with comprehensive validation
- Added multi-language AI model selection
- Implemented existing project analysis capabilities
- Extended WebSocket communication for real-time updates

### Registry Updates
- AICommandRequest@v1.2: Added region and context fields
- AICommandResponse@v1.2: Added usage tracking information
- New validation scripts for registry consistency
"@

Add-Content -Path "version.md" -Value $versionEntry
```

## Session Management Best Practices

### Task Organization Rules
1. **Session Scope**: Handle 3-5 related tasks per session
2. **Atomic Changes**: Each registry update should correspond to functional implementation
3. **Correlation Tracking**: Use consistent correlation IDs across all related changes
4. **Documentation Sync**: Update both registry and implementation docs simultaneously

### Commit Message Standards
```bash
# Registry updates with code changes
git commit -m "feat(ai): add multi-language support [AI_20250926103000_a1b2c3d4]

- Extended AICommandRequest schema to v1.2 with region field
- Implemented dynamic model selection based on language/region
- Updated registry/schemas.json and registry/endpoints.json
- Added validation tests for new schema fields

Registry-Update: schemas@v1.2, identifiers@v1.1
Correlation-ID: AI_20250926103000_a1b2c3d4"
```

### Quality Gates
- **Registry Validation**: All JSON files must validate before commit
- **Schema Consistency**: Cross-reference validation between endpoints and schemas
- **Backward Compatibility**: Ensure migrations maintain compatibility
- **Context Currency**: Current context must reflect actual system state
- **Test Coverage**: New contracts require corresponding test coverage

Always maintain registry integrity, validate cross-references, and ensure persistent context accurately reflects system state.

````
