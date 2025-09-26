---
applyTo: "**/*"
description: Role-based instruction attachment system for context-aware development across all file types.
---

# Role-Based Instruction System

## Overview
This file defines which instruction files should be automatically attached based on file types and project contexts to ensure role-appropriate guidance during development.

## Role Attachment Rules

### Architect Role
**When working with:** Design documents, configuration files, system architecture
**Files:** `**/*.md`, `**/*.ts`, `**/*.tsx`, `**/*.js`, `**/*.jsx`, `**/*.py`, `**/*.cs`, `**/*.json`, `**/*.yml`, `**/*.yaml`
**Instructions:**
- architect.instructions.md
- architecture-decisions.instructions.md

### Developer Role  
**When working with:** Any development files
**Files:** `**/*`
**Instructions:**
- developer.instructions.md
- code-style.instructions.md
- naming-conventions.instructions.md

### DevOps Role
**When working with:** Infrastructure, deployment, and configuration files
**Files:** `**/*.yml`, `**/*.yaml`, `**/Dockerfile*`, `**/*.ps1`, `**/*.sh`, `**/*.tf`, `**/*k8s*.y*ml`
**Instructions:**
- devops.instructions.md
- performance-optimization.instructions.md

### Desktop & Revit (.NET) Role
**When working with:** Desktop application and Revit plugin files
**Files:** `src/desktop-app/**/*.cs`, `src/revit-plugin/**/*.cs`, `**/*.xaml`
**Instructions:**
- dotnet-backend.instructions.md
- ux-ui-design.instructions.md
- revit-architecture.instructions.md
- revit-workflow.instructions.md

### Python FastAPI Role
**When working with:** Cloud server backend files
**Files:** `src/cloud-server/**/*.py`, `**/*.toml`, `**/*.ini`
**Instructions:**
- python-fastapi.instructions.md
- api-standards.instructions.md
- error-handling.instructions.md
- logging-standards.instructions.md

### AI Integration Role
**When working with:** AI model integration and prompt engineering
**Files:** `src/cloud-server/**/*.py`, `src/desktop-app/**/*.cs`, `src/revit-plugin/**/*.cs`, `**/*.ts`, `**/*.tsx`, `**/*.js`, `**/*.jsx`
**Instructions:**
- ai-integration.instructions.md
- ai-prompt-standards.instructions.md
- data-structures.instructions.md

### Web Frontend Role
**When working with:** Next.js/React frontend files
**Files:** `**/*.tsx`, `**/*.jsx`
**Instructions:**
- web-typescript-react.instructions.md
- ux-ui-design.instructions.md
- architecture-decisions.instructions.md
- code-style.instructions.md

### QA & Security Role
**When working with:** All files (universal application)
**Files:** `**/*`
**Instructions:**
- qa.instructions.md
- security.instructions.md
- registry-governance.instructions.md
- vibe-coding-checkpointing.instructions.md

### Monetization & Business Role
**When working with:** Business logic and monetization features
**Files:** `src/cloud-server/**/*.py`, `src/revit-plugin/**/*.cs`, `**/*.md`
**Instructions:**
- monetization-strategy.instructions.md

## Usage Guidelines

### Automatic Attachment
- Instructions should be automatically attached based on file patterns being edited
- Multiple roles can apply simultaneously for comprehensive coverage
- Always include universal roles (Developer, QA & Security) for all file types

### Manual Override
- Developers can manually reference specific instruction files when needed
- Use `@apply` directive to force inclusion of specific role instructions
- Context-sensitive application based on current development task

### Priority Order
1. Universal roles (Developer, QA & Security) - always applied
2. Technology-specific roles based on file extensions
3. Domain-specific roles based on file paths
4. Business logic roles for relevant features

## Compliance Requirements
- All code changes must follow at least the Developer and Security role instructions
- Technology-specific roles are mandatory for their respective file types
- Architecture changes require Architect role instruction compliance
- CI/CD changes require DevOps role instruction compliance