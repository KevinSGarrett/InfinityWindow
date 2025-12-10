# Alignment Overview

This is a skim-friendly entry point for alignment and requirement tracking. For the full matrices and evidence, see `docs/alignment/` (v1 dashboard) and `docs/alignment_002/` (current matrices, requirement index, and evidence files). Use this page to jump to the right docs, code, and tests per requirement cluster.

## How to use this doc
- Start here to see which clusters are Complete vs Partial vs Not started.
- Follow the pointers to the canonical docs (`TODO_CHECKLIST`, `PROGRESS`, design notes) and the code/tests that enforce each area.
- For deeper audits or requirement IDs, open `docs/alignment_002/alignment_summary.md` and `docs/alignment_002/requirements_index.json`.

## Clusters

### Task-aware auto-mode routing — Status: Partial
- Scope: Auto-mode routing v2 adds richer `_infer_auto_submode` signals (code fences/blocks, research cues, history length), telemetry route/reason counters, and UI transparency (model override + “Most recent auto route” pill in Usage).
- Docs: `docs/TODO_CHECKLIST.md` (§2), `docs/PROGRESS.md` (routing v2 entry), `docs/USER_MANUAL.md` (§5.3/§11), `docs/USAGE_TELEMETRY_DASHBOARD.md`, `docs/SYSTEM_OVERVIEW.md` (§4.1).
- Code: `backend/app/llm/openai_client.py` (routing/telemetry reasons), `backend/app/api/main.py` (`/debug/telemetry`), `frontend/src/App.tsx` (model override + route pill in Usage).
- Tests: `qa/mode_routing_probe.py`, `qa/tests_api/test_auto_mode_routing.py`; UI routing telemetry touched in `frontend/tests/ui-usage-phase3.spec.ts`.
- Remaining: data-driven tuning and any Autopilot-level routing integration.

### Autonomous TODO intelligence — Status: Partial
- Scope: Auto add/complete/dedupe with confidence scoring, audit notes, and telemetry are live; dependency graphing and richer approval flows remain.
- Docs: `docs/TODO_CHECKLIST.md` (§2, §6), `docs/PROGRESS.md` (2025-12-14 audit trail), `docs/USER_MANUAL.md` (§6.2–6.3).
- Code: `backend/app/api/main.py` (task maintainer + telemetry), `backend/app/db/models.py` (`Task.auto_notes`), `frontend/src/App.tsx` (Tasks tab + audit note display).
- Tests: `qa/tests_api/test_tasks_automation_audit.py`, `qa/tests_api` task telemetry cases; Playwright coverage in `frontend/tests/tasks-confidence.spec.ts` and `tasks-suggestions.spec.ts`.

### Usage & telemetry dashboard — Status: Implemented (Phase 1/2 UI + Phase 3 project summary)
- Scope: Phase 1/2 UI (cards/charts/filters/JSON+CSV exports) plus Phase 3 project-level summary/analytics card with 1h/24h/7d windows via `/projects/{project_id}/usage_summary`.
- Docs: `docs/USAGE_TELEMETRY_DASHBOARD.md`, `docs/TODO_CHECKLIST.md` (§2, §5), `docs/PROGRESS.md` (Phase 3 entry), `docs/USER_MANUAL.md` (§11/§5.3), `qa/tests_api/test_usage_telemetry_dashboard.py`, `qa/tests_api/test_usage_phase3.py`, `frontend/tests/ui-usage-phase3.spec.ts`.
- Code: `frontend/src/App.tsx` (Usage tab analytics card + window selector), `backend/app/api/main.py` (`/debug/telemetry`, `/conversations/{id}/usage`, `/projects/{project_id}/usage_summary`), `backend/app/llm/openai_client.py` (telemetry counters).
- Tests: `qa/tests_api/test_usage_telemetry_dashboard.py`, `qa/tests_api/test_usage_phase3.py`, `frontend/tests/ui-usage-phase3.spec.ts`, smoke `qa/run_smoke.py` (telemetry reset).

### Ingestion & vector store (T-phase ingestion) — Status: Complete for repo ingestion; blueprint ingestion TBD
- Scope: Repo ingestion batching, hash-skipping, and progress/audit endpoints are live with stubbed vector store support; blueprint/plan ingestion remains design-only.
- Docs: `docs/TODO_CHECKLIST.md` (§1), `docs/PROGRESS.md` (2025-12-04 ingestion batching), `docs/SYSTEM_OVERVIEW.md` (§3.7), `docs/CONFIG_ENV.md` (embedding/batch knobs).
- Code: `backend/app/llm/embeddings.py` (`embed_texts_batched`), `backend/app/vectorstore/chroma_store.py`, `backend/app/api/main.py` (ingestion job endpoints).
- Tests: `qa/ingestion_probe.py`, `qa/run_smoke.py` (ingestion smoke), `docs/TEST_PLAN.md` B-Docs cases.

