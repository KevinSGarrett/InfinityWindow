# Task-Specific Issues Log

This file tracks issues focused on tasks/automation. Source of truth remains `docs/ISSUES_LOG.md`; this view is scoped to task-related items.

| ID        | Symptoms / Impact                                                                  | Resolution & References                                                                                  | Status |
|-----------|------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|--------|
| ISSUE-017 | Chat → tasks auto-add flaky; first phrasing failed, later succeeded.               | Added post-/chat auto-update hook with retry; retested via chat and API regressions (`B-Tasks-E2E`).     | Resolved |
| ISSUE-018 | Auto task upkeep not automatic; needed explicit `auto_update_tasks`.               | Auto-update now runs after `/chat` by default (`AUTO_UPDATE_TASKS_AFTER_CHAT`); manual endpoint retained.| Resolved |
| ISSUE-019 | `POST /projects/{id}/auto_update_tasks` intermittently 503.                         | Added `_run_auto_update_with_retry` and clearer errors; double-run succeeds.                            | Resolved |
| ISSUE-020 | AI file edit target missing (`docs/tasks/login-page-epic.md`).                      | Added placeholder file and guard to skip missing targets.                                               | Mitigated |
| ISSUE-021 | Completion detection gap (“we finished X” not closing tasks).                       | Lowered completion thresholds, expanded phrase matching; validated with fresh task closure.             | Resolved |
| ISSUE-022 | Stale completion suggestions for already-done tasks.                                | Added stale suggestion cleanup; no pending completes for done tasks after cleanup.                      | Resolved |
| ISSUE-023 | Test artifacts left in task list (ids 109/110/111/113/114/116).                     | Implemented `DELETE /tasks/{id}` and removed artifacts.                                                 | Resolved |
| ISSUE-024 | Task status validation missing (accepted `badstatus`).                             | Enum validation added to `TaskUpdate`; invalid statuses now 422; patched bad data.                      | Resolved |
| ISSUE-025 | Deprecation warnings (`datetime.utcnow()` in SQLAlchemy/main) during tests_api run. | Replaced app usage with `datetime.now(timezone.utc)` in `app/api/main.py` and `ingestion/github_ingestor.py`; remaining warnings originate from SQLAlchemy internals (schema.py) and are upstream-only. | Accepted (Upstream) |
| ISSUE-026 | None (Phase 1 + Phase 2 + Phase 3 1-4 checks)                                      | Playwright e2e (5/5) green on 8000; `qa/tests_api` green; usage cost non-zero; Phase 3 so far clean.    | No issues |
| ISSUE-027 | Telemetry reset response echoes pre-reset counts                                   | Adjusted reset to clear before snapshot; response now shows cleared counters after reset.               | Resolved |

Notes:
- General issue history (including non-task items) lives in `docs/ISSUES_LOG.md`.
- Task automation telemetry and endpoints are documented in `docs/tasks/AUTOMATION.md`.

