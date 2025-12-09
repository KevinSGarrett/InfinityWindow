# Alignment Overview

This is a skim-friendly entry point for alignment and requirement tracking. For the full matrices and evidence, see `docs/alignment/` (v1 dashboard) and `docs/alignment_002/` (current matrices, requirement index, and evidence files). Use this page to jump to the right docs, code, and tests per requirement cluster. For a canonical requirements summary, see `docs/REQUIREMENTS_CRM.md`.

## How to use this doc
- Start here to see which clusters are Complete vs Partial vs Not started.
- Follow the pointers to the canonical docs (`TODO_CHECKLIST`, `PROGRESS`, design notes) and the code/tests that enforce each area.
- For deeper audits or requirement IDs, open `docs/alignment_002/alignment_summary.md` and `docs/alignment_002/requirements_index.json`.

## Clusters

### Task-aware auto-mode routing — Status: Partial
- Scope: Heuristic submode routing, telemetry counters, and a UI override are live; data-driven refinement and richer override surfaces remain.
- Docs: `docs/TODO_CHECKLIST.md` (§2), `docs/PROGRESS.md` (2025-12-13 routing Phase 2), `docs/USER_MANUAL.md` (§5.3), `docs/SYSTEM_OVERVIEW.md` (§4.1).
- Code: `backend/app/llm/openai_client.py` (routing/telemetry), `backend/app/api/main.py` (`/debug/telemetry`), `frontend/src/App.tsx` (mode + model override UI).
- Tests: `qa/mode_routing_probe.py`; `docs/TEST_PLAN.md` B-Mode-01/02; UI exercised indirectly in `frontend/tests/usage-dashboard.spec.ts` via routing charts.

### Autonomous TODO intelligence — Status: Partial
- Scope: Auto add/complete/dedupe with confidence scoring, audit notes, context-aware prompts (goals/instructions/pinned notes + blocked/dependency context), and noisy/long-history guards are live; dependency graphing and richer approval flows remain.
- Docs: `docs/TODO_CHECKLIST.md` (§2, §6), `docs/PROGRESS.md` (2025-12-14 audit trail), `docs/USER_MANUAL.md` (§6.2–6.3), `docs/tasks/AUTOMATION.md`.
- Code: `backend/app/api/main.py` (task maintainer + telemetry), `backend/app/db/models.py` (`Task.auto_notes`), `frontend/src/App.tsx` (Tasks tab + audit note display).
- Tests: `qa/tests_api/test_tasks_automation_audit.py`, `qa/tests_api` task telemetry cases; Playwright coverage in `frontend/tests/tasks-confidence.spec.ts` and `tasks-suggestions.spec.ts`.

### Usage & telemetry dashboard — Status: Partial (Phase 1/2 done; Phase 3 persistence pending)
- Scope: Cards + charts for action/model/confidence/auto-mode routes, shared filters/time window, filtered JSON/CSV exports, and inline empty/error/export-fallback states are shipped. Long-window persistence/analytics is not started.
- Docs: `docs/USAGE_TELEMETRY_DASHBOARD.md`, `docs/TODO_CHECKLIST.md` (§2, §5), `docs/PROGRESS.md` (2025-12-13/2025-12-08 entries), `docs/USER_MANUAL.md` (§11, §5.3).
- Code: `frontend/src/App.tsx` (Usage tab charts/exports), `backend/app/api/main.py` (`/debug/telemetry`, `/conversations/{id}/usage`), `backend/app/llm/openai_client.py` (telemetry counters).
- Tests: `qa/tests_api/test_usage_telemetry_dashboard.py`, `frontend/tests/usage-dashboard.spec.ts`, smoke `qa/run_smoke.py` (telemetry reset).

### Retrieval & context shaping — Status: Partial (Phase 0 complete)
- Scope: Centralized retrieval profiles for messages/docs/memory/tasks with env overrides; deeper per-surface tuning and scoring are planned.
- Docs: `docs/REQUIREMENTS_CRM.md`, `docs/TODO_CHECKLIST.md` (§2), `docs/CONFIG_ENV.md` (Retrieval profiles/Phase 0), `docs/PROGRESS.md` (2025-12-16).
- Code: `backend/app/context/retrieval_strategies.py`, retrieval wiring in `backend/app/api/main.py` and `backend/app/api/search.py`, `backend/app/vectorstore/chroma_store.py`.
- Tests: `qa/tests_api/test_retrieval_profiles.py`, search API coverage.

### Filesystem safety & Files tab UX — Status: Complete
- Scope: `local_root_path` validation with inline errors/reset-to-root in Files tab; backend confinement via `_safe_join`/`_get_project_root`.
- Docs: `docs/REQUIREMENTS_CRM.md`, `docs/TODO_CHECKLIST.md` (§3 FS UX line), `docs/PROGRESS.md` (2025-12-16), `docs/USER_MANUAL.md` (§8.1).
- Code: `backend/app/api/main.py` (`/projects/{id}/fs/list`), `_get_project_root`, `_safe_join`; `frontend/src/App.tsx` (Files tab error surfaces).
- Tests: `qa/tests_api/test_projects_fs.py`; Playwright Files tab coverage (Agent #B branch).

### Ingestion & vector store (T-phase ingestion) — Status: Complete for repo ingestion; blueprint ingestion TBD
- Scope: Repo ingestion batching, hash-skipping, and progress/audit endpoints are live with stubbed vector store support; blueprint/plan ingestion remains design-only.
- Docs: `docs/TODO_CHECKLIST.md` (§1), `docs/PROGRESS.md` (2025-12-04 ingestion batching), `docs/SYSTEM_OVERVIEW.md` (§3.7), `docs/CONFIG_ENV.md` (embedding/batch knobs).
- Code: `backend/app/llm/embeddings.py` (`embed_texts_batched`), `backend/app/vectorstore/chroma_store.py`, `backend/app/api/main.py` (ingestion job endpoints).
- Tests: `qa/ingestion_probe.py`, `qa/run_smoke.py` (ingestion smoke), `docs/TEST_PLAN.md` B-Docs cases.

