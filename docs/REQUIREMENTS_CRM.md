# Canonical Requirements Model (CRM)

Skim-first map of requirement clusters, their status, and where to look in docs/code/tests. For matrices and evidence, see `docs/ALIGNMENT_OVERVIEW.md` and `docs/alignment_002/`.

## Task-aware auto-mode routing — Status: Partial
- Scope: Heuristic submode routing (`auto` → code/research/fast/deep), telemetry counters, UI model override/last-chosen display. Data-driven refinement remains.
- Docs: `docs/TODO_CHECKLIST.md` (§2), `docs/PROGRESS.md` (2025-12-13/10), `docs/USER_MANUAL.md` (§5.3), `docs/SYSTEM_OVERVIEW.md` (§4.1).
- Code: `backend/app/llm/openai_client.py`, `backend/app/api/main.py` (`/debug/telemetry`), `frontend/src/App.tsx` (mode + model override UI).
- Tests: `qa/mode_routing_probe.py`, `docs/TEST_PLAN.md` B-Mode-01/02, `frontend/tests/usage-dashboard.spec.ts`.

## Autonomous TODO intelligence — Status: Partial
- Scope: Auto add/complete/dedupe with confidence scoring, audit notes, context-aware prompts (goals/instructions/pinned notes + blocked/dependency context), and noisy/long-history guards. Dependency graphing and richer approval flows remain.
- Docs: `docs/TODO_CHECKLIST.md` (§2, §6), `docs/PROGRESS.md` (2025-12-14 audit trail, noisy-history hardening), `docs/tasks/AUTOMATION.md`, `docs/USER_MANUAL.md` (§6.2–6.3).
- Code: `backend/app/api/main.py` (task maintainer/telemetry), `backend/app/db/models.py` (`Task.auto_notes`), `frontend/src/App.tsx`.
- Tests: `qa/tests_api/test_tasks_automation_audit.py`, `qa/tests_api/test_chat_tasks_noisy.py`, `qa/tests_api/test_chat_tasks_autopilot.py`, `frontend/tests/tasks-suggestions.spec.ts`, `frontend/tests/tasks-confidence.spec.ts`, `qa/run_smoke.py`.

## Usage & telemetry dashboard — Status: Partial (Phase 1/2 done; Phase 3 future)
- Scope: Cards + charts for action/model/confidence/auto-mode routes; shared action/group/model filters and time filter; filtered JSON/CSV exports; inline empty/error/export-fallback states. Long-window persistence/analytics (Phase 3) not started.
- Docs: `docs/USAGE_TELEMETRY_DASHBOARD.md`, `docs/TODO_CHECKLIST.md` (§2, §5), `docs/PROGRESS.md` (2025-12-13/08), `docs/USER_MANUAL.md` (§11, §5.3).
- Code: `frontend/src/App.tsx`, `backend/app/api/main.py` (`/debug/telemetry`, `/conversations/{id}/usage`), `backend/app/llm/openai_client.py`.
- Tests: `qa/tests_api/test_usage_telemetry_dashboard.py`, `frontend/tests/usage-dashboard.spec.ts`, `qa/run_smoke.py`.

## Retrieval & context shaping — Status: Partial (Phase 0 complete)
- Scope: Centralized retrieval profiles for messages/docs/memory/tasks with env-configurable `top_k`/thresholds; deeper per-surface tuning and scoring are future (Phase 1).
- Docs: `docs/CONFIG_ENV.md` (§Retrieval profiles/Phase 0), `docs/TODO_CHECKLIST.md` (§2), `docs/PROGRESS.md` (2025-12-16 entry), `docs/SYSTEM_OVERVIEW.md`.
- Code: `backend/app/context/retrieval_strategies.py`, retrieval wiring in `backend/app/api/main.py` and `backend/app/api/search.py`, helpers in `backend/app/vectorstore/chroma_store.py`.
- Tests: `qa/tests_api/test_retrieval_profiles.py`, search API coverage (`qa/tests_api/test_api_projects.py`, `test_ingestion_e2e.py`).

## Filesystem safety & Files tab UX (PS.SAFETY.FS.001) — Status: Complete
- Scope: `local_root_path` must be valid; Files tab shows inline errors and reset-to-root guidance when path is missing/invalid; backend `_safe_join`/`_get_project_root` prevent escapes.
- Docs: `docs/TODO_CHECKLIST.md` (§3 FS UX line), `docs/PROGRESS.md` (2025-12-16), `docs/USER_MANUAL.md` (§8.1).
- Code: `backend/app/api/main.py` (`/projects/{id}/fs/list`), `_get_project_root`, `_safe_join`; `frontend/src/App.tsx` (Files tab error states).
- Tests: `qa/tests_api/test_projects_fs.py`; Playwright Files tab coverage (Agent #B branch; add when merged).

## Ingestion & repo/blueprint jobs — Status: Complete for repo; design-only for blueprint
- Scope: Repo ingestion batching/hash-skipping/progress endpoints with stubbed vector store support. Blueprint/plan ingestion remains design-only.
- Docs: `docs/PROGRESS.md` (2025-12-04), `docs/TODO_CHECKLIST.md` (§1, Phase T notes), `docs/SYSTEM_OVERVIEW.md` (§3.7), `docs/CONFIG_ENV.md`.
- Code: `backend/app/llm/embeddings.py` (`embed_texts_batched`), `backend/app/vectorstore/chroma_store.py`, `backend/app/api/main.py` (ingestion jobs).
- Tests: `qa/ingestion_probe.py`, `qa/run_smoke.py`, `docs/TEST_PLAN.md` B-Docs cases.

## Autopilot / Blueprint & Learning — Status: Design-only
- Scope: Blueprint/Plan graph, Manager/Worker agents, execution runs/rollback, learning signals, autonomy modes; no code/UI live yet.
- Docs: `docs/TODO_CHECKLIST.md` (§7), `docs/PROGRESS.md` (design notes), `docs/AUTOPILOT_PLAN.md`, `docs/AUTOPILOT_LEARNING.md`, `docs/alignment_002/requirements_index.json`.
- Code: Planned only.
- Tests: Planned only.

