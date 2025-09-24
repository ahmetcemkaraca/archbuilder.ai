# AGENTS.md — Revit Addin Code

Commands, Services, UI, Validation for the add-in.

## Active Rules (MDc)
- `.cursor/rules/instructions-universal-agent.mdc`
- `.cursor/rules/instructions-revit-architecture.mdc`
- `.cursor/rules/instructions-revit-workflow.mdc`
- `.cursor/rules/instructions-ux-ui-design.mdc`
- `.cursor/rules/instructions-dotnet-backend.mdc`

## When to consult which rules
- Revit API transactions/commands: Revit Workflow.
- Ribbon/UX and dialogs: UX/UI Design.
- Family/element interactions: Revit Architecture.
- Error handling/logs: Universal + .NET Backend patterns.
