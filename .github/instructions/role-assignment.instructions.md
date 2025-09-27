---
applyTo: "**/*"
description: Role Assignment System — automatic instruction attachment based on file patterns and development contexts.
---

# ArchBuilder.AI Role Assignment System

## Overview
This system automatically attaches relevant instruction files based on file types and project contexts to ensure role-appropriate guidance during development.

## Universal Roles (Always Applied)

### Core Development (All Files)
**Files**: `**/*`
**Instructions**:
- `core-development.instructions.md` (mandatory)
- `copilot-instructions.md` (project-wide guidelines)

## Technology-Specific Roles

### Desktop & Revit (.NET) Role
**Files**: `src/desktop-app/**/*.cs`, `src/revit-plugin/**/*.cs`, `**/*.xaml`
**Instructions**:
- `dotnet-backend.instructions.md`
- `ux-ui-design.instructions.md` 
- `revit-architecture.instructions.md`
- `revit-workflow.instructions.md`

### Python FastAPI Role  
**Files**: `src/cloud-server/**/*.py`, `**/*.toml`, `**/*.ini`
**Instructions**:
- `python-fastapi.instructions.md`
- `api-standards.instructions.md`
- `error-handling.instructions.md`
- `logging-standards.instructions.md`

### Web Frontend Role
**Files**: `**/*.tsx`, `**/*.jsx`
**Instructions**:
- `web-typescript-react.instructions.md`
- `ux-ui-design.instructions.md`
- `code-style.instructions.md`

### DevOps Role
**Files**: `**/*.yml`, `**/*.yaml`, `**/Dockerfile*`, `**/*.ps1`, `**/*.sh`, `**/*.tf`, `**/*k8s*.y*ml`
**Instructions**:
- `devops.instructions.md`
- `performance-optimization.instructions.md`

## Domain-Specific Roles

### AI Integration Role
**Files**: `src/cloud-server/**/*.py`, `src/desktop-app/**/*.cs`, `src/revit-plugin/**/*.cs`, `**/*.ts`, `**/*.tsx`, `**/*.js`, `**/*.jsx`
**Instructions**:
- `ai-integration.instructions.md`
- `ai-prompt-standards.instructions.md`
- `data-structures.instructions.md`

### Architect Role
**Files**: `**/*.md`, `**/*.json`, `**/*.yml`, `**/*.yaml`, `docs/**/*`, `configs/**/*`
**Instructions**:
- `architect.instructions.md`

### QA & Security Role  
**Files**: `**/*test*.*`, `**/*spec*.*`, `**/*.feature`, `**/*.cy.*`, `**/*`
**Instructions**:
- `qa.instructions.md`
- `registry-governance.instructions.md`

### Monetization & Business Role
**Files**: `src/cloud-server/**/*.py`, `src/revit-plugin/**/*.cs`, `**/*.md`
**Instructions**:
- `monetization-strategy.instructions.md`

## Role Application Rules

### Automatic Attachment Priority:
1. **Universal Roles** (Core Development) - always applied to all files
2. **Technology-Specific Roles** - based on file extensions and paths  
3. **Domain-Specific Roles** - based on file paths and content context
4. **Business Logic Roles** - for relevant features and business logic

### File Pattern Matching:
- Use glob patterns for automatic role detection
- Multiple roles can apply simultaneously for comprehensive coverage
- Technology roles override general patterns when more specific

### Manual Override:
- Developers can manually reference specific instruction files when needed
- Use `@apply` directive in comments to force inclusion of specific roles
- Context-sensitive application based on current development task

### Role Conflict Resolution:
- More specific roles take precedence over general ones
- Technology-specific roles override domain-specific for technical decisions  
- Universal rules (Core Development) always apply and cannot be overridden
- Business rules apply when implementing monetization or user-facing features

## Compliance Requirements

### Mandatory for All Code:
- **Core Development** rules must always be followed
- **Security** considerations apply to all file types
- **Registry Management** required for any public contract changes

### Technology-Specific Compliance:
- **.NET files** must follow dotnet-backend + UX/UI design patterns
- **Python files** must follow FastAPI + API standards + logging patterns  
- **React/TypeScript** must follow web frontend + UX/UI design standards
- **Infrastructure files** must follow DevOps + performance optimization

### Domain-Specific Compliance:
- **AI Integration** required when working with ML models, prompts, or AI workflows
- **Architecture** decisions must be documented for system design changes
- **Monetization** rules apply when implementing billing, subscriptions, or usage tracking

## Usage Examples

### Example 1: Editing a React Component
**File**: `src/web-ui/components/AILayoutGenerator.tsx`
**Auto-Applied Roles**:
- Core Development (universal)
- Web Frontend Role (*.tsx)
- AI Integration Role (AI-related component)
- UX/UI Design (inherited from Web Frontend)

### Example 2: Editing Python API Endpoint  
**File**: `src/cloud-server/api/layout_generation.py`
**Auto-Applied Roles**:
- Core Development (universal)
- Python FastAPI Role (cloud-server/*.py)
- AI Integration Role (AI-related endpoint) 
- API Standards (inherited from FastAPI)

### Example 3: Infrastructure Configuration
**File**: `k8s/monitoring/deployment.yml`  
**Auto-Applied Roles**:
- Core Development (universal)
- DevOps Role (*.yml in k8s/)
- Performance Optimization (inherited from DevOps)

### Example 4: Revit Plugin Development
**File**: `src/revit-plugin/Commands/GenerateLayoutCommand.cs`
**Auto-Applied Roles**:
- Core Development (universal)
- Desktop & Revit (.NET) Role (revit-plugin/*.cs)
- Revit Architecture (specific to Revit development)
- Revit Workflow (command patterns)

## Quality Assurance

### Pre-Development Checks:
- [ ] Identify file patterns and applicable roles
- [ ] Load all relevant instruction files
- [ ] Check for role conflicts and resolution strategy
- [ ] Validate compliance requirements for target roles

### Post-Development Validation:
- [ ] Verify compliance with all applicable role requirements  
- [ ] Check technology-specific standards adherence
- [ ] Validate domain-specific pattern implementation
- [ ] Ensure universal rules (Core Development) compliance

This role assignment system ensures comprehensive, context-aware development guidance while maintaining consistency across the ArchBuilder.AI codebase.