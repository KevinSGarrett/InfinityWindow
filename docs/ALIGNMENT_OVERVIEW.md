# Alignment Overview

This is a skim-friendly entry point for alignment and requirement tracking. For the full matrices and evidence, see `docs/alignment/` (v1 dashboard) and `docs/alignment_002/` (current matrices, requirement index, and evidence files). Use this page to jump to the right docs, code, and tests per requirement cluster.

## How to use this doc
- Start here to see which clusters are Complete vs Partial vs Not started.
- Follow the pointers to the canonical docs (`TODO_CHECKLIST`, `PROGRESS`, design notes) and the code/tests that enforce each area.
- For deeper audits or requirement IDs, open `docs/alignment_002/alignment_summary.md` and `docs/alignment_002/requirements_index.json`.

## Clusters

### Context-aware task upkeep — Status: Partial
- Scope: The maintainer builds a `PROJECT_CONTEXT` block (instructions, pinned note/sprint focus, project goal/description, and a short list of high-priority open tasks with blocked/not-blocked flags) for automation prompts via `build_task_context_for_project` and `_TASK_CONTEXT_STATS`. Telemetry records whether context was injected and how many high-priority tasks were surfaced.
- Frontend: Usage tab shows a subtle “context-aware TODO extraction enabled” hint when instructions + pinned note are present.
- Docs: `docs/TODO_CHECKLIST.md`, `docs/PROGRESS.md`, `docs/REQUIREMENTS_CRM.md`, `docs/USER_MANUAL.md` (Usage tab note).
- Code: `backend/app/api/main.py` (context assembly, telemetry counters), `backend/app/db/models.py` (task fields), `frontend/src/App.tsx` (Usage hint), `frontend/tests/tasks-confidence.spec.ts` (seeds instructions/pinned note).
- Tests: `qa/tests_api/test_tasks_automation_prompt_context.py`, `qa/tests_api/test_tasks_automation_audit.py`, Playwright `frontend/tests/tasks-confidence.spec.ts`.

### Task-aware auto-mode routing — Status: Partial
- Scope: Heuristic submode routing, telemetry counters, and a UI override are live; data-driven refinement and richer override surfaces remain.
- Docs: `docs/TODO_CHECKLIST.md` (§2), `docs/PROGRESS.md` (routing Phase 2), `docs/USER_MANUAL.md` (§5.3), `docs/SYSTEM_OVERVIEW.md` (§4.1).
- Code: `backend/app/llm/openai_client.py` (routing/telemetry), `backend/app/api/main.py` (`/debug/telemetry`), `frontend/src/App.tsx` (mode + model override UI).
- Tests: `qa/mode_routing_probe.py`; `docs/TEST_PLAN.md` B-Mode-01/02; UI exercised indirectly in `frontend/tests/usage-dashboard.spec.ts` via routing charts.

### Autonomous TODO intelligence — Status: Partial
- Scope: Auto add/complete/dedupe with confidence scoring and audit notes plus **v2 review queue** that auto-applies high-confidence actions and queues low-confidence or dependency-blocked suggestions with reasons (confidence/dependency/duplicate). Priority chips and dependency badges surface in the Tasks tab; TaskDependency scaffolding and telemetry-driven tuning remain future.
- Docs: `docs/REQUIREMENTS_CRM.md`, `docs/TODO_CHECKLIST.md` (§2, §6), `docs/PROGRESS.md`, `docs/USER_MANUAL.md` (§6.2–6.4).
- Code: `backend/app/api/main.py` (maintainer heuristics, review queue, telemetry), `backend/app/db/models.py` (automation metadata/TaskDependency scaffold), `frontend/src/App.tsx` (Tasks tab review queue with priority/dependency chips).
- Tests: `qa/tests_api/test_tasks_automation_audit.py`, `qa/tests_api/test_usage_telemetry_dashboard.py`; Playwright `frontend/tests/tasks-confidence.spec.ts`, `frontend/tests/tasks-suggestions.spec.ts`.

### Usage & telemetry dashboard — Status: Partial (Phase 1/2 done; Phase 3 persistence pending)
- Scope: Cards + charts for action/model/confidence/auto-mode routes, shared filters/time window, filtered JSON/CSV exports, and inline empty/error/export-fallback states are shipped. Long-window persistence/analytics is not started.
- Docs: `docs/TODO_CHECKLIST.md` (§2, §5), `docs/PROGRESS.md`, `docs/USER_MANUAL.md` (§11, §5.3).
- Code: `frontend/src/App.tsx` (Usage tab charts/exports), `backend/app/api/main.py` (`/debug/telemetry`, `/conversations/{id}/usage`), `backend/app/llm/openai_client.py` (telemetry counters).
- Tests: `qa/tests_api/test_usage_telemetry_dashboard.py`, `frontend/tests/usage-dashboard.spec.ts`, smoke `qa/run_smoke.py` (telemetry reset).

### Enhanced retrieval & context shaping — Status: Partial
- Requirements: REQ-RETRIEVAL-001 (per-feature retrieval caps with env overrides) and REQ-RETRIEVAL-002 (diagnostics/UI visibility).
- Docs: `docs/REQUIREMENTS_CRM.md`, `docs/TODO_CHECKLIST.md`, `docs/PROGRESS.md`, `docs/CONFIG_ENV.md`, `docs/USER_MANUAL.md`.
- Code: `backend/app/retrieval_config.py` (env-driven `RetrievalProfile` with clamps/defaults), `backend/app/api/main.py` (`/chat` retrieval, `/debug/retrieval_config`, task upkeep), `backend/app/api/search.py` (search K limits), `frontend/src/App.tsx` (Usage tab retrieval summary).
- Tests: `qa/tests_api/test_retrieval_config.py` (defaults, env overrides, chat/search callsites); Usage tab exercised in `frontend/tests/usage-dashboard.spec.ts` and `frontend/tests/ui-usage-filters.spec.ts` alongside telemetry.

### Ingestion & vector store (T-phase ingestion) — Status: Complete for repo ingestion; blueprint ingestion TBD
- Scope: Repo ingestion batching, hash-skipping, and progress/audit endpoints are live with stubbed vector store support; blueprint/plan ingestion remains design-only.
- Docs: `docs/TODO_CHECKLIST.md` (§1), `docs/PROGRESS.md` (ingestion batching), `docs/SYSTEM_OVERVIEW.md` (§3.7), `docs/CONFIG_ENV.md` (embedding/batch knobs).
- Code: `backend/app/llm/embeddings.py` (`embed_texts_batched`), `backend/app/vectorstore/chroma_store.py`, `backend/app/api/main.py` (ingestion job endpoints).
- Tests: `qa/ingestion_probe.py`, `qa/run_smoke.py` (ingestion smoke), `docs/TEST_PLAN.md` B-Docs cases.
