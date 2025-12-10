# Alignment Log — Unsure/To‑Verify Alignments

Use this file for items that are not yet confidently classified as correct or misaligned. Move entries to `correct-alignments.md` or `misalignments.md` once verified.

## Index
- Last updated by Cursor on: 2025-12-08
- Coverage status: Phase 1 checklist captured; no unsure items yet; triage to follow after backend/frontend/doc comparison.

## How to use this file
- Note the plan source (file/section) and the repo area in question.
- Describe why the alignment is uncertain (missing evidence, ambiguous requirement, partial implementation).
- Add a verification action (e.g., code read, test, doc cross-check).

## Phase 0 — Prep
- Tracking structure established; no unsure items logged yet.

## Phase 1 — Plans intake (extracted requirements to verify)
Re-run: 2025-12-08 — requirements re-confirmed; no changes from prior intake.

### From Updated_Project_Plan_2.txt (archived pre-Autopilot-v2 design)
- Blueprint & Plan Graph: add Blueprint/PlanNode models, PlanNodeTaskLink, TaskDependency, BlueprintIngestionJob; extend Project with active_blueprint_id.
- Endpoints: CRUD for blueprints/plan_nodes, generate_plan, compare_to_parent, generate tasks for plan nodes; heartbeat /autopilot_tick.
- Ingestion pipeline: chunk blueprint (500k words), outline extraction/merge, PlanNode creation with offsets/anchors/order; job tracking and error handling.
- PlanNode → tasks: LLM decomposition with dependencies, acceptance criteria, effort, risk.
- Manager/worker/autonomy modes: manager agent, workers (code/test/doc), execution runs/steps; human-in-the-loop safety/allowlist for terminal/files; autonomy levels (off/suggest/semi_auto/full_auto).
- Context builder: deterministic slices (instructions, pinned notes, plan nodes, decisions).
- Safety: path confinement, terminal allowlist, approvals for writes/unsafe commands.
- Docs update requirement: SYSTEM_MATRIX, API_REFERENCE, DEV_GUIDE, USER_MANUAL, OPERATIONS_RUNBOOK, TEST_PLAN.

### From Updated_Project_Plan_2_Model_Matrix.txt (archived)
- Model role aliases and env vars: OPENAI_MODEL_SUMMARY/SNAPSHOT/BLUEPRINT/PLAN_TASKS/MANAGER/WORKER_CODE/WORKER_TEST/WORKER_DOC/ALIGNMENT/INTENT/RESEARCH_DEEP plus chat mode envs and defaults.
- Defaults recommended (e.g., auto→gpt-4.1-mini, deep→gpt-5.1, research→o3-deep-research, blueprint/plan_tasks roles, manager/worker roles).
- call_model_for_role helper in openai_client; wiring for blueprint ingestion, plan generation, manager/worker, alignment checks, summaries/snapshots.
- Docs to sync: CONFIG_ENV, USER_MANUAL (chat modes), SYSTEM_OVERVIEW (routing summary).

### From Updated_Project_Plan_2_Ingestion_Plan.txt (archived)
- Scalable ingestion: embed_texts_batched with MAX_EMBED_TOKENS_PER_BATCH / MAX_EMBED_ITEMS_PER_BATCH; embed_batch helper in openai_client.
- IngestionJob model: kind/status/progress/error; endpoints POST/GET /projects/{id}/ingestion_jobs.
- Repo ingestion refactor: collect_repo_chunks + batch ingest; progress polling UI; hash-based incremental (FileIngestionState).
- Blueprint/document summaries: BlueprintSectionSummary per PlanNode; summary docs for large blueprints.
- Retrieval context: multi-stage retrieval to keep contexts small.

These items were reviewed in Phase 2; initial misalignments have been logged. Keep this list for any follow-up uncertain cases.

