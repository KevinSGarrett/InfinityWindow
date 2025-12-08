# Alignment Log — To-Do (Not Yet Started)

Use this file for plan items that have not been started in the repo. Move items to `correct-alignments.md` once implemented and verified, or to `misalignments.md` if started but conflicting, or to `unsure-alignments.md` if ambiguous.

## Index
- Last updated by Cursor on: 2025-12-08
- Coverage status: Phase 1 checklist added; design-only autopilot/blueprint/model-matrix items expected to land here after verification.

## How to use this file
- Reference the plan source (file/section) and describe the intended implementation.
- Leave status as “Not started” until work begins; link to issues/tasks when created.

## Phase 2 — Design-only plan items (2025-12-08)
- Autopilot/Blueprint/Manager roadmap remains design-only; no backend models/endpoints or frontend surfaces exist. Treat the following checklist IDs as TODO until implementation starts:  
  - PLAN2-BLUEPRINT-MODELS / PLAN2-BLUEPRINT-API / PLAN2-BLUEPRINT-INGEST / PLAN2-PLAN-TASKS / PLAN2-PLAN-UI (Updated_Project_Plan_2 §§1.1–1.5).  
  - PLAN2-SUMMARIES / PLAN2-SNAPSHOT / PLAN2-CONTEXT / PLAN2-ALIGNMENT (Updated_Project_Plan_2 §2).  
  - PLAN2-RUNS-MODELS / PLAN2-WORKERS / PLAN2-RUNS-API / PLAN2-RUNS-UI (Updated_Project_Plan_2 §3).  
  - PLAN2-AUTONOMY-PROJECT / PLAN2-INTENT / PLAN2-MANAGER / PLAN2-AUTOPILOT-UI (Updated_Project_Plan_2 §4).  
  - PLAN2-CEO-DASHBOARD / PLAN2-DOCS-UPDATE (Updated_Project_Plan_2 §5.1–5.2).  
  - Evidence: `docs/PROGRESS.md` (“Autopilot & Blueprint & Learning [design-only roadmap]”) and `docs/SYSTEM_OVERVIEW.md` §5 note these are future phases; `rg` shows no `autopilot`/`blueprint`/`execution_run` symbols in `backend/app`.  
- QA probes for these features are not present: PLAN2-QA-PROBES (Updated_Project_Plan_2 §5.3) — add blueprints_probe and runs_autopilot_probe once implementation begins; no files under `qa/` or Playwright specs cover these flows today.
- Model-matrix & learning extensions remain unstarted: PLAN2MM-ROLE-ALIASES, PLAN2MM-WORKER-ROUTES, PLAN2AL-LEARNING-FIELDS, PLAN2AL-BLUEPRINT-UNDERSTAND, PLAN2AL-RUN-OUTCOMES. Docs call these design-only; backend lacks `call_model_for_role`, learning fields on Task/PlanNode/ExecutionRun, or `/refine_plan`/`/learning_metrics` endpoints.
- Ingestion/Context roadmap items not yet built: PLAN2T-BLUEPRINT-SUMMARIES, PLAN2T-CONTEXT-MULTISTAGE, PLAN2T-BUDGET-KNOBS. There is no `BlueprintSectionSummary` model or context-builder token budget enforcement; SYSTEM_OVERVIEW §5 and PROGRESS mark them as future work.

## Pending from Updated_Project_Plans
Re-run: 2025-12-08 — still not started; items remain to-do.

## Phase 3 — Backend alignment check (2025-12-08)
- Scan result: Autopilot/plan graph/manager/worker/model-routing remain not started; alignment checks and snapshots/context builder remain pending.
- Existing backend aligns on: ingestion batching/jobs/hash skipping, fs/terminal safety, usage/telemetry surfacing (tracked in correct-alignments).

## Phase 4 — Frontend/UI alignment check (2025-12-08)
- Plan-driven UI enhancements not started or only partially present; keep as to-do:
  - Usage/Telemetry dashboard Phase 2/3 charts & exports beyond current lists/buckets/cards.
  - Autopilot affordances (manager/worker/plan views, autonomy mode controls) not present.
  - Ingestion UX for progress/polling (repo/blueprint) beyond existing minimal flows.
  - Model routing/override UI per plan phases (phase3/4 UI elements) beyond current model override dropdown.
  - Phase3/4 UI elements from updated plans (e.g., alignment checks surfacing, blueprint/plan navigation) not implemented.

## Phase 5 — Tests & QA alignment check (2025-12-08)
- To-do coverage gaps remain for plan-critical features that are not yet implemented:
  - No tests/specs for blueprint/plan graph, manager/worker/autonomy flows, alignment checks, blueprint ingestion/plan generation, or role-based model routing.
  - Existing tests cover current system (tasks/telemetry/usage, fs, docs, terminal, ingestion jobs), but do not cover the new plan surfaces.
  - Test plans (`docs/tasks/TEST_PLAN_TASKS.md`, `docs/TEST_PLAN.md`, templates) would need expansion once implementations exist.

## Phase 6 — Telemetry/Observability alignment check (2025-12-08)
- Current telemetry/usage supports: task actions (recent_actions with confidence/model/group/blocked), confidence buckets/stats, model filters in UI, usage records per conversation, and summary cards. Export is limited to JSON copy of recent actions.
- Plan-expectation gaps (to-do):
  - Telemetry dashboard Phase 2/3: charts/exports/time filters beyond current lists/buckets/cards.
  - Model routing logs by role/alias (manager/worker/blueprint/plan_tasks) are not present because role routing is not implemented.
  - Task automation telemetry beyond current actions (e.g., alignment checks, autopilot runs/manager decisions) not present.
  - Ingestion telemetry tied to blueprint/repo batching and job progress charts not implemented (only basic ingestion_jobs endpoints).
  - Exports/diagnostics: no CSV/JSON bulk export, no dashboard history; current export is “Copy JSON” for recent actions.

## Phase 7 — Ingestion & Data Flows alignment check (2025-12-08)
- Current state:
  - Ingestion jobs endpoints exist (create/list/cancel/history/cancel) and repo/doc ingest flows run with batching and hash-based skipping (`embed_texts_batched`, `FileIngestionState`).
  - Docs/PROGRESS and SYSTEM_OVERVIEW describe live progress/bytes counters and cancel in UI.
  - Blueprint ingestion/PlanNode generation not present; no BlueprintSectionSummary or summary doc generation.
  - Ingestion telemetry is limited to job endpoints; no blueprint-specific progress, section anchors, or retrieval summaries.
- To-do: implement blueprint ingestion/summaries (PLAN2T-BLUEPRINT-SUMMARIES), multi-stage retrieval/token budgeting (PLAN2T-CONTEXT-MULTISTAGE), and budget guardrails/exports (PLAN2T-BUDGET-KNOBS) once Autopilot/blueprint work begins.

## Phase 8 — Worker/Manager & Autopilot Playbooks (2025-12-08)
- Current state:
  - No manager agent, worker agents (code/test/doc), or execution runs/steps.
  - Autonomy modes (off/suggest/semi_auto/full_auto) and allowlists/approvals not wired to UI/logic; task automation is limited to add/complete heuristics.
  - Model role aliases for manager/worker/plan tasks/alignment not implemented.
  - AUTOPILOT_EXAMPLES/LEARNING/LIMITATIONS/MODEL_MATRIX not reflected in code; prompts/heuristics not in place.
- To-do: implement manager/worker agents, autonomy modes with safety guardrails, role-based model routing, prompts/heuristics per playbooks, and surface relevant UI (autonomy controls, plan/worker views).

## Phase 9 — Compliance & Safety checks (2025-12-08)
- Current strengths:
  - `local_root_path` enforced; `_safe_join` blocks `..`/absolute paths; terminal run scoped to project root and uses `check=True`.
  - Chat model_not_found fallback present.
  - Task status/priority validation; filesystem/terminal instructions aliases handled.
- Gaps (to-do per plan):
  - Autonomy safety modes and command allowlists/approvals not wired (full autopilot not implemented).
  - Alignment checks (preflight for edits/commands) not implemented.
  - Instruction handling beyond current prompts (manager/worker/plan alignment) not present.
  - Broader compliance guardrails tied to autopilot modes not in place.

## Phase 10 — Synthesis & Fix Plan (2025-12-08)
- Summary recorded (planning, no implementation yet):
  - Quick wins: role-based model alias helper + env defaults; ingestion batching/incremental; telemetry charts/exports v2.
  - Next: autonomy guardrails scaffolding; blueprint/plan scaffolding; summary/snapshot services; alignment checks.
  - Tests/docs to expand after each slice.
- Action: choose prioritized slices from above and move them into active work; misalignments remain empty until started work conflicts.

### Blueprint & Plan Graph (Updated_Project_Plan_2.txt)
- Models: Blueprint, PlanNode, PlanNodeTaskLink, TaskDependency, BlueprintIngestionJob; extend Project with active_blueprint_id.
- Endpoints: CRUD/list for blueprints/plan_nodes; generate_plan; compare_to_parent; plan heartbeat `/projects/{id}/autopilot_tick` (manager).
- Services: Plan generation from blueprint chunks, PlanNode → Task decomposition with dependencies.

### Manager/Worker/Autonomy (Updated_Project_Plan_2.txt & Worker_Manager_Playbook)
- Manager agent, worker agents (code/test/doc), execution runs/steps, autonomy modes (off/suggest/semi_auto/full_auto), terminal allowlist/auto-run guardrails tied to autonomy.

### Model Matrix & Routing (Updated_Project_Plan_2_Model_Matrix.txt)
- Role aliases/env vars: summary/snapshot/blueprint/plan_tasks/manager/worker_code/worker_test/worker_doc/alignment/intent/research_deep; `call_model_for_role` helper; default mappings; docs sync.

### Ingestion Plan (Updated_Project_Plan_2_Ingestion_Plan.txt)
- Batched embeddings helper (embed_texts_batched with token/item caps), centralized embed_batch.
- Repo ingestion refactor with batching and hash-based incremental (FileIngestionState).
- Blueprint/document section summaries (BlueprintSectionSummary) and summary docs.
- Multi-stage retrieval wiring for context builder.

### Summaries/Snapshots
- Conversation summary and project snapshot services with role aliases (summary/snapshot).

### Alignment checks
- Alignment-check service and model alias for file edit/terminal actions.

