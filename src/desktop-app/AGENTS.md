# AGENTS.md — Desktop App (WPF)

This folder contains the Windows desktop application. Follow the rules below for .NET/WPF and UX.

How AGENTS.md works: read `.mds/rules.md` for nested rule behavior and usage.

## Active Rules to Consult (MDc locations)
- `.cursor/rules/instructions-universal-agent.mdc`
- `.cursor/rules/instructions-dotnet-backend.mdc`
- `.cursor/rules/instructions-ux-ui-design.mdc`
- `.cursor/rules/instructions-revit-architecture.mdc`
- `.cursor/rules/instructions-revit-workflow.mdc`
- `.cursor/rules/instructions-qa.mdc`
- `.cursor/rules/instructions-security.mdc`
- `.cursor/rules/instructions-code-style.mdc`
- `.cursor/rules/instructions-naming-conventions.mdc`

## Coding-time Checklist
- Target .NET runtime compatible with Revit-supported framework.
- MVVM and transaction-safe integration patterns.
- UI text via i18n; no hardcoded strings.
- Structured logging and error taxonomy.
- Small, reversible edits; CI stays green.
