# InfinityWindow – Progress Log (Recovery Alignment)

This log is the source of truth for status; keep `docs/TODO_CHECKLIST.md` consistent with it.

## 2025-12-11 – Enhanced retrieval & context shaping v1 (feature/retrieval-profiles-v1, feature/retrieval-profiles-frontend-v1)
- Backend now builds an env-driven `RetrievalProfile` (`messages_k/docs_k/memory_k/tasks_k`) with caps and defaults that mirror the prior 5/5/5/5 behavior; chat (`/chat`), search (`/search/messages|docs|memory`), and task upkeep share the active profile.
- Diagnostics: `GET /debug/retrieval_config` returns the active profile + source, covered by `qa/tests_api/test_retrieval_config.py` (defaults, env overrides, and chat/search callsites).
- Frontend surfaces a read-only retrieval config summary in the Usage tab alongside telemetry (branch `feature/retrieval-profiles-frontend-v1`); usage dashboard specs continue to exercise the Usage view.
- Tests/commands: `python -m pytest qa/tests_docs/test_docs_existence.py qa/tests_api/test_docs_status.py -q --disable-warnings`; `set LLM_MODE=stub` / `set VECTORSTORE_MODE=stub` + `make ci`; Playwright `frontend/tests/usage-dashboard.spec.ts` and `frontend/tests/ui-usage-filters.spec.ts` cover the Usage view with telemetry/export filters.

## 2025-12-11 – Context-aware task upkeep (feature/context-aware-tasks-v1)
- Maintainer now builds a `PROJECT_CONTEXT` block for automation prompts (instructions, pinned note/sprint focus, project goal/description, and high-priority open tasks with blocked/not-blocked flags) via `build_task_context_for_project` + `_TASK_CONTEXT_STATS`; telemetry records whether context was injected and how many high-priority tasks were surfaced.
- Usage tab shows a subtle “context-aware TODO extraction enabled” hint when instructions + pinned note are present (seeded in `frontend/tests/tasks-confidence.spec.ts`).
- QA coverage added for prompt context assembly (`qa/tests_api/test_tasks_automation_prompt_context.py`) alongside existing automation audit coverage; branch: `feature/context-aware-tasks-v1`.

## Recovery 2025-12-10
- Restored clean copy from `C:\InfinityWindow_Backup\019` into `C:\InfinityWindow_Recovery`; rebuilt SQLite/Chroma in stub mode and validated the stack.
- Wired GitHub via staging branch `recovery-main-2025-12-10`; guardrails: small single-feature branches, human merges to main, no repo-wide conflict/branch cleanup prompts.
- Recommended checks: `python -m pytest qa/tests_api` with `LLM_MODE=stub` / `VECTORSTORE_MODE=stub` and `npm run build --prefix frontend` (or `make ci` in QA copy).
- Terminal guard v1 enforced before execution; history logging skipped for blocked/failed runs.
- Terminal history v1: `TerminalHistory` model with 200-entry retention per project; API `GET /projects/{project_id}/terminal/history?limit=` returns newest-first; covered by `test_terminal_guard.py` / `test_terminal_history.py` and guard/history QA.

## 1. Core stability & QA
- Message search regression resolved; `/search/messages` + Chroma ingestion stable.
- QA smoke suite and guarded reset helper in place.
- Model routing fallbacks for research/auto modes; autonomous task loop upgraded.
- Large repo ingestion batching (`embed_texts_batched`, `IngestionJob`, `FileIngestionState`) with progress UI/polling and cancel/error handling.
- Playwright smokes + API suites green on 8000; CI routine defined; terminal guard/history shipped and covered by QA.

## 2. v3 – Intelligence & automation
- Task-aware auto-mode routing live (heuristic submode, telemetry counters, override UI); tuning with real telemetry remains.
- Autonomous TODO intelligence: auto add/complete/deduped tasks, review queue v2 with dependency/duplicate reasons, dependency hints guard completions, audit snippets + telemetry; priority/grouping heuristics partially tuned; dependency graph/advanced dedupe future.
- Usage/telemetry dashboard Phase 2 shipped (charts/filters/time window, JSON/CSV exports, inline empty/error states); long-window analytics/persistence and context-aware extraction prompts are still future.
- Retrieval/context shaping v1 shipped (env-driven `RetrievalProfile`, `/debug/retrieval_config`, Usage summary). Future: telemetry-driven tuning with real data, long-window analytics, and strategy profiles.

## 3. v3/v4 – UX and right-column
- Eight-tab right column with refresh-all; Search/Usage/Notes/Decisions UX improvements; manual terminal UI + command history.
- Layout polish continues (spacing/typography/panel ergonomics); UI refactor/theme work remains future.

## 4. Documentation overhaul
- Docs created/updated: root `README`, `docs/README`, `SYSTEM_OVERVIEW`, `USER_MANUAL`, `SYSTEM_MATRIX`, `TODO_CHECKLIST`, `HYDRATION_2025-12-02`, `DEV_GUIDE`, `AGENT_GUIDE`, `OPERATIONS_RUNBOOK`, `API_REFERENCE`, `CONFIG_ENV`, `SECURITY_PRIVACY`, `DECISIONS_LOG`, `RELEASE_PROCESS`, `CHANGELOG`.
- Ops/support onboarding docs still pending.

## 5. QA & CI
- `TEST_PLAN`, `TEST_REPORT_TEMPLATE`, `TEST_REPORT_2025-12-02` authored; `qa/` package and repo-root `Makefile ci` target available.
- Coverage/perf hooks available (`COVERAGE_ARGS`, `make perf`).
- CI runs stubbed (`LLM_MODE=stub`, `VECTORSTORE_MODE=stub`); Playwright suites (ui-smoke, ui-chat-smoke, ui-extended, tasks-suggestions, tasks-confidence) and API smoke/e2e tests green on 8000.
- Next: keep CI configuration in the primary repo aligned; long-window usage dashboard QA remains.

## 6. Autopilot reliability (current window)
- `auto_update_tasks` invoked after chat with retries/timeouts; stabilized to handle missing backlog files gracefully.
- Audit snippets + telemetry for auto-added/auto-completed/deduped tasks; dependency hints added; intent guard reduces noisy “analysis” tasks; further tuning ongoing.

## 7. Longer-term (v4+)
- Future: deeper analytics/long-window dashboards, project import/export bundles, advanced diff/preview UX, multi-user/roles, large-ingest phase 3 (blueprint/doc parity, resumable jobs, richer telemetry).

## 8. Autopilot, Blueprint & learning (design-only roadmap)
- No Autopilot/Blueprint/Manager/ExecutionRun code shipped in the recovery baseline.
- Roadmap tracked in AUTOPILOT_PLAN, AUTOPILOT_LEARNING, and Updated_Project_Plans (phases 1–4, Phase T, learning layer) — **Future / design-only**.

## 9. Security & compliance / Observability & billing
- Login audit logging pipeline completed 2025-12-05; healthcheck dashboard completed 2025-12-05.
- Billing event sink and Grafana latency/error dashboards not started.

