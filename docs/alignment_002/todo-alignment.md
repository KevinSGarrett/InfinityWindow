[P1.API.ENDPOINT.001] POST /projects/{id}/blueprints — To-do
Plan: Updated_Project_Plan_2.txt::1.2 Blueprint & plan endpoints
Expected contract:
- Create blueprint from document with optional base_blueprint_id and mark_active flag; versioning semantics.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 1

[P1.API.ENDPOINT.002] GET /projects/{id}/blueprints — To-do
Plan: Updated_Project_Plan_2.txt::1.2 Blueprint & plan endpoints
Expected contract:
- List blueprints for project including is_primary flag.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 1

[P1.API.ENDPOINT.003] GET /blueprints/{id} — To-do
Plan: Updated_Project_Plan_2.txt::1.2 Blueprint & plan endpoints
Expected contract:
- Return blueprint metadata, plan tree, and ingestion job.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 1

[P1.API.ENDPOINT.004] PATCH /blueprints/{id} — To-do
Plan: Updated_Project_Plan_2.txt::1.2 Blueprint & plan endpoints
Expected contract:
- Update blueprint title/description/status and optionally mark_active.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 1

[P1.API.ENDPOINT.005] PATCH /plan_nodes/{id} — To-do
Plan: Updated_Project_Plan_2.txt::1.2 Blueprint & plan endpoints
Expected contract:
- Update PlanNode fields such as title, summary, kind, status, priority, order_index, estimate_points, risk_level, extra_metadata.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 1

[P1.API.ENDPOINT.006] POST /blueprints/{id}/generate_plan — To-do
Plan: Updated_Project_Plan_2.txt::1.2 Blueprint & plan endpoints
Expected contract:
- Generate or regenerate PlanNode tree from blueprint document, optionally track BlueprintIngestionJob.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 1

[P1.API.ENDPOINT.007] POST /plan_nodes/{id}/generate_tasks — To-do
Plan: Updated_Project_Plan_2.txt::1.4 PlanNode → Tasks
Expected contract:
- Generate tasks for a PlanNode using LLM and link via PlanNodeTaskLink.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 1

[P1.API.ENDPOINT.008] POST /blueprints/{id}/generate_all_tasks — To-do
Plan: Updated_Project_Plan_2.txt::1.4 PlanNode → Tasks
Expected contract:
- Generate tasks for all feature/story nodes in a blueprint (heavy option).
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 1

[P1.API.ENDPOINT.009] POST /blueprints/{id}/compare_to_parent — To-do
Plan: Updated_Project_Plan_2.txt::1.2 Blueprint & plan endpoints
Expected contract:
- Compare blueprint to its parent and mark changed nodes in metadata.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 1

[P1.DATA.MODEL.001] Blueprint model — To-do
Plan: Updated_Project_Plan_2.txt::1.1 Data models
Expected contract:
- SQLAlchemy Blueprint with project/document FKs, status/version, primary/parent/replaced relationships, plan_nodes relationship, timestamps.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 1

[P1.DATA.MODEL.002] PlanNode model — To-do
Plan: Updated_Project_Plan_2.txt::1.1 Data models
Expected contract:
- PlanNode with blueprint FK, parent, kind/title/summary, doc anchors and offsets, order_index, status/priority/estimate/risk, extra_metadata, linked_task_id and indexes.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 1

[P1.DATA.MODEL.003] PlanNodeTaskLink model — To-do
Plan: Updated_Project_Plan_2.txt::1.1 Data models
Expected contract:
- Join table linking PlanNodes to Tasks with weight to support 1-N relationships.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 1

[P1.DATA.MODEL.004] TaskDependency model — To-do
Plan: Updated_Project_Plan_2.txt::1.1 Data models
Expected contract:
- TaskDependency with task_id and depends_on_task_id plus index for dependency graph.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 1

[P1.DATA.MODEL.005] BlueprintIngestionJob model — To-do
Plan: Updated_Project_Plan_2.txt::1.1 Data models
Expected contract:
- Tracks ingestion progress for blueprint plan generation with status, counts, error_message, timestamps.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 1

[P1.DATA.MODEL.006] Project.active_blueprint_id — To-do
Plan: Updated_Project_Plan_2.txt::1.1 Data models
Expected contract:
- Project gains active_blueprint_id FK to selected blueprint.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 1

[P1.SERVICE.BLUEPRINT.001] Blueprint ingestion pipeline — To-do
Plan: Updated_Project_Plan_2.txt::1.3 Ingestion pipeline
Expected contract:
- services/blueprints.py chunk→outline→merge flow to create PlanNodes with offsets, anchors, order_index, error handling.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 1

[P1.SERVICE.BLUEPRINT.002] PlanNode task generation helper — To-do
Plan: Updated_Project_Plan_2.txt::1.4 PlanNode → Tasks
Expected contract:
- generate_tasks_for_plan_node creates tasks with metadata, links, dependencies from LLM output.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 1

[P1.UI.PLAN.001] Plan tree UI — To-do
Plan: Updated_Project_Plan_2.txt::1.5 Frontend – Blueprint & Plan view
Expected contract:
- Tasks tab shows blueprint selector and nested Plan tree with status/priority chips and doc snippets.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 1

[P1.UI.PLAN.002] Generate tasks button — To-do
Plan: Updated_Project_Plan_2.txt::1.5 Frontend – Blueprint & Plan view
Expected contract:
- UI actions to trigger POST /plan_nodes/{id}/generate_tasks and set active phase on phase nodes.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 1

[P2.DATA.MODEL.001] ConversationSummary model — To-do
Plan: Updated_Project_Plan_2.txt::2.1 Conversation summaries
Expected contract:
- conversation_summaries table with conversation_id unique FK, short_summary, detail_summary, last_message_id, updated_at.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 2

[P2.DATA.MODEL.002] ProjectSnapshot model — To-do
Plan: Updated_Project_Plan_2.txt::2.2 ProjectSnapshot
Expected contract:
- project_snapshots table with project_id unique FK, summary_text, active_phase_node_id, key_metrics_json, updated_at.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 2

[P2.SERVICE.ALIGN.001] check_alignment helper — To-do
Plan: Updated_Project_Plan_2.txt::2.4 Alignment helper
Expected contract:
- services/alignment.py to score file edits/terminal commands with snapshot/plan/decisions context and return alignment JSON.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 2

[P2.SERVICE.CONTEXT.001] ContextBuilder with ContextBundle — To-do
Plan: Updated_Project_Plan_2.txt::2.3 ContextBuilder
Expected contract:
- context_builder.py with dataclasses (PlanNodeContext, TaskContext, etc.) selecting plan/tasks/decisions/memory for chat.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 2

[P2.SERVICE.CONVO.001] Conversation summary helper — To-do
Plan: Updated_Project_Plan_2.txt::2.1 Conversation summaries
Expected contract:
- update_conversation_summary that rolls summaries after N messages using fast/deep model.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 2

[P2.SERVICE.SNAPSHOT.001] Project snapshot helper and endpoint — To-do
Plan: Updated_Project_Plan_2.txt::2.2 ProjectSnapshot
Expected contract:
- refresh_project_snapshot builds summary doc + ProjectSnapshot and exposes POST /projects/{id}/snapshot/refresh.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 2

[P2.UI.SNAPSHOT.001] Snapshot UI surfaces — To-do
Plan: Updated_Project_Plan_2.txt::2.2 ProjectSnapshot Frontend
Expected contract:
- Docs tab pins snapshot doc; Notes tab shows snapshot card with status/metrics.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 2

[P3.API.ENDPOINT.001] POST /projects/{id}/runs — To-do
Plan: Updated_Project_Plan_2_Phase3_4.txt::3.4 Endpoints
Expected contract:
- Create ExecutionRun with validation of project/task and status planned.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 3

[P3.API.ENDPOINT.002] GET /projects/{id}/runs — To-do
Plan: Updated_Project_Plan_2_Phase3_4.txt::3.4 Endpoints
Expected contract:
- List runs for project with optional status filter (open/all).
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 3

[P3.API.ENDPOINT.003] GET /runs/{id} — To-do
Plan: Updated_Project_Plan_2_Phase3_4.txt::3.4 Endpoints
Expected contract:
- Fetch run with ordered steps.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 3

[P3.API.ENDPOINT.004] POST /runs/{id}/advance — To-do
Plan: Updated_Project_Plan_2_Phase3_4.txt::3.4 Endpoints
Expected contract:
- Advance run with approval=approve|skip|abort and execute next step via worker wrappers.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 3

[P3.API.ENDPOINT.005] POST /runs/{id}/rollback — To-do
Plan: Updated_Project_Plan_2_Phase3_4.txt::3.4 Endpoints
Expected contract:
- Rollback touched files using rollback_data and mark run aborted.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 3

[P3.DATA.MODEL.001] ExecutionRun model — To-do
Plan: Updated_Project_Plan_2_Phase3_4.txt::3.1 Backend models for runs
Expected contract:
- execution_runs with project/task/conversation FKs, run_type, status, started_by, meta, touched_files_json, timestamps, indexes.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 3

[P3.DATA.MODEL.002] ExecutionStep model — To-do
Plan: Updated_Project_Plan_2_Phase3_4.txt::3.1 Backend models for runs
Expected contract:
- execution_steps with run FK, order_index, actor, tool, input/output payloads, status, rollback_data, timestamps, index.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 3

[P3.SAFETY.DIFF.001] Diff and rollback capture — To-do
Plan: Updated_Project_Plan_2_Phase3_4.txt::3.5 Diffs & rollback details
Expected contract:
- Before write_file capture original content/diff into ExecutionStep.output_payload and touched_files_json with rollback_data.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 3

[P3.SAFETY.TERM.001] Command allowlist and forbidden substrings — To-do
Plan: Updated_Project_Plan_2_Phase3_4.txt::3.6 Command safety allowlist
Expected contract:
- SAFE_COMMAND_PREFIXES and FORBIDDEN_SUBSTRINGS enforced for run_terminal steps, gating approvals in semi/full auto.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 3

[P3.SERVICE.RUNS.001] runs orchestration helpers — To-do
Plan: Updated_Project_Plan_2_Phase3_4.txt::3.2 Backend run orchestration
Expected contract:
- services/runs.py with create_run, append_step, get_next_pending_step, mark_step_status, mark_run_status, rollback_run.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 3

[P3.SERVICE.WORKER.001] Worker role wrappers — To-do
Plan: Updated_Project_Plan_2_Phase3_4.txt::3.3 Worker roles module
Expected contract:
- services/workers.py with run_code_worker/test_worker/doc_worker using role-specific prompts and allowed tools.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 3

[P3.UI.RUNS.001] Runs panel UI — To-do
Plan: Updated_Project_Plan_2_Phase3_4.txt::3.6 Frontend: Runs panel & step UI
Expected contract:
- Runs tab/panel listing runs and steps with status, alignment badge, approvals (approve/skip/abort) and diff viewer.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 3

[P4.API.ENDPOINT.001] POST /projects/{id}/autopilot_tick — To-do
Plan: Updated_Project_Plan_2.txt::4.4 Autopilot tick endpoint
Expected contract:
- Autopilot heartbeat endpoint that is idempotent and safe; uses ManagerAgent to start/advance runs or return waiting status.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 4

[P4.API.ENDPOINT.002] GET /projects/{id}/manager/plan — To-do
Plan: Updated_Project_Plan_2.txt::4.3 Manager explain_plan
Expected contract:
- Explain current plan/next tasks/runs for UI consumption.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 4

[P4.DATA.MODEL.001] Project autonomy fields — To-do
Plan: Updated_Project_Plan_2.txt::3.1 Models (Phase 3/4 carry-over) and 4.1 Project autonomy settings
Expected contract:
- Project fields: autonomy_mode, active_phase_node_id, autopilot_paused, max_parallel_runs.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 4

[P4.LEARN.API.001] POST /projects/{id}/refine_plan — To-do
Plan: Updated_Project_Plan_2_AUTOPILOT_LEARNING.txt::4.1 API: refine_plan
Expected contract:
- Endpoint invoking ManagerAgent.refine_plan to adjust ordering/priorities using learning signals.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 4

[P4.LEARN.API.002] GET /projects/{id}/learning_metrics — To-do
Plan: Updated_Project_Plan_2_AUTOPILOT_LEARNING.txt::5.1 Backend metrics endpoint
Expected contract:
- Endpoint returning learning metrics (cycle time, difficulty, fragile areas, plan deviation, blocked tasks).
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 4

[P4.LEARN.MODEL.001] Task learning fields — To-do
Plan: Updated_Project_Plan_2_AUTOPILOT_LEARNING.txt::1.1 Task learning fields
Expected contract:
- Task fields: difficulty_score, rework_count, planned_phase_node_id, actual_phase_node_id, actual_started_at/completed_at.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 4

[P4.LEARN.MODEL.002] PlanNode learning fields — To-do
Plan: Updated_Project_Plan_2_AUTOPILOT_LEARNING.txt::1.2 PlanNode learning fields
Expected contract:
- PlanNode learned_priority, learned_risk_level, inferred_dependency_json.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 4

[P4.LEARN.MODEL.003] ExecutionRun learning fields — To-do
Plan: Updated_Project_Plan_2_AUTOPILOT_LEARNING.txt::1.3 ExecutionRun learning fields
Expected contract:
- ExecutionRun outcome and learning_notes fields populated after runs.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 4

[P4.LEARN.SERVICE.001] Blueprint understanding pipeline — To-do
Plan: Updated_Project_Plan_2_AUTOPILOT_LEARNING.txt::2.1 Blueprint Understanding Pipeline
Expected contract:
- services/blueprint_understanding.py producing architecture/foundations/sequence docs and annotating PlanNodes with learned fields.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 4

[P4.LEARN.SERVICE.002] Run outcome recording & retrospectives — To-do
Plan: Updated_Project_Plan_2_AUTOPILOT_LEARNING.txt::3 Run-Time Learning & 3.2 Periodic retrospectives
Expected contract:
- ManagerAgent.record_run_outcome and periodic_retrospective/refine_plan methods updating learned fields and tasks.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 4

[P4.LEARN.UI.001] Learning metrics UI — To-do
Plan: Updated_Project_Plan_2_AUTOPILOT_LEARNING.txt::5.3 Frontend surfaces
Expected contract:
- UI card showing learning_metrics and button to call refine_plan.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 4

[P4.SERVICE.INTENT.001] Intent classifier — To-do
Plan: Updated_Project_Plan_2.txt::4.2 Intent classifier
Expected contract:
- intent_classifier.py classify_intent using model alias intent; integrated in chat endpoint before Manager handling.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 4

[P4.SERVICE.MANAGER.001] ManagerAgent orchestration — To-do
Plan: Updated_Project_Plan_2.txt::4.3 ManagerAgent
Expected contract:
- ManagerAgent class handling start/continue runs, choose tasks, advance runs, explain_plan with heuristics and safety/autonomy rules.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 4

[P4.UI.AUTOPILOT.001] Autopilot controls & heartbeat UI — To-do
Plan: Updated_Project_Plan_2.txt::4.5 Frontend heartbeat & controls
Expected contract:
- UI dropdown for autonomy mode, pause/resume, status pill, heartbeat polling every 30–60s calling /autopilot_tick, with toasts/badges.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase 4

[PD.DOCS.001] Docs updates for new features — To-do
Plan: Updated_Project_Plan_2.txt::5.2 Docs to update
Expected contract:
- SYSTEM_OVERVIEW, SYSTEM_MATRIX, API_REFERENCE, USER_MANUAL, DEV_GUIDE, AGENT_GUIDE, OPERATIONS_RUNBOOK, TEST_PLAN updated for blueprint/runs/autopilot.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Docs/QA

[PD.QA.001] QA probes for blueprints and runs/autopilot — To-do
Plan: Updated_Project_Plan_2.txt::5.3 QA & smoke tests
Expected contract:
- qa/blueprints_probe.py, qa/runs_autopilot_probe.py and smoke coverage added; TEST_PLAN scenarios H-Blueprint-01, H-Autopilot-01/02.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Docs/QA

[PM.MATRIX.EMBED.001] Embedding model default — To-do
Plan: Updated_Project_Plan_2_Model_Matrix.txt::5.1 Embedding model
Expected contract:
- get_embedding_model uses OPENAI_EMBEDDING_MODEL default text-embedding-3-small across ingestion/search/memory/blueprints.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Model Matrix

[PM.MATRIX.ROLE.001] Role alias env vars — To-do
Plan: Updated_Project_Plan_2_Model_Matrix.txt::1.1 Core env vars & 1.2 defaults
Expected contract:
- Env vars OPENAI_MODEL_SUMMARY/SNAPSHOT/BLUEPRINT/PLAN_TASKS/MANAGER/WORKER_CODE/WORKER_TEST/WORKER_DOC/ALIGNMENT/INTENT/RESEARCH_DEEP defined.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Model Matrix

[PM.MATRIX.ROLE.002] get_model_for_role helper — To-do
Plan: Updated_Project_Plan_2_Model_Matrix.txt::4.1 Role → env → model resolution
Expected contract:
- openai_client implements _ROLE_ENV_VARS/_ROLE_DEFAULT_MODELS and get_model_for_role(role).
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Model Matrix

[PM.MATRIX.ROLE.003] call_model_for_role usage — To-do
Plan: Updated_Project_Plan_2_Model_Matrix.txt::4.2 Calling helper & 3.x subsystem wiring
Expected contract:
- Subsystems call call_model_for_role for manager/workers/blueprint/plan_tasks/summary/snapshot/alignment/intent.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Model Matrix

[PS.SAFETY.APPROVAL.001] Approval gates by autonomy mode — To-do
Plan: Updated_Project_Plan_2_AUTOPILOT_LIMITATIONS.txt::3.3 Approval gates
Expected contract:
- Suggest: everything needs approval; Semi: safe reads/tests auto, writes/unsafe commands need approval; Full: auto except forbidden commands; rollback available.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Safety

[PT.INGEST.BUDGET.001] Budget/env knobs for embeddings and context — To-do
Plan: Updated_Project_Plan_2_Ingestion_Plan.txt::T5.1 Budget knobs in config
Expected contract:
- CONFIG_ENV and backend honor MAX_EMBED_TOKENS_PER_BATCH, MAX_EMBED_ITEMS_PER_BATCH, MAX_CONTEXT_TOKENS_PER_CALL, AUTOPILOT_MAX_TOKENS_PER_RUN.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase T

[PT.INGEST.MODEL.003] BlueprintSectionSummary model — To-do
Plan: Updated_Project_Plan_2_Ingestion_Plan.txt::T3.1 BlueprintSection summaries
Expected contract:
- BlueprintSectionSummary per PlanNode with short_summary and detailed_summary updated during plan generation.
Observed evidence:
- N/A:- — Not found in repo; no evidence of implementation.
Rationale: Not found in repo; no evidence of implementation.
Owner: TBD; Suggested milestone: Phase T
