# Changelog

## [Unreleased]
- Registry validation: pending local script execution (pwsh not available). Use CI pipeline.

## [Phase 10] - Error Handling Enhancements
- Added `RevitAutoPlanException` base with `RevitAPIException` and `RevitTransactionFailedException`.
- Integrated user-friendly TR messages and journal logging in `InitializePhaseNineCommand`.

## [Phase 9] - Phase Management
- Implemented `PhaseManager` with create/list/set APIs.
- Added `InitializePhaseNineCommand` and Ribbon button (AutoPlan AI → Phase 9).
- i18n strings for all user messages; removed hardcoded UI text.
- Revit 2026 compatibility checks and safe null-guards.
- Smoke test documentation under `docs/services/project-service.md`.
