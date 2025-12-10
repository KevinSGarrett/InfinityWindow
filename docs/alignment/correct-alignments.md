# Alignment Log — Correct Alignments

This file records every confirmed alignment between the updated project plans in `C:\InfinityWindow_Recovery\Updated_Project_Plans` and the current repository (`C:\InfinityWindow_Recovery`). Entries should be exhaustive and precise.

## Index
- Last updated by Cursor on: 2025-12-08
- Coverage status: Phase 1 checklist drafted; doc/backend/frontend validation in progress; alignment-status dashboard pending first counts.

## How to use this file
- Each entry should reference the exact plan file/section and the corresponding code/doc/test location(s).
- Note verification method (read/inspect/test) and date.
- Keep entries brief but specific; include paths and identifiers.

## Phase 0 — Prep (in progress)
- Scope set: plans to ingest (all `Updated_Project_Plan_2*.txt`), repo areas (backend, frontend, docs, tests), telemetry/ingestion/autopilot/model matrix.

## Requirements Checklist (Phase 1 intake)
ID | Plan file + section | Area | Phase (v2 / v3+ / design-only) | Status (unknown / aligned / misaligned / todo / unsure)
---|---|---|---|---
PLAN2-BLUEPRINT-MODELS | Updated_Project_Plan_2 §1.1 | backend, autopilot | design-only | todo
PLAN2-BLUEPRINT-API | Updated_Project_Plan_2 §1.2 | backend, frontend | design-only | todo
PLAN2-BLUEPRINT-INGEST | Updated_Project_Plan_2 §1.3 | backend, ingestion | design-only | todo
PLAN2-PLAN-TASKS | Updated_Project_Plan_2 §1.4 | backend, tasks | design-only | todo
PLAN2-PLAN-UI | Updated_Project_Plan_2 §1.5 | frontend, tasks | design-only | todo
PLAN2-SUMMARIES | Updated_Project_Plan_2 §2.1 | backend, context | design-only | todo
PLAN2-SNAPSHOT | Updated_Project_Plan_2 §2.2 | backend, docs, frontend | design-only | todo
PLAN2-CONTEXT | Updated_Project_Plan_2 §2.3 | backend, context | design-only | todo
PLAN2-ALIGNMENT | Updated_Project_Plan_2 §2.4 | backend, safety | design-only | todo
PLAN2-RUNS-MODELS | Updated_Project_Plan_2 §3.1 | backend, automation | design-only | todo
PLAN2-WORKERS | Updated_Project_Plan_2 §3.3 | backend, automation | design-only | todo
PLAN2-RUNS-API | Updated_Project_Plan_2 §3.4 | backend, api | design-only | todo
PLAN2-RUNS-UI | Updated_Project_Plan_2 §3.6 | frontend, automation | design-only | todo
PLAN2-AUTONOMY-PROJECT | Updated_Project_Plan_2 §4.1 | backend, autopilot | design-only | todo
PLAN2-INTENT | Updated_Project_Plan_2 §4.2 | backend, llm | design-only | todo
PLAN2-MANAGER | Updated_Project_Plan_2 §§4.3–4.4 | backend, automation | design-only | todo
PLAN2-AUTOPILOT-UI | Updated_Project_Plan_2 §4.6 | frontend, autopilot | design-only | todo
PLAN2-CEO-DASHBOARD | Updated_Project_Plan_2 §5.1 | frontend, docs | design-only | todo
PLAN2-DOCS-UPDATE | Updated_Project_Plan_2 §5.2 | docs | design-only | todo
PLAN2-QA-PROBES | Updated_Project_Plan_2 §5.3 | qa, tests | design-only | todo
PLAN2T-EMBED-BATCH | Updated_Project_Plan_2_Ingestion_Plan §§T1.1–T1.2 | backend, ingestion | v2 | aligned
PLAN2T-INGESTION-JOBS | Updated_Project_Plan_2_Ingestion_Plan §T1.2 | backend, frontend, ingestion | v2 | aligned
PLAN2T-REPO-BATCH | Updated_Project_Plan_2_Ingestion_Plan §§T1.3–T2.2 | backend, ingestion | v2 | aligned
PLAN2T-BLUEPRINT-SUMMARIES | Updated_Project_Plan_2_Ingestion_Plan §T3 | backend, ingestion, autopilot | design-only | todo
PLAN2T-CONTEXT-MULTISTAGE | Updated_Project_Plan_2_Ingestion_Plan §T4 | backend, context | design-only | todo
PLAN2T-BUDGET-KNOBS | Updated_Project_Plan_2_Ingestion_Plan §T5 | backend, config, telemetry | design-only | todo
PLAN2MM-ROLE-ALIASES | Updated_Project_Plan_2_Model_Matrix §§1–4 | backend, model-routing | design-only | todo
PLAN2MM-WORKER-ROUTES | Updated_Project_Plan_2_Model_Matrix §3 | backend, model-routing | design-only | todo
PLAN2MM-EMBED-MODEL-HELPER | Updated_Project_Plan_2_Model_Matrix §5 | backend, ingestion | v2 | aligned
PLAN2AL-LEARNING-FIELDS | Updated_Project_Plan_2_AUTOPILOT_LEARNING §1 | backend, tasks, autopilot | design-only | todo
PLAN2AL-BLUEPRINT-UNDERSTAND | Updated_Project_Plan_2_AUTOPILOT_LEARNING §2 | backend, ingestion, autopilot | design-only | todo
PLAN2AL-RUN-OUTCOMES | Updated_Project_Plan_2_AUTOPILOT_LEARNING §§3–5 | backend, telemetry, autopilot | design-only | todo

## Placeholder sections
- Autopilot & Worker/Manager
- Model Matrix & Routing
- Ingestion & Data
- UI/UX (Tasks, Usage/Telemetry, Ingestion)
- Docs & Runbooks
- Tests & QA

## Phase 2 — Early alignments (verified)
- Ingestion jobs: Endpoints for creating/listing/canceling ingestion jobs exist and are documented (`/projects/{id}/ingestion_jobs`), matching the plan’s job-tracking requirement.  
  - Evidence: API reference (`docs/API_REFERENCE_UPDATED.md`) and backend routes in `backend/app/api/main.py`.
- Repo ingest path safety: Filesystem and terminal operations are constrained to `project.local_root_path`; `_safe_join` blocks `..`/absolute paths.  
  - Evidence: `backend/app/api/main.py` `_safe_join`, fs/terminal routes.
- Usage/telemetry surfacing: Recent task actions, confidence buckets, and model filters in UI and `/debug/telemetry`; Usage tab loads telemetry on entry.  
  - Evidence: `frontend/src/App.tsx`, Usage tab behavior; telemetry endpoint in `backend/app/api/main.py`.
- [PLAN2T-EMBED-BATCH] Batched embeddings helper with env caps is implemented as the default ingestion path.  
  - Plan source: Updated_Project_Plan_2_Ingestion_Plan §§T1.1–T1.2  
  - Evidence: `backend/app/llm/embeddings.py` (`embed_texts_batched`, `MAX_EMBED_TOKENS_PER_BATCH`, `MAX_EMBED_ITEMS_PER_BATCH`); surfaced in docs `PROGRESS.md` and `SYSTEM_OVERVIEW.md` §3.7.  
  - Status: aligned (tested via ingestion flows described in docs).
- [PLAN2T-INGESTION-JOBS] IngestionJob model + POST/GET/cancel endpoints with UI polling/history align with the plan.  
  - Plan source: Updated_Project_Plan_2_Ingestion_Plan §T1.2  
  - Evidence: `backend/app/db/models.py` (`IngestionJob`), `backend/app/api/main.py` ingestion job routes, UI in `frontend/src/App.tsx` Docs tab, documented in `docs/API_REFERENCE_UPDATED.md` and `docs/PROGRESS.md`.  
  - Status: aligned (UI and API exercised in recent QA per `PROGRESS.md`).
- [PLAN2T-REPO-BATCH] Repo ingestion batching with hash-based skipping matches the scalability plan.  
  - Plan source: Updated_Project_Plan_2_Ingestion_Plan §§T1.3–T2.2  
  - Evidence: `backend/app/llm/embeddings.py` batching; `backend/app/db/models.py` (`FileIngestionState`); `backend/app/ingestion/github_ingestor.py` batch loop and cancel flag; surfaced in `docs/SYSTEM_OVERVIEW.md` §3.7 and `docs/PROGRESS.md`.  
  - Status: aligned (progress/bytes counters and cancel surfaced in UI).
- [PLAN2MM-EMBED-MODEL-HELPER] Embedding model resolution via `OPENAI_EMBEDDING_MODEL` defaults to `text-embedding-3-small`, as required by the model matrix.  
  - Plan source: Updated_Project_Plan_2_Model_Matrix §5  
  - Evidence: `backend/app/llm/embeddings.py` `_get_embedding_model_name`, `docs/CONFIG_ENV.md` env knob, `docs/API_REFERENCE_UPDATED.md` mentions embedding defaults.  
  - Status: aligned (configurable embedding model in place).

## Guidance on classification
- **Correct alignments**: Items implemented and verified.
- **Misalignments**: Only for items started/in-progress/implemented but conflicting with plans.
- **To-do** (future work not started): Use `todo-alignment.md`.
- **Unsure**: Ambiguous/unverified; move to correct/misaligned/to-do once confirmed.

