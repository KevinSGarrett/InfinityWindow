# REQUIREMENTS_CRM

This stub captures the CRM requirements for InfinityWindow. Full details are being authored separately; until then, this placeholder keeps the canonical docs set intact for CI and points readers to `SYSTEM_OVERVIEW.md` and `MODEL_MATRIX.md` for related context.
# InfinityWindow – Requirements CRM

## Source of truth
- Latest project plans — `Project_Plan_003_UPDATED.txt` plus the `Updated_Project_Plan_2_*.txt` set — are the design spec of record.
- Newer plans supersede older ones; `Project_Plan_001_ORIGINAL.txt` and `Project_Plan_002_NEW_FEATURES.txt` remain archived for historical context.
- Pipeline: Plans → CRM → `TODO_CHECKLIST.md` / `PROGRESS.md` → implementation + tests.
- CRM merges the latest plans with the implemented system and assigns each requirement a status (**Implemented / Partial / Not started**).
- `docs/TODO_CHECKLIST.md` and `docs/PROGRESS.md` are derived from this CRM and must stay in sync with it.
- When CRM/docs/tests disagree with the latest plans, treat that as an alignment bug: fix CRM/docs/tests (and the plan, if it was wrong) rather than treating drift as the new spec.
- Canonical docs guardrail: `backend/app/api/main.py` exposes `CANONICAL_DOC_PATHS` and `/debug/docs_status`; QA covers both via `qa/tests_docs/test_docs_existence.py` and `qa/tests_api/test_docs_status.py` to prevent docs drift.

## Requirement clusters & status
Status labels here mirror `PROGRESS.md` and `TODO_CHECKLIST.md` and reference the latest plans.

| Area / capability | Plan reference | Status | Notes |
| --- | --- | --- | --- |
| Task-aware auto-mode routing | `Project_Plan_003_UPDATED.txt` | Partial | Heuristic routing, telemetry, and UI override shipped; data-driven refinement and richer override surfaces are planned. |
| Autonomous TODO intelligence | `Project_Plan_003_UPDATED.txt` | Partial | Auto add/complete/dedupe with audit notes shipped; TaskDependency model + dependency-aware automation (blocked auto-completion, dependency actions telemetry) are live; full graph-driven planning/Autopilot manager behavior remains design-only (future). |
| Usage & telemetry dashboard | `Updated_Project_Plan_2_Model_Matrix.txt` | Partial | Phase 2 charts/filters/exports are live; long-window persistence/analytics remain planned. |
| Enhanced retrieval & context shaping | `Project_Plan_003_UPDATED.txt` | Not started | Retrieval tuning/context-shaping items are future; no implementation yet. |
| Repo ingestion & vector store | `Updated_Project_Plan_2_Ingestion_Plan.txt` | Implemented | Batched repo ingestion with progress/skip-on-hash is live; blueprint/plan ingestion remains design-only. |
| Filesystem safety & Files tab UX | `Project_Plan_003_UPDATED.txt` | Implemented | Scoped filesystem + Files tab (diff/preview) are live; guardrails enforced in API/UI. |
| Docs alignment & canonical docs guardrails | `Project_Plan_003_UPDATED.txt` | Implemented | Canonical docs are listed in `CANONICAL_DOC_PATHS` and surfaced via `/debug/docs_status`, guarded by `qa/tests_docs/test_docs_existence.py` and `qa/tests_api/test_docs_status.py`. |
| Autopilot / Blueprint / Learning | `Updated_Project_Plan_2*.txt`, `docs/AUTOPILOT_*.md` | Not started (design-only) | Manager/Workers/Blueprint/Learning are design-only; see Updated_Project_Plan_2 set and AUTOPILOT docs; status tracked in CRM/TODO/PROGRESS. |

