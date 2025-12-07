# InfinityWindow Autopilot – Implementation Checklist

Status: Design only – not implemented yet. Current shipped automation is limited to task upkeep/hooks after `/chat`; Autopilot Phases 1–4 (Blueprint/Plan, Manager/Workers, Runs) are not live. Keep this checklist aligned with `docs/PROGRESS.md`, `docs/TODO_CHECKLIST.md`, and the planned API surface in `docs/API_REFERENCE_UPDATED.md` section 11.

Phase 1: [ ]   Phase 2: [ ]   Phase 3: [ ]   Phase 4: [ ]   Phase T: [ ]  (Keep these checkboxes in sync with `docs/PROGRESS.md`.)

This file is the **operational checklist** for turning the Autopilot design into a working feature set.  
It breaks down each Autopilot phase into concrete implementation steps so that, when a phase is scheduled, you can walk this list top‑to‑bottom.  
`docs/PROGRESS.md` and `docs/TODO_CHECKLIST.md` should point here rather than duplicating every sub‑item.

---

## Phase 1 – Blueprint & Plan graph [design‑only]

### Data models & migrations

- [ ] Add new models to `backend/app/db/models.py` (with corresponding tables):
  - [ ] `Blueprint` – links a project to a large spec `Document`, with versioning and status.
  - [ ] `PlanNode` – hierarchical plan nodes (phase/epic/feature/story/task_spec) with anchors/offsets, status, priority, risk.
  - [ ] `PlanNodeTaskLink` – many‑to‑many link between PlanNodes and `Task`s.
  - [ ] `TaskDependency` – explicit task‑to‑task dependencies.
  - [ ] `BlueprintIngestionJob` – tracks blueprint ingestion status/progress/errors.
- [ ] For early development, document that we rely on “delete DB / recreate” for schema changes.  
  Longer term, plan an Alembic migration path so Blueprint/Plan tables can be added safely in place.

### Backend services & endpoints

- [ ] Create `backend/app/services/blueprints.py` with helpers for:
  - [ ] Loading blueprint documents and chunking them.
  - [ ] Calling the LLM to extract per‑chunk outlines and merging them into a global PlanNode tree.
  - [ ] Generating tasks from a given PlanNode (`generate_tasks_for_plan_node`).  
- [ ] Add Blueprint/Plan endpoints to `app/api/main.py` as per `AUTOPILOT_PLAN.md` and `API_REFERENCE.md`:
  - [ ] `POST /projects/{project_id}/blueprints`
  - [ ] `GET /projects/{project_id}/blueprints`
  - [ ] `GET /blueprints/{blueprint_id}`
  - [ ] `PATCH /blueprints/{blueprint_id}`
  - [ ] `POST /blueprints/{blueprint_id}/generate_plan`
  - [ ] `PATCH /plan_nodes/{id}`
  - [ ] `POST /plan_nodes/{plan_node_id}/generate_tasks`
  - [ ] `POST /blueprints/{blueprint_id}/generate_all_tasks` (optional)

### Frontend surfaces

- [ ] In the Tasks tab, add:
  - [ ] Blueprint selector (list of blueprints for the project, with active indicator).
  - [ ] Plan tree view (phases → epics → features → stories), collapsible.
  - [ ] “Generate tasks for this node” action.
  - [ ] Filter to show only tasks linked to the selected PlanNode.

### Config & model routing

- [ ] Wire Blueprint ingestion code to use `MODEL_MATRIX` roles:
  - [ ] `call_model_for_role("blueprint", ...)` for per‑chunk outline extraction and global merge.
  - [ ] `call_model_for_role("plan_tasks", ...)` for PlanNode → Task decomposition.
- [ ] Ensure `OPENAI_MODEL_BLUEPRINT` and `OPENAI_MODEL_PLAN_TASKS` env vars fall back to the design defaults in `MODEL_MATRIX.md`.

### Docs to update when Phase 1 ships

- [ ] `SYSTEM_OVERVIEW.md` – describe Blueprint/Plan graph as a current feature.
- [ ] `SYSTEM_MATRIX.md` – move Blueprint/Plan models/endpoints from “planned” into the main tables.
- [ ] `API_REFERENCE.md` – promote Blueprint endpoints out of the “planned” section.
- [ ] `CONFIG_ENV.md` – mark any Blueprint‑related env vars as live.
- [ ] `PROGRESS.md` / `TODO_CHECKLIST.md` – mark Phase‑1 items as completed/in‑progress.
- [ ] `AUTOPILOT_PLAN.md` / `AUTOPILOT_IMPLEMENTATION_CHECKLIST.md` – update status for Phase 1.

### QA & smoke tests

- [ ] Add a `qa/blueprints_probe.py` that:
  - [ ] Seeds a small synthetic blueprint document.
  - [ ] Creates a Blueprint + runs `generate_plan`.
  - [ ] Asserts PlanNodes and linked Tasks exist and are structurally sane.
- [ ] `TEST_PLAN.md` – mark `J-Blueprint-01` as active and adjust phases if needed.

---

## Phase 2 – Project Brain & context engine [design‑only]

### Data models & migrations

- [ ] Add to `backend/app/db/models.py`:
  - [ ] `ConversationSummary` – per‑conversation short/detailed summaries, last_message_id, updated_at.
  - [ ] `ProjectSnapshot` – project‑level snapshot text, active_phase_node_id, key_metrics_json, updated_at.
- [ ] Add any needed FKs from `Project` to Snapshot and from `Conversation` to Summary.
- [ ] Continue with reset‑DB pattern in dev/QA; plan eventual Alembic migrations to add these tables in production.

### Backend services & endpoints

- [ ] Implement `backend/app/services/conversation_summaries.py`:
  - [ ] `update_conversation_summary(conversation_id: int)` with LLM calls via `call_model_for_role("summary", ...)`.
- [ ] Implement `backend/app/services/snapshot.py`:
  - [ ] `refresh_project_snapshot(project_id: int)` using `call_model_for_role("snapshot", ...)`.
- [ ] Implement `backend/app/llm/context_builder.py`:
  - [ ] Build a structured `ContextBundle` from instructions, snapshot, PlanNodes, tasks, decisions, memory, recent messages.
  - [ ] Provide a `build_context_for_chat(...)` helper used by chat and future workers.
- [ ] Implement `backend/app/services/alignment.py`:
  - [ ] `check_alignment(project_id, action_type, action_payload) -> AlignmentResult` using `call_model_for_role("alignment", ...)`.
- [ ] Add/confirm endpoints:
  - [ ] `POST /projects/{project_id}/snapshot/refresh`
  - [ ] `GET /projects/{project_id}/snapshot`
  - [ ] Any internal alignment endpoints (or inline calls from runs/worker code) as per `AUTOPILOT_PLAN.md`.

### Frontend surfaces

- [ ] Add a small **Snapshot card** (e.g., in Notes or Usage tab) that shows:
  - [ ] Goals, active blueprint/phase, key metrics, recent progress and risks.
  - [ ] A “Refresh snapshot” button calling `/snapshot/refresh`.

### Config & model routing

- [ ] Use `MODEL_MATRIX` role aliases:
  - [ ] `summary` → `OPENAI_MODEL_SUMMARY`.
  - [ ] `snapshot` → `OPENAI_MODEL_SNAPSHOT`.
  - [ ] `alignment` → `OPENAI_MODEL_ALIGNMENT`.
- [ ] Confirm `CONFIG_ENV.md` documents these env vars and that defaults are consistent with `MODEL_MATRIX.md`.

### Docs to update when Phase 2 ships

- [ ] `SYSTEM_OVERVIEW.md` – describe ConversationSummary/ProjectSnapshot and context builder as live features.
- [ ] `SYSTEM_MATRIX.md` – move ConversationSummary/ProjectSnapshot from “planned” into the core data model section.
- [ ] `API_REFERENCE.md` – mark snapshot endpoints as implemented.
- [ ] `AUTOPILOT_LEARNING.md` – update where it references snapshot integration.

### QA & smoke tests

- [ ] Extend `qa/run_smoke.py` to include:
  - [ ] A snapshot probe that creates a project, calls `/snapshot/refresh`, and asserts snapshot text + metrics are present.
- [ ] Add manual cases to `TEST_PLAN.md` (e.g., “Snapshot view updates after tasks/decisions change”).  
- [ ] When stable, record a dated test report verifying snapshot & context builder behavior.

---

## Phase 3 – Execution runs & workers [design‑only]

### Data models & migrations

- [ ] Add to `backend/app/db/models.py`:
  - [ ] `ExecutionRun` – project_id, conversation_id, task_id, run_type, status, error_message, meta, touched_files_json, timestamps.
  - [ ] `ExecutionStep` – run_id, order_index, actor, tool, input_payload, output_payload, rollback_data, status, error_message, timestamps.
  - [ ] Optional: `execution_run_id` on `UsageRecord` for usage‑per‑run tracking.
- [ ] Add appropriate indexes (e.g., runs by project/status, steps by run/order_index).

### Backend services & endpoints

- [ ] Implement `backend/app/services/runs.py`:
  - [ ] Helpers: `create_run`, `append_step`, `get_next_pending_step`, `mark_step_status`, `mark_run_status`, `rollback_run`.
- [ ] Implement `backend/app/services/workers.py`:
  - [ ] Prompts and wrappers for code/test/doc workers using Files/Terminal/Search tools.
  - [ ] Integration with `openai_client.run_agent_with_tools` (when added).
- [ ] Add run endpoints to `app/api/main.py` as per `API_REFERENCE.md`:
  - [ ] `POST /projects/{project_id}/runs`
  - [ ] `GET /projects/{project_id}/runs`
  - [ ] `GET /runs/{run_id}`
  - [ ] `POST /runs/{run_id}/advance`
  - [ ] `POST /runs/{run_id}/rollback`

### Frontend surfaces

- [ ] Add a **Runs** tab or panel that:
  - [ ] Lists runs for the current project (id, type, status, linked task, created_at).
  - [ ] Shows ordered steps for a selected run, with statuses and short descriptions.
  - [ ] Offers Approve/Skip/Abort/Revert actions wired to `/runs/{id}/advance` and `/runs/{id}/rollback`.
  - [ ] Renders file diffs and alignment information for `write_file` steps.

### Config & model routing

- [ ] Implement `run_agent_with_tools` in `openai_client.py` and wire it to:
  - [ ] `call_model_for_role("worker_code", ...)`.
  - [ ] `call_model_for_role("worker_test", ...)`.
  - [ ] `call_model_for_role("worker_doc", ...)`.
- [ ] Confirm `OPENAI_MODEL_WORKER_CODE`, `OPENAI_MODEL_WORKER_TEST`, `OPENAI_MODEL_WORKER_DOC` are documented in `CONFIG_ENV.md` and `MODEL_MATRIX.md`.

### Docs to update when Phase 3 ships

- [ ] `SYSTEM_OVERVIEW.md` – add ExecutionRuns/Steps as core automation primitives.
- [ ] `SYSTEM_MATRIX.md` – move ExecutionRun/ExecutionStep from “planned” to core data model + feature tables.
- [ ] `API_REFERENCE.md` – mark runs endpoints as current.
- [ ] `AUTOPILOT_EXAMPLES.md` – confirm examples align with actual UI flows.

### QA & smoke tests

- [ ] Add `qa/runs_probe.py`:
  - [ ] Create a minimal project + task.
  - [ ] Create a run with a synthetic step (e.g., plan‑only or a safe file write).
  - [ ] Advance the run to completion and assert status/steps are correct.
- [ ] Extend `TEST_PLAN.md` with manual Runs panel checks (if not already captured under Phase H).

---

## Phase 4 – ManagerAgent & Autopilot heartbeat [design‑only]

### Data models & migrations

- [ ] Extend `Project` in `backend/app/db/models.py` with:
  - [ ] `autonomy_mode` (`"off" | "suggest" | "semi_auto" | "full_auto"`).
  - [ ] `active_phase_node_id` (FK to PlanNode).
  - [ ] `autopilot_paused` (bool).
  - [ ] `max_parallel_runs` (int).

### Backend services & endpoints

- [ ] Implement `backend/app/llm/intent_classifier.py`:
  - [ ] `classify_intent(...)` using `call_model_for_role("intent", ...)`.
- [ ] Implement `backend/app/services/manager.py` (ManagerAgent):
  - [ ] Methods for loading context (snapshot, PlanNodes, tasks, runs).
  - [ ] Task selection heuristics (dependencies, learned priority/risk once Phase 2/learning exist).
  - [ ] `handle_start_build`, `handle_continue_build`, `has_unfinished_run`, `has_run_awaiting_approval`, `advance_run`, `start_run_for_next_task`, `explain_plan`.
- [ ] Add `/projects/{id}/autopilot_tick` and `/projects/{id}/manager/plan` to `app/api/main.py`, using the flow described in `AUTOPILOT_PLAN.md`.

### Frontend surfaces

- [ ] Add **Autopilot controls** in the header:
  - [ ] Autonomy mode dropdown (Off / Suggest / Semi / Full).
  - [ ] Pause/Resume toggle.
  - [ ] Status pill (Idle / Running / Waiting for approval / Error).
- [ ] Add an “Explain current plan” UI (e.g., in Notes/Tasks tab) that calls `/projects/{id}/manager/plan` and renders:
  - [ ] Active phase.
  - [ ] Top recommended tasks.
  - [ ] Active runs and a short rationale.

### Config & model routing

- [ ] Ensure ManagerAgent uses `call_model_for_role("manager", ...)` for planning and explanations.
- [ ] Confirm `OPENAI_MODEL_MANAGER` is documented and uses a strong default model (per `MODEL_MATRIX.md`).  

### Docs to update when Phase 4 ships

- [ ] `SYSTEM_OVERVIEW.md` – add a subsection describing the ManagerAgent & Autopilot modes as shipping features.
- [ ] `SYSTEM_MATRIX.md` – include Manager/Autopilot endpoints and UI surfaces in the main feature tables.
- [ ] `USER_MANUAL.md` – expand the “Autopilot” section from preview to a real “How to use Autopilot” chapter.
- [ ] `AUTOPILOT_LIMITATIONS.md` – update any constraints that changed (e.g., background behavior, new guardrails).

### QA & smoke tests

- [ ] Implement `qa/autopilot_probe.py`:
  - [ ] Seed a small project + blueprint/plan + tasks.
  - [ ] Enable `semi_auto` mode.
  - [ ] Call `/autopilot_tick` until a run is started and steps reach `needs_approval`.
  - [ ] Assert Manager respects autonomy and does not execute dangerous commands.
- [ ] Activate and run `J-Autopilot-01` / `J-Autopilot-02` in `TEST_PLAN.md` once the behavior is stable.

---

## Phase T – Scalable ingestion & token/cost control [design‑only]

> Repo ingestion groundwork (jobs + batching) shipped on **2025‑12‑04**. The remaining items focus on blueprint-scale ingestion and Autopilot integration.

### Data models & migrations

- [ ] Add to `backend/app/db/models.py`:
  - [x] `IngestionJob` – project_id, kind (`repo`/`docs`/`blueprint`), source, status, total_items, processed_items, error_message, meta. *(Repo ingestion uses this today.)*
  - [x] `FileIngestionState` – project_id, relative_path, sha256, last_ingested_at (+ unique constraint on project_id + path). *(Repo ingestion uses this today.)*
  - [ ] `BlueprintSectionSummary` – per‑PlanNode short/detailed summaries.

### Backend services & endpoints

- [x] Implement batched embeddings helper (in `app/llm/embeddings.py`):
  - [x] `get_embedding_model()` using `OPENAI_EMBEDDING_MODEL` with a safe default.
  - [x] `embed_texts_batched(...)` enforcing `MAX_EMBED_TOKENS_PER_BATCH` and `MAX_EMBED_ITEMS_PER_BATCH`.
- [x] Refactor repo ingestion (`github_ingestor.py`) into:
  - [x] Collector layer – walk files, filter with include/exclude globs, compute hashes, build chunks.
  - [x] Embedding layer – call `embed_texts_batched` and write embeddings to Chroma while updating `IngestionJob` progress.
  - [ ] Blueprint ingestion uses the same pattern (pending).
- [x] Add ingestion job endpoints to `app/api/main.py`:
  - [x] `POST /projects/{project_id}/ingestion_jobs`
  - [x] `GET /projects/{project_id}/ingestion_jobs/{job_id}`

### Frontend surfaces

- [x] Extend the “Ingest local repo” UI to:
  - [x] Kick off an ingestion job instead of a one-shot request.
  - [x] Poll job progress and show processed/total counts.
  - [x] Surface errors (e.g., token limit issues) with actionable messages.

### Config & model routing

- [ ] Implement and document the following env vars (see `CONFIG_ENV.md` and `MODEL_MATRIX.md`):
  - [x] `OPENAI_EMBEDDING_MODEL`
  - [x] `MAX_EMBED_TOKENS_PER_BATCH`
  - [x] `MAX_EMBED_ITEMS_PER_BATCH`
  - [ ] `MAX_CONTEXT_TOKENS_PER_CALL`
  - [ ] `AUTOPILOT_MAX_TOKENS_PER_RUN`

### Docs to update when Phase T ships

- [x] `SYSTEM_OVERVIEW.md` – describe large-repo ingestion as a batched flow (blueprint portion still design-only).
- [x] `SYSTEM_MATRIX.md` – move IngestionJob/FileIngestionState into the core matrix; BlueprintSectionSummary remains planned.
- [x] `API_REFERENCE.md` – document ingestion job APIs as live endpoints.
- [x] `CONFIG_ENV.md` – mark batching env vars as active.

### QA & smoke tests

- [ ] Add a `qa/ingestion_probe.py` that:
  - [ ] Seeds a project with a moderately large repo or doc set.
  - [ ] Starts an ingestion job via API.
  - [ ] Polls job status until `completed` and asserts no single embeddings call exceeds token caps (via logs/telemetry).
- [x] Add manual test steps under `TEST_PLAN.md` (e.g., verifying progress card behavior and hash-skipping).

---

## Where this fits

Use this checklist together with:

- `AUTOPILOT_PLAN.md` – overall architecture and per‑phase goals.
- `AUTOPILOT_LEARNING.md` – Project Learning Layer design.
- `MODEL_MATRIX.md` – model/env routing for chat modes and Autopilot roles.
- `TEST_PLAN.md` – especially Phase H (Autopilot & Blueprint [design‑only]) test cases.
- `PROGRESS.md` / `TODO_CHECKLIST.md` – to track which phases/items are in progress or complete.

As Autopilot work lands, update this file first, then propagate status into the rest of the docs so there is a single, authoritative checklist for implementation progress.

