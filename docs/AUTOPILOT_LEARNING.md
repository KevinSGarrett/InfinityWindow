# InfinityWindow Autopilot – Project Learning Layer (Design)

Status: Design only – not implemented yet. Current automation is limited to task upkeep/hooks after `/chat`; learning-layer models, metrics, and endpoints are not shipped. Keep alignment with `docs/PROGRESS.md`, `docs/TODO_CHECKLIST.md`, and the planned API notes in `docs/API_REFERENCE_UPDATED.md` section 11.

This document summarizes the **Project Learning Layer** for InfinityWindow Autopilot, based on `Updated_Project_Plans/Updated_Project_Plan_2_AUTOPILOT_LEARNING.txt`. It describes how future versions of InfinityWindow should “learn the project” over time without fine‑tuning models.

---

## 1. Concept

“Learning the project” means:

1. **Observing execution**
   - For each `ExecutionRun` and `ExecutionStep`, record how hard the work was, how many failures occurred, and where specs/code were fragile.
2. **Recording structured learning**
   - Encode signals into models:
     - `Task`: difficulty score, rework count, planned vs actual PlanNode, actual start/finish times.
     - `PlanNode`: learned priority, learned risk, inferred dependencies.
     - `ExecutionRun`: outcome and learning notes.
3. **Adapting the plan**
   - ManagerAgent uses these signals to:
     - Re‑order tasks and phases.
     - Split or merge tasks.
     - Propose spikes/prototypes where specs are unclear.
     - Suggest blueprint pivots when new versions land.
4. **Respecting blueprints, but not worshipping them**
   - Blueprints are **versioned inputs**, not immutable truth.
   - The build strategy improves over time as the project is built and tested.

---

## 2. Planned Data Model Extensions

All of these are **future** additions to `backend/app/db/models.py`:

### 2.1 Task learning fields

Extend `Task` with:

- `difficulty_score: int | None` – 1..5, derived from run stats.
- `rework_count: int` – number of times reopened or follow‑up created.
- `planned_phase_node_id`, `actual_phase_node_id` – links into the PlanNode tree.
- `actual_started_at`, `actual_completed_at` – timestamps derived from the runs that touched the task.

### 2.2 PlanNode learning fields

Extend `PlanNode` with:

- `learned_priority: "low" | "normal" | "high"`
- `learned_risk_level: "low" | "normal" | "high"`
- `inferred_dependency_json: JSON` – high‑level dependencies between PlanNodes.

### 2.3 ExecutionRun learning fields

Extend `ExecutionRun` with:

- `outcome: "success" | "failed_tests" | "code_error" | "blocked" | "cancelled" | "unknown"`
- `learning_notes: Text` – 1–5 sentences describing what was learned.

---

## 3. Blueprint Understanding Pipeline

When a large blueprint is ingested and a PlanNode tree is generated (Phase 1), the Learning Layer adds:

1. **Blueprint understanding docs**
   - New module: `backend/app/services/blueprint_understanding.py`.
   - Function: `build_blueprint_understanding(blueprint_id: int)`.
   - Steps:
     - Serialize PlanNode tree (phases/epics/features/stories) as JSON.
     - Call LLM (deep/research model) to produce:
       - Architecture overview.
       - Foundational requirements.
       - Non‑functional requirements.
       - Proposed build sequence.
     - Store results as `Document` rows (e.g., kind = `blueprint_architecture`, `blueprint_foundations`, `blueprint_build_sequence`).

2. **PlanNode annotations**
   - Use these docs + PlanNode summaries to:
     - Initialize `learned_priority`.
     - Initialize `learned_risk_level`.
     - Fill `inferred_dependency_json`.

3. **Blueprint Learning Snapshot**
   - Create a “Blueprint Learning Snapshot vN” document summarizing:
     - Key architectural decisions.
     - MVP set and phases.
     - Known uncertainties.

ManagerAgent consults these understanding docs whenever planning work or performing retrospectives.

---

## 4. Run‑Time Learning from Execution

### 4.1 Recording outcomes

ManagerAgent gains:

```python
def record_run_outcome(self, run: ExecutionRun) -> None:
    """
    Update Tasks, PlanNodes, and ExecutionRun with learning
    signals based on how this run went.
    """
```

Implementation outline:

- Compute run stats:
  - Number of steps.
  - Number of failed steps.
  - Whether rollback happened.
  - Time between first and last step.
- Derive `difficulty_score` using heuristics + an optional cheap LLM call.
- Update the linked Task:
  - Set/adjust `difficulty_score`.
  - Increment `rework_count` if task was reopened or follow‑up tasks were created.
  - Set `actual_started_at` / `actual_completed_at` once.
- Update PlanNode:
  - Raise `learned_risk_level` if runs frequently fail or block.
  - Raise `learned_priority` for high‑impact nodes or those feeding many dependent tasks.
- Write `learning_notes`:
  - Short, human‑readable explanation of what was learned from the run.

### 4.2 Periodic retrospectives

ManagerAgent also exposes:

```python
def periodic_retrospective(self) -> dict:
    """
    Look at recent runs & tasks, identify patterns, and propose:
      - priority/risk updates
      - dependency tweaks
      - new spike/prototype tasks
    Returns a dict summary for logging/UI.
    """
```

Triggering:

- Automatically after every N runs or once per day.
- Manually via `POST /projects/{project_id}/refine_plan`.

Behavior:

- Gather:
  - Recent `ExecutionRun`s.
  - Tasks with high `rework_count`.
  - PlanNodes with many failures.
  - Blueprint version changes.
- Call a deep model with a “retrospective” prompt.
- Parse output into:
  - PlanNode priority/risk adjustments.
  - New or split tasks.
  - Suggested dependency tweaks.
  - Suggested blueprint clarifications.
- Apply only **safe, local changes** automatically; require human approval for big plan shifts.

---

## 5. Plan Refinement & Pivots

### 5.1 `/projects/{project_id}/refine_plan`

New endpoint:

- `POST /projects/{project_id}/refine_plan`
  - Body: `{ "mode": "normal" | "aggressive" }`.
  - Calls `ManagerAgent.refine_plan(mode=...)`.

`refine_plan`:

- Invokes `periodic_retrospective()`.
- In `normal` mode:
  - Only updates learned priority/risk and local ordering.
- In `aggressive` mode:
  - Permits larger cross‑phase reordering, but still never deletes nodes, only marks them as obsolete/needs_review.
- Records a Decision and updates the ProjectSnapshot to explain changes.

### 5.2 Blueprint version pivots

Helper module: `backend/app/services/blueprint_diff.py`:

- Function `diff_blueprints(old_id: int, new_id: int) -> BlueprintDiff`:
  - Classifies PlanNodes as unchanged / modified / added / removed.

Manager pivot flow:

- When a new blueprint version becomes active:
  - Diff against old version.
  - For modified/added nodes: generate/update tasks.
  - For removed nodes: mark tasks as `needs_review` instead of deleting.
  - Log a Decision: “Pivot to Blueprint vN+1”.
  - Optionally call `refine_plan("normal")` to rebalance under the new blueprint.

---

## 6. Learning Metrics & UI

### 6.1 API: `/projects/{project_id}/learning_metrics`

Adds a new endpoint:

- `GET /projects/{project_id}/learning_metrics`
  - Returns aggregate metrics such as:
    - `avg_task_cycle_time`
    - `avg_difficulty_score`
    - `top_fragile_areas` (PlanNodes or paths with high rework/failures)
    - `plan_deviation_rate`
    - `blocked_tasks_count`

This is intended for:

- QA probes (smoke tests that seed synthetic runs and assert metrics move).
- A small **Learning & Plan Health** card in the UI.

### 6.2 Snapshot integration

ProjectSnapshot generation is extended to include:

- Section “Learning & Plan Health” with:
  - Average difficulty.
  - Fragile components.
  - Plan deviation rate.
  - Summary of the last retrospective/refine_plan.

Docs tab pins this snapshot so humans (and agents) can quickly see how the project is evolving.

### 6.3 Frontend surfaces

Initial UI targets:

- **Learning card** (likely in Usage or Notes tab):
  - Pulls `/projects/{id}/learning_metrics`.
  - Shows badges for fragile areas (click to filter Tasks by those PlanNodes).
- **“Improve plan based on learning”** button:
  - Calls `/projects/{id}/refine_plan` with `mode="normal"`.
  - Shows a modal summarizing proposed changes.

---

## 7. Model Choices for Learning

The learning layer reuses the **Model Matrix** role aliases (see `docs/MODEL_MATRIX.md`):

- **Run‑level notes & difficulty estimation**
  - Use `OPENAI_MODEL_SUMMARY` or `OPENAI_MODEL_WORKER_TEST` (fast/cheap).
- **Blueprint understanding & retrospectives**
  - Use `OPENAI_MODEL_MANAGER` or `OPENAI_MODEL_RESEARCH_DEEP` (deep models).
- **Metrics & scoring**
  - Mostly deterministic Python code; only call models for natural‑language summarization (learning_notes, retrospective narratives).

This separation keeps expensive models focused where they add value (plan changes) while using cheaper models for incremental scoring and summaries.

---

## 8. QA & Implementation Notes

When implementing this layer:

1. **Start with data models and metrics endpoints** in QA only.
2. **Add smoke tests** in `qa/`:
   - Seed projects/runs/tasks.
   - Call `record_run_outcome` and `refine_plan`.
   - Assert that learning fields and metrics change as expected.
3. **Wire UI surfaces** once metrics are stable.
4. **Keep docs in sync**:
   - Update `SYSTEM_MATRIX.md`, `API_REFERENCE.md`, `TEST_PLAN.md`, and `PROGRESS.md` as each piece lands.

Until then, treat this file (and the underlying `Updated_Project_Plan_2_AUTOPILOT_LEARNING.txt`) as the **design contract** for how InfinityWindow should adapt its plans over time.


