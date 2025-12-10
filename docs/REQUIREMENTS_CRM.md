# CRM Requirements – Autonomous TODO Intelligence

Status: **Partial** (v2 heuristics and UI are live; data-driven tuning and richer analytics remain).

## Implemented in v2
- Review queue heuristics split **high-confidence auto-apply** from **low-confidence/ambiguous queue**; reasons include low confidence, dependency conflicts, and duplicate matches.
- **Dependency-aware automation**: completion and add flows honor dependency hints/blocked phrasing and push risky items to review; dependency badges/hints surface in suggestions and audit notes.
- **Review queue UI**: shows confidence, priority chips, dependency badges, matched text, and reason; approve/dismiss requires a reason and applies/cleans up the suggestion accordingly.
- **Telemetry**: counters for auto-applied vs queued vs dismissed/ignored suggestions plus auto-add/auto-complete/dedupe; manual vs auto suggestions are recorded and visible in the Usage dashboard and exports.
- **Auditability**: `auto_notes` carry dependency hints and rationale for applied/queued/dismissed actions so Tasks and Usage views stay explainable.

## Remaining / Future
- **Data-driven tuning** of thresholds/weights using real telemetry (still future; keep status Partial).
- **TaskDependency graph + autopilot ordering** and deeper analytics/persistence in the dashboard.

## References & validation
- Docs: `docs/TODO_CHECKLIST.md`, `docs/PROGRESS.md` (2025-12-10 Autonomous TODO v2), `docs/USER_MANUAL.md` (§Tasks/Review queue), `docs/USAGE_TELEMETRY_DASHBOARD.md`, `docs/tasks/AUTOMATION.md`.
- Tests/coverage: `qa/tests_api/test_tasks_automation_audit.py`, `qa/tests_api/test_usage_telemetry_dashboard.py`, Playwright `frontend/tests/tasks-suggestions.spec.ts` and `tasks-confidence.spec.ts`; CI via `make ci` with `LLM_MODE=stub` and `VECTORSTORE_MODE=stub`.

