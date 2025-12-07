# InfinityWindow Autopilot Plan – Blueprint, Manager, Workers & Runs

Status: Design only – not implemented yet. Current shipped automation is limited to task upkeep/hooks after `/chat`; Manager/Workers/ExecutionRuns/Blueprint flow are not live. For the live API surface see `docs/API_REFERENCE_UPDATED.md` (sections 1–9) and planned endpoints in section 11, and keep status aligned with `docs/PROGRESS.md` and `docs/TODO_CHECKLIST.md`.

This document ties together the Autopilot design files under `Updated_Project_Plans/` and explains **what we plan to build** on top of the current InfinityWindow system.  
The running system described in `SYSTEM_OVERVIEW.md` and `SYSTEM_MATRIX.md` does **not** yet include these models/endpoints/UI surfaces.

---

## 1. Goals & Scope

Autopilot extends InfinityWindow from “chat + tasks + files + terminal” into a **project execution engine**:

- Ingest a huge blueprint/spec (up to ~500k words) into a structured **Blueprint → PlanNode** graph.
- Generate and maintain a **Task graph** (tasks + dependencies) from that plan.
- Introduce **ExecutionRun / ExecutionStep** to log multi‑step work (file edits, test runs, doc updates) with diff/rollback.
- Add a **ManagerAgent** that:
  - Chooses what to work on next.
  - Starts runs and advances steps.
  - Learns from execution and refines the plan.
- Add **worker agents** (code/test/docs) that execute steps safely via existing Files/Terminal/Search tools.
- Build an **Autonomy layer** (`off`, `suggest`, `semi_auto`, `full_auto`) driven by `/projects/{id}/autopilot_tick`.

The detailed design lives in:

- `Updated_Project_Plans/Updated_Project_Plan_2.txt`
- `Updated_Project_Plans/Updated_Project_Plan_2_Phase3_4.txt`
- `Updated_Project_Plans/Updated_Project_Plan_2_Worker_Manager_Playbook.txt`

This doc summarizes those plans at a level suitable for the docs set and cross‑links them into `SYSTEM_OVERVIEW.md`, `SYSTEM_MATRIX.md`, and `API_REFERENCE.md`. When you start implementing these phases, use `AUTOPILOT_IMPLEMENTATION_CHECKLIST.md` as the step‑by‑step guide.

---

## 2. Phases at a Glance

We treat Autopilot as four main phases (plus a supporting ingestion phase “T”):

1. **Phase 1 – Blueprint & Plan Graph**
   - New models: `Blueprint`, `PlanNode`, `PlanNodeTaskLink`, `TaskDependency`, `BlueprintIngestionJob`.
   - New endpoints:
     - `POST /projects/{id}/blueprints`
     - `GET /projects/{id}/blueprints`
     - `GET /blueprints/{blueprint_id}`
     - `PATCH /blueprints/{blueprint_id}`
     - `POST /blueprints/{blueprint_id}/generate_plan`
     - `PATCH /plan_nodes/{id}`
     - `POST /plan_nodes/{id}/generate_tasks`
     - `POST /blueprints/{blueprint_id}/generate_all_tasks` (optional, heavy)
   - New frontend surfaces:
     - **Blueprint selector** and **Plan tree view** in the Tasks tab.
     - Ability to “Generate tasks for this node” and filter tasks by PlanNode.

2. **Phase 2 – Project Brain & Context Engine**
   - New models: `ConversationSummary`, `ProjectSnapshot`.
   - New modules:
     - `backend/app/services/conversation_summaries.py`
     - `backend/app/services/snapshot.py`
     - `backend/app/llm/context_builder.py`
     - `backend/app/services/alignment.py`
   - New endpoints:
     - `POST /projects/{id}/snapshot/refresh`
     - `GET /projects/{id}/snapshot`
     - `POST /alignment/check` (internal helper or inline in runs)
   - Context builder used by chat and workers so every LLM call sees a **structured bundle** (instructions, snapshot, relevant PlanNodes/tasks/decisions/memory).

3. **Phase 3 – Execution Runs & Worker Tools**
   - New models: `ExecutionRun`, `ExecutionStep`.
   - New modules:
     - `backend/app/services/runs.py`
     - `backend/app/services/workers.py`
   - New endpoints:
     - `POST /projects/{project_id}/runs`
     - `GET /projects/{project_id}/runs`
     - `GET /runs/{run_id}`
     - `POST /runs/{run_id}/advance`
     - `POST /runs/{run_id}/rollback`
   - New frontend:
     - **Runs panel** (likely a new right‑hand tab) listing runs and their steps.
     - Step‑level diff view for file edits and alignment badges.

4. **Phase 4 – Manager Agent & Autopilot**
   - Extend `Project` with:
     - `autonomy_mode` = `"off" | "suggest" | "semi_auto" | "full_auto"`
     - `active_phase_node_id`
     - `autopilot_paused`
     - `max_parallel_runs`
   - New modules:
     - `backend/app/llm/intent_classifier.py`
     - `backend/app/services/manager.py` (ManagerAgent)
   - New endpoints:
     - `POST /projects/{project_id}/autopilot_tick`
     - `GET /projects/{project_id}/manager/plan`
     - `POST /projects/{project_id}/refine_plan`
   - New frontend:
     - Autopilot controls in the header (mode dropdown, Pause/Resume, status pill).
     - “Explain manager plan” button and plan summary view.

5. **Phase T – Scalable Ingestion & Token/Cost Control**
   - Batching & progress tracking for repo/blueprint ingestion.
   - New models:
     - `IngestionJob`, `FileIngestionState`, `BlueprintSectionSummary`.
   - New helpers:
     - `embed_texts_batched(...)` and `get_embedding_model()` in `chroma_store.py` or `app/services/embeddings.py`.
   - New endpoints:
     - `POST /projects/{id}/ingestion_jobs`
     - `GET /projects/{id}/ingestion_jobs/{job_id}`

---

## 3. How Autopilot Uses Existing Features

Autopilot is explicitly built **on top of** the current InfinityWindow behavior:

- **Projects / Conversations / Messages**: every run is scoped to a project and often linked to a conversation.
- **Tasks**: PlanNodes generate structured tasks; ManagerAgent chooses and closes them; ExecutionRuns are usually linked to tasks.
- **Docs & Memory**: blueprints and project docs drive the plan; memory + decisions feed alignment and context.
- **Files & Terminal**: workers never gain new powers— they just use existing filesystem/terminal/search endpoints under stricter rules (see `AUTOPILOT_LIMITATIONS.md`).
- **Usage & Telemetry**: ExecutionRuns link to `UsageRecord`s so the Usage tab can show cost per run, and Autopilot respects per‑run budget knobs (planned in `Updated_Project_Plan_2_Ingestion_Plan.txt`).

The design keeps the **same safety contract** (local_root_path guardrails, terminal allowlist) and formalizes it for autonomous operation.

---

## 4. Planned Data Models (Summary)

> See `SYSTEM_MATRIX.md` for how these map to tables and endpoints; this section is a conceptual sketch only.

- `Blueprint`
  - Links a project to a large specification document.
  - Holds versioning (`version`, `status`, `parent_blueprint_id`, `replaced_by_id`).
  - Project may have multiple blueprints; one is active.

- `PlanNode`
  - Represents phases/epics/features/stories/task_specs derived from the blueprint.
  - Stores hierarchy (`parent_id`), doc anchors, offsets into the blueprint text.
  - Tracks status, priority, risk.

- `PlanNodeTaskLink`
  - Many‑to‑many bridge between PlanNodes and `Task`s.

- `TaskDependency`
  - Declares that one task depends on another, so ManagerAgent can respect dependencies.

- `ConversationSummary` / `ProjectSnapshot`
  - Compact summaries used by the context builder and the “CEO dashboard”.

- `ExecutionRun`
  - One multi‑step automation (implement feature, fix bug, run tests only, docs sync, etc.).
  - Records which project/task/conversation it belongs to, status, error info, touched files.

- `ExecutionStep`
  - Atomic step within a run (read_file, write_file, run_terminal, search_docs/messages, etc.).
  - Records tool inputs/outputs, rollback data, status (`pending`, `needs_approval`, `completed`, `failed`, `skipped`).

- `IngestionJob` / `FileIngestionState` / `BlueprintSectionSummary`
  - Provide resumable, cost‑aware ingestion and hierarchical summaries for huge repos/blueprints.

---

## 5. Manager & Workers (Behavioral Contract)

The behavioral rules are described in detail in:

- `Updated_Project_Plans/Updated_Project_Plan_2_Worker_Manager_Playbook.txt`
- `docs/AUTOPILOT_LIMITATIONS.md`
- `docs/AUTOPILOT_LEARNING.md`

High‑level expectations:

- **ManagerAgent**
  - Chooses tasks based on Blueprint/PlanNode, difficulty, risk, and dependencies.
  - Starts/advances runs within `max_parallel_runs` and autonomy rules.
  - Records learning signals after each run (difficulty, rework, learning notes).
  - Periodically refines the plan (via `/projects/{id}/refine_plan` and the Project Learning Layer).

- **Code worker**
  - Uses Files/Terminal/Search to implement code changes in small, test‑driven steps.
  - Always runs relevant tests and explains diffs.

- **Test worker**
  - Designs/runs tests, summarizes failures, and avoids over‑broad test runs when targeted ones suffice.

- **Docs worker**
  - Keeps docs/blueprint in sync with behavior.
  - Logs spec changes as Decisions and/or new Blueprint versions instead of silently diverging.

All workers respect:

- Filesystem guardrails (no escapes from `local_root_path`).
- Terminal allowlist and alignment checks before risky commands.
- Autonomy gates (suggest/semi/full) so humans stay in control of major actions.

---

## 6. Learning Layer & Plan Refinement (Where It Fits)

The Project Learning Layer design is captured in `Updated_Project_Plan_2_AUTOPILOT_LEARNING.txt` and summarized in `docs/AUTOPILOT_LEARNING.md`. At a high level:

- ExecutionRuns emit structured signals: outcomes, learning notes, cycle time, difficulty, rework.
- Tasks and PlanNodes accumulate these signals as `difficulty_score`, `rework_count`, `learned_priority`, `learned_risk_level`, inferred dependencies.
- ManagerAgent periodically runs retrospectives to:
  - Reorder tasks/phases.
  - Split/merge tasks.
  - Propose blueprint pivots when requirements change.
- A `/projects/{id}/learning_metrics` endpoint exposes aggregate metrics for UI and QA:
  - Average cycle time.
  - Average difficulty.
  - Fragile areas (high rework/failure).
  - Plan deviation rate.

This is **not** yet wired into the codebase; it is a roadmap for how future versions of InfinityWindow will “learn the project” without fine‑tuning LLMs.

---

## 7. Ingestion Batching & Model Matrix (Pointers)

Two companion docs refine the supporting pieces:

- **`docs/MODEL_MATRIX.md`** – maps chat modes and Autopilot roles (`manager`, `worker_code`, `worker_test`, `worker_doc`, `summary`, `snapshot`, `intent`, `alignment`, etc.) to model IDs and env vars.
- **`Updated_Project_Plans/Updated_Project_Plan_2_Ingestion_Plan.txt`** – defines:
  - Batch‑wise embeddings via `embed_texts_batched`.
  - `IngestionJob` and `FileIngestionState` for resumable ingestion and hash‑based re‑ingest.
  - Hierarchical blueprint summaries to keep context tokens under control.

`CONFIG_ENV.md` documents the current environment variables and is being extended to include the planned Autopilot/ingestion knobs; see that file for the latest list.

---

## 8. How This Connects to the Rest of the Docs

When you are working on Autopilot features, use this stack of docs together:

- **High‑level design**: `docs/AUTOPILOT_PLAN.md` (this file).
- **Detailed architecture**: `Updated_Project_Plans/Updated_Project_Plan_2*.txt`.
- **Current system**: `docs/SYSTEM_OVERVIEW.md` (what exists today).
- **Feature matrix**: `docs/SYSTEM_MATRIX.md` (will grow a “Planned: Autopilot & Blueprint” section).
- **API contracts**: `docs/API_REFERENCE.md` (will gain planned endpoints).
- **Config**: `docs/CONFIG_ENV.md` and `docs/MODEL_MATRIX.md`.
- **Safety & behavior**: `docs/AUTOPILOT_LIMITATIONS.md`, `docs/AUTOPILOT_LEARNING.md`, `docs/AGENT_GUIDE.md`, `docs/SECURITY_PRIVACY.md`.

As Autopilot is implemented, each phase should:

1. Update this file and the detailed plan docs to reflect reality.
2. Update `SYSTEM_MATRIX.md`, `API_REFERENCE.md`, `PROGRESS.md`, `TODO_CHECKLIST.md`, and `CHANGELOG.md`.
3. Add or extend QA coverage in `docs/TEST_PLAN.md`, `docs/TEST_REPORT_TEMPLATE.md`, and `qa/` probes.


