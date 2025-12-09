# InfinityWindow Autopilot Plan (Design)

Status: **Design-only. Autopilot is not implemented.** Current automation stops at task upkeep/hooks after `/chat`. Keep status aligned with `docs/PROGRESS.md`, `docs/TODO_CHECKLIST.md`, and `docs/AUTOPILOT_IMPLEMENTATION_CHECKLIST.md`.

Sources:
- `Project_Plans/Updated_Project_Plans/Updated_Project_Plan_2.txt`
- `Project_Plans/Updated_Project_Plans/Updated_Project_Plan_2_Phase3_4.txt`

---

## Purpose

Explain how InfinityWindow will grow from today’s chat + tasks + files + terminal workflow into a managed project execution engine with blueprints, structured plans, and safe automation. Nothing below is live yet.

---

## Phase summary (design targets)

### Phase 1 – Blueprint & Plan graph
- Models: `Blueprint`, `PlanNode`, `PlanNodeTaskLink`, `TaskDependency`, `BlueprintIngestionJob`.
- Endpoints: create/list/update blueprints; generate PlanNode trees; generate tasks for nodes.
- UI: Blueprint selector + Plan tree inside the Tasks tab; “Generate tasks for this node”.

### Phase 3 – Execution runs & workers
- Models: `ExecutionRun`, `ExecutionStep` with rollback and telemetry links.
- Services: `runs.py`, `workers.py`; tool-calling via Files/Terminal/Search with alignment checks.
- Endpoints: create/list runs, advance, rollback, fetch run detail.
- UI: Runs panel/tab with step list, diffs, approval gates.

### Phase 4 – ManagerAgent & autonomy modes
- Project fields: `autonomy_mode` (`off|suggest|semi_auto|full_auto`), `active_phase_node_id`, `autopilot_paused`, `max_parallel_runs`.
- Services: `manager.py` (ManagerAgent), `intent_classifier.py`.
- Endpoints: `/projects/{id}/autopilot_tick`, `/projects/{id}/manager/plan`, `/projects/{id}/refine_plan`.
- UI: Header controls for Autopilot mode/pause/status + “Explain plan” view.

### Supporting ingestion & context (Phase T + Phase 2)
- Batching + token-aware ingestion (`IngestionJob`, `FileIngestionState`, `BlueprintSectionSummary`).
- Context builder, conversation summaries, and project snapshots to keep LLM calls grounded.

---

## How this ties to the current system

- Builds **on top of** existing Projects/Tasks/Docs/Memory; workers use the same Files/Terminal/Search endpoints with stricter guardrails.
- Uses the planned role-based model routing in `docs/MODEL_MATRIX.md`.
- Safety rules and limits are captured in `docs/AUTOPILOT_LIMITATIONS.md`; the learning layer is in `docs/AUTOPILOT_LEARNING.md`.

---

## When implementation starts

1. Walk the short checklist in `docs/AUTOPILOT_IMPLEMENTATION_CHECKLIST.md` (all items are currently Not started).
2. Update `SYSTEM_OVERVIEW.md`, `SYSTEM_MATRIX.md`, `CONFIG_ENV.md`, and `API_REFERENCE.md` as endpoints and models land.
3. Add QA probes and test plan entries before turning on any autonomy beyond suggest.
