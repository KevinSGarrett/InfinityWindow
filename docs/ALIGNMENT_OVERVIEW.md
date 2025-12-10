# Alignment Overview

This page links requirement clusters to code, tests, and docs for the recovery build (baseline 2025-12-10). Start with `docs/REQUIREMENTS_CRM.md`, `docs/TODO_CHECKLIST.md`, and the recovery note in `docs/PROGRESS.md`, then drill into `docs/alignment_002/` for matrices and evidence.

## Clusters

### Recovery baseline & repo hygiene — Status: Complete
- Scope: canonical repos (`C:\InfinityWindow_Recovery` active, `C:\InfinityWindow_Backup\019` read-only, `C:\InfinityWindow` quarantined), branch hygiene, agent roles (A/B/C), and no mega conflict cleanups.
- Docs: `docs/REQUIREMENTS_CRM.md`, `docs/TODO_CHECKLIST.md` (§0), `docs/PROGRESS.md` (Recovery 2025-12-10), `docs/DEVELOPMENT_WORKFLOW.md`.
- Tests/process: manual guardrails (git status/branch checks) before edits; feature branches only.

### Task-aware auto-mode routing — Status: Partial
- Scope: heuristic submode routing + telemetry live; needs post-recovery validation and refinement.
- Docs: CRM, TODO (§2), `docs/PROGRESS.md` (Current status), `docs/USER_MANUAL.md` (§5.3), `docs/SYSTEM_OVERVIEW.md` (§4.1).
- Code: `backend/app/llm/openai_client.py`, `/debug/telemetry`, model override UI in `frontend/src/App.tsx`.
- Tests: `qa/mode_routing_probe.py`, `docs/TEST_PLAN.md` B-Mode-01/02, telemetry assertions in `frontend/tests/usage-dashboard.spec.ts`.

### Autonomous TODO intelligence — Status: Partial
- Scope: auto add/complete/dedupe + telemetry shipped; priority/dependency heuristics and richer approval UX remain.
- Docs: CRM, TODO (§2), `docs/PROGRESS.md` (Current status), `docs/USER_MANUAL.md` (§6.2–6.3).
- Code: `backend/app/api/main.py` maintainer + telemetry, `backend/app/db/models.py` task notes, Tasks UI in `frontend/src/App.tsx`.
- Tests: `qa/tests_api/test_tasks_automation_audit.py`, task telemetry coverage; Playwright `frontend/tests/tasks-confidence.spec.ts`, `tasks-suggestions.spec.ts`.

### Usage & telemetry dashboard — Status: Partial (Phase 1/2)
- Scope: task telemetry charts/filters/time window + JSON exports; long-window persistence/analytics are future.
- Docs: CRM, TODO (§2), `docs/PROGRESS.md` (Current status), `docs/USAGE_TELEMETRY_DASHBOARD.md`, `docs/USER_MANUAL.md` (§11).
- Code: Usage tab in `frontend/src/App.tsx`; `/debug/telemetry` and `/conversations/{id}/usage` in `backend/app/api/main.py` and `llm/openai_client.py` counters.
- Tests: `qa/tests_api/test_usage_telemetry_dashboard.py`, `frontend/tests/usage-dashboard.spec.ts`, smoke telemetry reset via `qa/run_smoke.py`.

### Ingestion & vector store — Status: Shipped (repo); Blueprint ingestion future
- Scope: text/repo ingestion jobs with hash skip, progress, cancel/history; vector search over messages/docs/memory. Blueprint/plan ingestion not present.
- Docs: CRM, TODO (§1/§3 future), `docs/PROGRESS.md` (Current status), `docs/SYSTEM_OVERVIEW.md` (§3.7), `docs/CONFIG_ENV.md` (embedding knobs).
- Code: `backend/app/llm/embeddings.py`, `backend/app/vectorstore/chroma_store.py`, ingestion job routes in `backend/app/api/main.py`.
- Tests: `qa/ingestion_probe.py`, `qa/run_smoke.py` ingestion cases, `docs/TEST_PLAN.md` B-Docs matrix.

### Autopilot / Blueprint / Export-Import — Status: Future (design-only)
- Scope: Manager/Workers, ExecutionRuns, autonomy modes, Blueprint ingestion/plan tree, export/import flows, long-horizon analytics.
- Docs: CRM (Future cluster), TODO (§3), `docs/PROGRESS.md` (Current status notes), `docs/AUTOPILOT_*` docs (design only).
- Code: not present in this repo; treat any references as roadmap.
