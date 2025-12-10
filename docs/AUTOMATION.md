# Task Automation Overview (Autonomous TODO v2)

This is a short overview of the current Tasks automation behavior. For full API shapes and deeper notes, see `docs/tasks/AUTOMATION.md`.

## Current behavior
- After each `/chat`, the maintainer auto-adds/completes/dedupes tasks using confidence scoring and dependency/blocked context.
- **Review queue v2** splits high-confidence auto-apply from queued suggestions; queue reasons include low confidence, dependency blocks, and duplicate matches. Approve/dismiss requires a reason.
- **Dependency-aware guardrails**: dependency hints block risky auto-closes and show as badges/notes in suggestions and audit history.

## Telemetry & UI
- Task counters include auto-added/auto-completed/auto-deduped plus suggestion counters (auto_applied/queued/dismissed/ignored); recent actions list carries confidence, priority/group, blocked/dependency hints, and audit notes.
- Usage tab dashboard/exports surface these counters with action/group/model filters and time windows.
- Tasks tab review queue shows confidence, priority chips, dependency badges, matched text, and reasons; archived projects are read-only and disable review queue actions.

## References & validation
- Docs: `docs/REQUIREMENTS_CRM.md`, `docs/TODO_CHECKLIST.md`, `docs/PROGRESS.md` (2025-12-10 Autonomous TODO v2), `docs/USER_MANUAL.md` (§6), `docs/USAGE_TELEMETRY_DASHBOARD.md`.
- Tests: `qa/tests_api/test_tasks_automation_audit.py`, `qa/tests_api/test_usage_telemetry_dashboard.py`, Playwright `frontend/tests/tasks-suggestions.spec.ts`, `frontend/tests/tasks-confidence.spec.ts`.

