# AGENTS.md — AI (Models, Prompts, Validation)

This folder contains AI model selection, prompt templates, and validation logic.

## Active Rules (MDc)
- `.cursor/rules/instructions-ai-integration.mdc`
- `.cursor/rules/instructions-ai-prompt-standards.mdc`
- `.cursor/rules/instructions-data-structures.mdc`
- `.cursor/rules/instructions-logging-standards.mdc`
- `.cursor/rules/instructions-error-handling.mdc`
- `.cursor/rules/instructions-performance-optimization.mdc`

## When to consult which rules
- Model selection or provider clients: AI Integration, Performance Optimization.
- Prompt changes/templates: AI Prompt Standards.
- Output schemas (JSON) & contracts: Data Structures.
- Validators (schema/geometry/building code): Data Structures, Error Handling.
- Telemetry for AI calls: Logging Standards.
