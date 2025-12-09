# REQUIREMENTS_CRM

This stub captures the CRM requirements for InfinityWindow. Full details are being authored separately; until then, this placeholder keeps the canonical docs set intact for CI and points readers to `SYSTEM_OVERVIEW.md` and `MODEL_MATRIX.md` for related context.
# REQUIREMENTS_CRM

This stub captures the CRM requirements for InfinityWindow. Full details are being authored separately; until then, this placeholder keeps the canonical docs set intact for CI and points readers to `SYSTEM_OVERVIEW.md` and `MODEL_MATRIX.md` for related context.
# InfinityWindow – Requirements CRM

## Source of truth
- Latest project plans – `Project_Plan_003_UPDATED.txt` and the `Updated_Project_Plan_2_*.txt` set – are the design spec of record. Newer plans supersede older ones.
- This CRM merges those plans with the implemented system (code + tests) to label each requirement **Implemented / Partial / Not started**.
- `docs/TODO_CHECKLIST.md` and `docs/PROGRESS.md` are backlog/status views derived from this CRM and must stay in sync with it.
- Older `Project_Plan_001_ORIGINAL.txt` and `Project_Plan_002_NEW_FEATURES.txt` are archived for historical context only.
- If CRM/docs/tests ever disagree with the latest plans, treat it as an alignment issue and update CRM/docs/tests (and plans, if the plan is wrong) rather than accepting the drift.

## Requirement clusters & status (unchanged)
These status labels reflect the current code/tests and mirror the roadmap in `PROGRESS.md` / `TODO_CHECKLIST.md`.

| Area / capability | Plan reference | Status | Notes |
| --- | --- | --- | --- |
| Core platform: projects, conversations, chat modes, docs/memory/decisions, filesystem/terminal, usage logging | `Project_Plan_003_UPDATED.txt` | Implemented | Matches current backend/frontend; tracked in SYSTEM_MATRIX and PROGRESS. |
| Tasks + automation + telemetry polish | `Project_Plan_003_UPDATED.txt` | Partial | Core task loop, dedupe, completion, telemetry shipped; heuristics/review queue continue to iterate. |
| Ingestion + search (batched repo/doc ingest, search endpoints, UI progress) | `Updated_Project_Plan_2_Ingestion_Plan.txt` | Implemented | Batching, progress, and skip-on-hash are live; future blueprint ingest remains design-only. |
| Usage/telemetry dashboard | `Updated_Project_Plan_2_Model_Matrix.txt` | Partial | Phase 2 dashboards/filters are live; long-term analytics/persistence remain planned. |
| Autopilot Blueprint/Plan graph + ExecutionRuns/Manager/Workers | `Updated_Project_Plan_2.txt`, `Updated_Project_Plan_2_Phase3_4.txt`, `Updated_Project_Plan_2_Worker_Manager_Playbook.txt` | Not started (design-only) | No Autopilot/Blueprint/Run code is present; designs live in the plans and AUTOPILOT docs. |
| Learning layer & plan refinement | `Updated_Project_Plan_2_AUTOPILOT_LEARNING.txt` | Not started (design-only) | Learning metrics/refinement remain future; not implemented today. |