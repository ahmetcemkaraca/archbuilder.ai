# AGENTS.md — Revit Plugin

This folder contains the Revit Add-in. Follow Revit API patterns, safe transactions, and UI/UX for architects.

See `.mds/rules.md` for AGENTS.md behavior and nested rules.

## Active Rules to Consult (MDc locations)
- `.cursor/rules/instructions-universal-agent.mdc`
- `.cursor/rules/instructions-dotnet-backend.mdc`
- `.cursor/rules/instructions-revit-architecture.mdc`
- `.cursor/rules/instructions-revit-workflow.mdc`
- `.cursor/rules/instructions-ux-ui-design.mdc`
- `.cursor/rules/instructions-qa.mdc`
- `.cursor/rules/instructions-security.mdc`

## Coding-time Checklist
- Wrap element creation in Revit Transactions; provide rollback.
- Validate element references; avoid duplicates.
- i18n for UI; logs/comments in Turkish.
- Ensure compatibility with target Revit version/framework.
