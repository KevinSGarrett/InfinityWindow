# InfinityWindow TODO / Roadmap Checklist

This document is a **checklist view** of the roadmap described in `docs/PROGRESS.md`.  
It is intentionally redundant, but more actionable: use it to track what remains, in what order.

> Status here should always be consistent with `PROGRESS.md`.  
> When in doubt, treat `PROGRESS.md` as the single source of truth and update this file to match.

Legend:

- `[x]` – Completed and merged to `main`.
- `[~]` – In progress or partially complete.
- `[ ]` – Not started.

---

## 1. Core stability and QA

- [x] **Message search regression** fixed (`/search/messages` + Chroma ingestion).  
- [x] **QA smoke suite** (`qa/run_smoke.py` + probes) created and wired.  
- [x] **Guarded QA reset helper** (`tools/reset_qa_env.py`).  
- [x] **Model routing fallbacks** for `research` and `auto` modes implemented.  
- [x] **Autonomous task loop** upgraded (auto‑complete + dedupe + ordering).  
- [x] **Playwright UI smoke tests** for right‑column tabs, Files, Notes, Memory.  
- [x] **CI routine** (`make ci` in QA copy) defined and documented.  
- [x] **Expand automated test coverage** beyond smoke (backend + frontend) — Playwright + API suites green on 8000.  
- [x] **Large repo ingestion batching** so embeddings requests stay under the OpenAI token cap (split files into batches, stream progress, provide UI feedback).  
  - `embed_texts_batched` (with `MAX_EMBED_*` caps) now powers doc/repo ingestion.
  - `IngestionJob` + `FileIngestionState` tables track job progress and skip unchanged files.
  - Docs tab shows live status via `GET /projects/{id}/ingestion_jobs/{job_id}`.

---

## 2. v3 – Intelligence & automation

These items are described conceptually in `PROGRESS.md` under v3/v4+. This checklist tracks implementation status.

- [~] **Task‑aware auto‑mode routing**  
  - [x] Heuristic `_infer_auto_submode` for `auto` (`code`/`research`/`fast`/`deep`).  
  - [x] Telemetry counters for routes + fallbacks.  
  - [ ] Refine heuristics using real telemetry data.  
  - [x] Add UI surface to inspect chosen model and override if needed (model override dropdown + last chosen model display).  

- [~] **Autonomous TODO intelligence**  
  - [x] Completion detection (“X is done” → mark tasks done).  
  - [x] Semantic dedupe when adding new tasks.  
  - [x] Basic ordering heuristics (open first, then by `updated_at`).  
  - [x] Confidence scores + telemetry for auto actions (add/complete).  
  - [x] Audit trail snippets for auto-added/completed/deduped tasks (Task.auto_notes shown in Tasks/Usage; telemetry recent_actions include notes + matched_text).  
  - [~] Suggested-change queue / Approve–Dismiss flow for low-confidence additions or completions (initial version shipped; refine heuristics/UX over time).  
  - [~] Priority & grouping heuristics (Critical / Blocked / Ready) instead of pure recency.  
  - [~] Dependency tracking and smarter duplicate detection beyond simple similarity (dependency hints appended to auto notes; full graph still future).  
  - [x] Core telemetry: counters + `/debug/telemetry` endpoint + Usage tab telemetry drawer for task automation.  
- [~] Full usage/telemetry dashboard UI (graphs, filters, long‑term analytics).  (Phase 2 shipped: charts for action/model/confidence/mode with shared filters/time window, filtered JSON/CSV exports, inline empty/error states, and export error fallbacks; Phase 3 long-term analytics/persistence still future.)  
  - [x] Usage tab filters/render verification; telemetry now fetches on tab entry/Use current chat; filters verified.  
  - [x] Audit trail snippets when the maintainer closes a task (“Closed automatically on …”).  
  - [x] Context-aware extraction prompts (goals/instructions/pinned notes + blocked/dependency context injected into extraction prompt).  
  - [x] Additional QA around noisy projects and long histories.  

- [~] **Enhanced retrieval & context shaping**  
  - [x] Per‑feature retrieval tuning (Phase 0): centralized retrieval profiles (messages/docs/memory/tasks) with env-configurable `top_k`, defaults unchanged.  
  - [~] Configurable retrieval strategies via `CONFIG_ENV.md` (Phase 0 knobs added; deeper tuning still future).  

---

## 3. v3/v4 – UX and right‑column improvements

- [x] **Right‑column 8‑tab model** (Tasks, Docs, Files, Search, Terminal, Usage, Notes, Memory).  
- [x] **Global “Refresh all”** for right‑hand panels.  
- [~] **Right‑column layout polish** (spacing, typography, panel ergonomics).  
- [x] **Search tab UX**: filters, result grouping, “open in…” affordances.  
- [x] **Usage tab UX**: better aggregation, per-project and per-conversation summaries.  
- [x] **Notes/Decisions UX**: richer metadata, tags, cross-links, pinned notes, and diff preview.  
- [x] **Notes/Decisions automation**: detect decision statements, draft entries automatically, and hook decisions to tasks/memory.  

### UI / Frontend

- [ ] Refactor UI.

---

## 4. Documentation overhaul

- [x] Root `README.md` simplified and pointed at the docs library.  
- [x] `docs/README.md` created as docs index.  
- [x] `docs/SYSTEM_OVERVIEW.md` updated to be accurate and current (non‑aspirational).  
- [x] `docs/USER_MANUAL.md` created with detailed setup and usage.  
- [x] `docs/SYSTEM_MATRIX.md` created to map features ↔ files ↔ endpoints ↔ tests.  
- [x] `docs/TODO_CHECKLIST.md` (this file) created.  
- [x] `docs/HYDRATION_2025-12-02.md` created and aligned with code + docs.  
- [x] `docs/DEV_GUIDE.md` created for contributors.  
- [x] `docs/AGENT_GUIDE.md` created for AI agents.  
- [x] `docs/OPERATIONS_RUNBOOK.md` created with concrete commands and flows.  
- [x] `docs/API_REFERENCE.md` added.  
- [x] `docs/CONFIG_ENV.md` added.  
- [x] `docs/SECURITY_PRIVACY.md` added.  
- [x] `docs/DECISIONS_LOG.md` added (separate from per‑project decision entities).  
- [x] `docs/RELEASE_PROCESS.md` defined.  
- [x] `docs/CHANGELOG.md` kept current with each window.  

### Ops & Onboarding

- [ ] Write onboarding document for ops.
- [ ] Write onboarding document for ops and support teams with a rollout checklist and training videos.

---

## 5. QA & CI

- [x] `docs/TEST_PLAN.md` authored with detailed phases and IDs.  
- [x] `docs/TEST_REPORT_TEMPLATE.md` authored.  
- [x] `docs/TEST_REPORT_2025-12-02.md` completed and updated after fixes.  
- [x] `qa/` package created with smoke probes.  
- [x] `Makefile` in QA copy with `make ci` target (backend tests + frontend build).  
- [~] Port CI configuration back into primary repo once test suite is richer. (Repo-root `Makefile` now includes `ci` for backend API tests + frontend build.)  
- [x] Add coverage reporting and basic performance checks. (Coverage defaults on via `COVERAGE_ARGS`; `make perf` runs perf smoke.)
- [~] Usage/telemetry dashboard (graphs/filters/long-term analytics) – Phase 1/2 shipped (charts, shared filters/time window, filtered exports, inline error/empty states); Phase 3 (persistence/long windows) still future. See `docs/USAGE_TELEMETRY_DASHBOARD.md`.

### QA & E2E

- [x] End-to-end chat flow for search and tasks. (qa/tests_e2e/test_chat_search_tasks.py)
- [x] Add API regression for chat → tasks auto-add/complete (B-Tasks-E2E).

---

## 6. Autopilot reliability (current window)

- [x] Wire `auto_update_tasks` to run automatically after `/chat` (with retry/timeout guards).
- [x] Stabilize `auto_update_tasks` (503 mitigation + retry).
- [x] Handle missing task backlog files gracefully (skip/log missing targets).
- [~] Improve task intent extraction to reduce extra “analysis” tasks and handle vague prompts.
  - Next: tighten dedupe/completion on noisy conversations; add telemetry-backed confidence scoring. (Recent QA adds noisy/long-history coverage and conservative completion guard.)
- [x] Audit snippets for auto-added/completed/deduped tasks (stored in `Task.auto_notes` and shown in Tasks/Usage UI).
- [x] Add dependency hints to new tasks (detect “depends on/after/waiting for” phrasing; append to auto notes) and tighten dedupe thresholds.

---

## 6. Longer‑term (v4+)

These are “nice to have” or larger projects captured in `PROGRESS.md`.

- [ ] Deeper analytics and dashboards for usage and automation.  
- [ ] Import/export flows for projects (zip bundle including DB subset + docs).  
- [ ] Advanced diff/preview UX (multi‑file, multi‑step).  
- [ ] Multi‑user / roles model (if and when needed).  
- [ ] Large-ingest phase 3 ideas (post-batching): blueprint/doc ingestion parity, resumable/partial jobs, structured job logs, globs presets, and richer telemetry dashboards.  

Use this checklist in combination with `PROGRESS.md` when planning work for the next window. When an item is completed, update both this file and the relevant section in `PROGRESS.md`.

---

## 7. Autopilot, Blueprint & Learning [design-only]

These items summarize the Autopilot plan from `AUTOPILOT_PLAN.md` / `AUTOPILOT_LEARNING.md`. None are implemented yet; they represent a multi‑phase roadmap. When you start a phase, use `AUTOPILOT_IMPLEMENTATION_CHECKLIST.md` as the authoritative step‑by‑step guide.

- [ ] **Phase 1 – Blueprint & Plan graph**  
  - [ ] Add `Blueprint`, `PlanNode`, `PlanNodeTaskLink`, `TaskDependency`, `BlueprintIngestionJob` models.  
  - [ ] Implement `/projects/{id}/blueprints` and `/blueprints/{id}/generate_plan`.  
  - [ ] Add Plan tree + “Generate tasks for this node” to the Tasks tab.  

- [ ] **Phase 2 – Project Brain & context engine**  
  - [ ] Add `ConversationSummary`, `ProjectSnapshot` models.  
  - [ ] Implement context builder and alignment helper modules.  
  - [ ] Wire chat and future workers through the context builder.  

- [ ] **Phase 3 – Execution runs & workers**  
  - [ ] Add `ExecutionRun` and `ExecutionStep` models.  
  - [ ] Implement runs API + rollback.  
  - [ ] Add Runs panel/tab in the UI.  

- [ ] **Phase 4 – ManagerAgent & Autopilot heartbeat**  
  - [ ] Extend `Project` with autonomy fields (`autonomy_mode`, `active_phase_node_id`, `autopilot_paused`, `max_parallel_runs`).  
  - [ ] Implement `ManagerAgent` + `/projects/{id}/autopilot_tick` + `/projects/{id}/manager/plan` + `/projects/{id}/refine_plan`.  
  - [ ] Add Autopilot controls to the header and wire them to the backend.  

- [ ] **Phase T – Scalable ingestion & token/cost control**  
  - [x] Implement `embed_texts_batched` and `IngestionJob`/`FileIngestionState` models (repo ingestion).  
  - [~] Add ingestion job APIs and UI progress for **blueprints** (repo path shipped; blueprint/plan ingestion still design-only).  
  - [ ] Wire budget knobs (`MAX_EMBED_TOKENS_PER_BATCH`, `MAX_EMBED_ITEMS_PER_BATCH`, `MAX_CONTEXT_TOKENS_PER_CALL`, `AUTOPILOT_MAX_TOKENS_PER_RUN`).  

---

## 8. Security & Compliance

- [x] Login audit logging pipeline — completed 2025-12-05.

### Observability & Billing

- [ ] Set up billing event sink and Grafana dashboard for latency and error alerts.

---

## Completed

- [x] Healthcheck dashboard — completed 2025-12-05.