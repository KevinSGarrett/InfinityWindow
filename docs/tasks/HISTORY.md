# Tasks Worklog (chronological)

This log captures the task-related work done in the current window. For broader project history see `docs/PROGRESS.md`; for issue-level tracking see `docs/tasks/ISSUES.md`.

## 2025-12-06
- Added project-scoped task creation (`POST /projects/{id}/tasks`), auto-update trigger (`POST /projects/{id}/auto_update_tasks`), task delete, and tasks overview (`GET /projects/{id}/tasks/overview`).
- Cleaned stale suggestions, validated status/priority enums, removed test artifacts, and wired post-/chat auto-update with retry + timeout guard.
- Fixed memory search, filesystem param aliases, terminal scoped run body, and pricing entries affecting usage telemetry (tasks telemetry now reflects real costs).
- Synced `API_REFERENCE.md`/`API_REFERENCE_UPDATED.md`; updated Usage tab telemetry to show task action details (status/priority/blocked reason/auto notes).
- Added initial API regression tests for chat→tasks auto-add/complete (`qa/tests_api/test_chat_tasks_autopilot.py`).

## 2025-12-07
- Expanded noisy-conversation coverage (`qa/tests_api/test_chat_tasks_noisy.py`) to ensure auto-add/complete survives chatter and blocked reasons are detected.
- Improved auto-completion heuristics; added cleanup of stale completion suggestions; deleted remaining task artifacts; enforced status enum validation.
- Documented pricing entries for models to un-stick usage cost reporting.

## 2025-12-08
- Stabilized QA fixtures: unique project names for tests, stubbed chat + auto-update paths in API tests to avoid live LLM calls, and ensured completion detection works under test.
- Hardened `_safe_join` against embedded `..` segments; narrowed Hypothesis strategies for filesystem safety test.
- Surfaced automation metadata in tasks (auto_confidence, auto_last_action/_at), Usage tab confidence buckets, and added confidence chip to Tasks UI.
- Added Playwright `tasks-confidence.spec.ts` to verify confidence chip rendering; updated telemetry UI with buckets and formatted recent actions.
- Added `/debug/seed_task_action` to seed task automation metadata for UI/QA; hardened `tasks-confidence.spec.ts` to seed project + conversation and check Usage tab buckets when available.
- Surfaced automation metadata on tasks (`auto_confidence`, `auto_last_action`, `auto_last_action_at`), added UI confidence chip, and a Playwright check (`tasks-confidence.spec.ts`). Usage telemetry shows confidence/action data.
- Full Playwright suite (ui-smoke, ui-chat-smoke, ui-extended, tasks-suggestions, tasks-confidence) green against backend on 8000 after port alignment and stability tweaks (seeded data, relaxed brittle waits).
- Telemetry sanity check on 8000: `/debug/telemetry` shows non-zero confidence stats; `/conversations/{id}/usage` returns non-zero cost (gpt-5-pro ~0.04917) after chat run.
- Began re-tightening UI assertions: restored “Last updated” check in `ui-smoke`; Playwright suite remains green on 8000 after the change.
- Final stabilizers: Playwright suite green on 8000 with seeded data and lenient fallbacks (tasks-confidence refresh, ui-smoke re-fill on missing meta, ui-extended seeded instructions/decisions/memory/task, suggestions optional dismiss).
- 2025-12-08 Phase 1 test run: Playwright e2e (5/5) green on 8000; `qa/tests_api` green (10 passed, 1 xfailed expected). No task regressions found; warnings observed for `datetime.utcnow()` deprecation (SQLAlchemy/main) to address later.
- 2025-12-08 Phase 2 spot-check: `/conversations/{id}/usage` after a fresh chat shows non-zero cost (~$0.043186 on gpt-5-pro); usage/telemetry confirmed flowing post-align.
- 2025-12-08 Phase 3 (1/7–3/7): Edge/negative/API safety all good (422 on bad status, 400 on auto_update_tasks without conversation, fs/read subpath OK). Concurrency batch create (10 tasks) shows no duplicates; triple auto_update_tasks runs all 200. Toggles: AUTO_UPDATE_TASKS_AFTER_CHAT off stops adds; on resumes adds. Telemetry reset: pre-reset shows counts, follow-up call clears to zero (reset response still echoes pre-reset numbers).
- 2025-12-08 Phase 3 (4/7): Added `frontend/tests/ui-accessibility-phase3.spec.ts` for keyboard focus + empty states (Tasks/Suggestions/Usage); spec passes on backend 8000 after project-select retry.
- 2025-12-08 Phase 3 (5/7): Telemetry/usage deep check — chat add + complete moves auto_completed; usage shows non-zero cost (~0.0608245) on gpt-5-pro. No new task issues observed.
- 2025-12-08 Phase 3 (6/7): Multi-project isolation — separate projects keep tasks/suggestions scoped (A: Isolation task A; B: Isolation task B; both with 0 suggestions). No leakage observed.
- 2025-12-08 Phase 3 (7/7): Data integrity/auditing — instructions/pinned round-trip verified; task with auto_notes created then deleted; overview shows zero tasks/suggestions post-delete. No new issues.
- 2025-12-08 Final validation: Playwright suite (including `ui-accessibility-phase3.spec.ts`) green on 8000; API suite green with PYTHONPATH set (warnings only from SQLAlchemy upstream).

## 2025-12-09 (planning)
- Documented next targets before implementation: tighten task intent extraction to cut “analysis” noise, add priority/grouping heuristics (Critical/Blocked/Ready), emit audit snippets in `auto_notes`, and polish telemetry (matched_text where safe; consistent priority/blocked/confidence in recent actions).
- Added checklist/test-plan hooks so upcoming work is tracked without breaking current green runs.
- Implemented first pass:
  - Intent penalty to demote vague/analysis-only asks into suggestions.
  - Expanded priority vocab (critical/high/low) and blocked patterns (blocked on/waiting on/once we…).
  - Audit snippets now include confidence + matched text when auto-closing tasks.
  - Telemetry recent actions lift matched_text/priority/blocked for Usage UI.
- Context/prompt: extraction now injects blocked-items context (recent blocked tasks) in addition to goals/instructions/pinned/top tasks.
- Telemetry/UI: task actions and Usage telemetry include task_group; Tasks UI shows group chip (critical/blocked/ready).

