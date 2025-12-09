# Canonical Requirements Model (CRM)

Use this as the high-level map of requirement clusters, their status, and where to look in docs/code/tests. For alignment matrices and evidence, see `docs/ALIGNMENT_OVERVIEW.md` and `docs/alignment_002/`.

## Task-aware auto-mode routing — Status: Partial
- Scope: Heuristic submode routing (`auto` → code/research/fast/deep), telemetry counters, and UI model override/last-chosen display are live. Data-driven refinement and richer override surfaces remain.
- Docs: `docs/TODO_CHECKLIST.md` (§2), `docs/PROGRESS.md` (2025-12-13/10 entries), `docs/USER_MANUAL.md` (§5.3), `docs/SYSTEM_OVERVIEW.md` (§4.1).
- Code: `backend/app/llm/openai_client.py`, `backend/app/api/main.py` (`/debug/telemetry`), `frontend/src/App.tsx` (mode + model override UI).
- Tests: `qa/mode_routing_probe.py`, `docs/TEST_PLAN.md` B-Mode-01/02, `frontend/tests/usage-dashboard.spec.ts` (routing charts coverage).

## Autonomous TODO intelligence — Status: Partial
- Scope: Auto add/complete/dedupe with confidence scoring, audit notes, context-aware prompts (goals/instructions/pinned notes + blocked/dependency context), and noisy/long-history guards are live. Dependency graphing, richer approval flows, and telemetry-driven tuning remain.
- Docs: `docs/TODO_CHECKLIST.md` (§2, §6), `docs/PROGRESS.md` (2025-12-14 audit trail, 2025-12-08 noisy-history), `docs/tasks/AUTOMATION.md`, `docs/USER_MANUAL.md` (§6.2–6.3).
- Code: `backend/app/api/main.py` (task maintainer/telemetry), `backend/app/db/models.py` (`Task.auto_notes`), `frontend/src/App.tsx` (Tasks tab + audit notes).
- Tests: `qa/tests_api/test_tasks_automation_audit.py`, `qa/tests_api/test_chat_tasks_noisy.py`, `qa/tests_api/test_chat_tasks_autopilot.py`, `frontend/tests/tasks-suggestions.spec.ts`, `frontend/tests/tasks-confidence.spec.ts`, `qa/run_smoke.py`.

## Usage & telemetry dashboard — Status: Partial (Phase 1/2 done; Phase 3 future)
- Scope: Cards + charts for action/model/confidence/auto-mode routes, shared action/group/model filters and time filter, filtered JSON/CSV exports, and inline empty/error/export-fallback states are shipped. Long-window persistence/analytics (Phase 3) not started.
- Docs: `docs/USAGE_TELEMETRY_DASHBOARD.md`, `docs/TODO_CHECKLIST.md` (§2, §5), `docs/PROGRESS.md` (2025-12-13/08 entries), `docs/USER_MANUAL.md` (§11, §5.3).
- Code: `frontend/src/App.tsx` (Usage tab charts/exports), `backend/app/api/main.py` (`/debug/telemetry`, `/conversations/{id}/usage`), `backend/app/llm/openai_client.py` (telemetry counters).
- Tests: `qa/tests_api/test_usage_telemetry_dashboard.py`, `frontend/tests/usage-dashboard.spec.ts`, `qa/run_smoke.py` (telemetry reset).

## Ingestion & repo/blueprint jobs — Status: Complete for repo; design-only for blueprint ingestion
- Scope: Repo ingestion batching, hash-skipping, progress/audit endpoints, and stubbed vector store support are live. Blueprint/plan ingestion remains design-only.
- Docs: `docs/PROGRESS.md` (2025-12-04 ingestion), `docs/TODO_CHECKLIST.md` (§1, Phase T notes), `docs/SYSTEM_OVERVIEW.md` (§3.7), `docs/CONFIG_ENV.md`.
- Code: `backend/app/llm/embeddings.py` (`embed_texts_batched`), `backend/app/vectorstore/chroma_store.py`, `backend/app/api/main.py` (ingestion job endpoints).
- Tests: `qa/ingestion_probe.py`, `qa/run_smoke.py`, `docs/TEST_PLAN.md` B-Docs cases.

## Enhanced retrieval & context shaping — Status: Partial (Phase 0 complete)
- Scope: Centralized retrieval profiles for messages/docs/memory/tasks with env-configurable `top_k`/thresholds; deeper per-surface tuning and scoring remain future.
- Docs: `docs/TODO_CHECKLIST.md` (§2), `docs/SYSTEM_OVERVIEW.md`, `docs/CONFIG_ENV.md` (§5.2).
- Code: `backend/app/context/retrieval_strategies.py`, retrieval wiring in `backend/app/api/main.py` and `backend/app/api/search.py`, vector store helpers in `backend/app/vectorstore/chroma_store.py`.
- Tests: `qa/tests_api/test_retrieval_profiles.py`.

## Autopilot / Blueprint & Learning — Status: Design-only
- Scope: Blueprint/Plan graph, Manager/Worker agents, execution runs/rollback, learning signals, autonomy modes; no code/UI live yet.
- Docs: `docs/TODO_CHECKLIST.md` (§7), `docs/PROGRESS.md` (design notes), `docs/AUTOPILOT_PLAN.md`, `docs/AUTOPILOT_LEARNING.md`, `docs/alignment_002/requirements_index.json`.
- Code: Planned only.
- Tests: Planned only.

