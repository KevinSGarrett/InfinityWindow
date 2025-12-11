# InfinityWindow TODO / Roadmap Checklist

This checklist mirrors `docs/PROGRESS.md` and should stay in sync with it. When in doubt, treat `PROGRESS.md` as the source of truth.

Legend: `[x]` done, `[~]` partial/in progress, `[ ]` not started. Items explicitly tagged **(Future / design-only)** have no shipped code yet.

---

## Recovery 2025-12-10 (baseline restoration)
- [x] Restore clean copy from `C:\InfinityWindow_Backup\019` into `C:\InfinityWindow_Recovery`; rebuild SQLite/Chroma in stub mode and validate stack.
- [x] Wire GitHub via recovery branch (`recovery-main-2025-12-10`); keep main human-merged with small, single-feature branches.
- [x] CI sanity: stubbed API tests + frontend build for the recovery baseline.
- [x] Terminal guard v1 (approval/guard before `/terminal/run`, aligned with QA guardrails).
- [x] Terminal history v1 (TerminalHistory model, newest-first feed, 200-entry retention per project, history skipped for blocked runs).

---

## 1. Core stability & QA
- [x] Message search regression fixed (`/search/messages` + Chroma ingestion).
- [x] QA smoke suite (`qa/run_smoke.py` + probes) created and wired.
- [x] Guarded QA reset helper (`tools/reset_qa_env.py`).
- [x] Model routing fallbacks for `research` and `auto` modes implemented.
- [x] Autonomous task loop upgraded (auto-complete + dedupe + ordering).
- [x] Playwright UI smoke tests for right-column tabs, Files, Notes, Memory.
- [x] CI routine (`make ci` in QA copy) defined and documented.
- [x] Expand automated test coverage beyond smoke (backend + frontend) — Playwright + API suites green on 8000.
- [x] Large repo ingestion batching (token caps, `embed_texts_batched`, `IngestionJob` + `FileIngestionState`, job progress UI/polling).
- [x] Terminal guard v1 and Terminal history v1 (Recovery 2025-12-10) landed and covered by guard/history QA.

---

## 2. v3 – Intelligence & automation
- [~] Task-aware auto-mode routing  
  - [x] Heuristic `_infer_auto_submode` for `auto` (`code`/`research`/`fast`/`deep`).  
  - [x] Telemetry counters for routes + fallbacks.  
  - [ ] Refine heuristics using real telemetry data.  
  - [x] UI surface to inspect chosen model and override if needed (model override dropdown + last chosen model display).  
- [~] Autonomous TODO intelligence  
  - [x] Completion detection (“X is done” → mark tasks done).  
  - [x] Semantic dedupe when adding new tasks.  
  - [x] Basic ordering heuristics (open first, then by `updated_at`).  
  - [x] Confidence scores + telemetry for auto actions (add/complete).  
  - [x] Audit trail snippets for auto-added/completed/deduped tasks (Task.auto_notes shown in Tasks/Usage; telemetry recent_actions include notes + matched_text).  
  - [x] Review queue v2 (auto-apply high-confidence; queued with reasons when low-confidence, dependency-blocked, or duplicate).  
  - [x] Dependency-aware automation (dependency hints block unsafe auto-closes; surfaced in suggestions/audit).  
  - [~] Priority & grouping heuristics (Critical / Blocked / Ready) tuning continues.  
  - [~] Dependency tracking / smarter duplicate detection beyond simple similarity (graph-level future).  
  - [x] Core telemetry: counters + `/debug/telemetry` endpoint + Usage tab telemetry drawer.  
  - [ ] Telemetry-driven tuning using real-world usage data (future).  
- [~] Usage/telemetry dashboard UI (Phase 2 shipped: charts/filters/time window + JSON/CSV exports; Phase 3 long-term analytics/persistence remains future).  
  - [x] Usage tab filters/render verification (short-window).  
  - [x] Audit trail snippets when maintainer closes tasks (“Closed automatically on …”).  
  - [ ] Context-aware extraction prompts (feed project goals/sprint focus/blockers).  
  - [x] Additional QA around noisy projects and long histories.  
- [ ] Enhanced retrieval & context shaping  
  - [ ] Per-feature retrieval tuning (tasks vs docs vs memory).  
  - [ ] Configurable retrieval strategies via `CONFIG_ENV.md`.  

---

## 3. v3/v4 – UX and right-column improvements
- [x] Right-column 8-tab model (Tasks, Docs, Files, Search, Terminal, Usage, Notes, Memory).
- [x] Global “Refresh all” for right-hand panels.
- [~] Right-column layout polish (spacing, typography, panel ergonomics).
- [x] Search tab UX: filters, result grouping, “open in…” affordances.
- [x] Usage tab UX: aggregation, per-project and per-conversation summaries.
- [x] Notes/Decisions UX: richer metadata, tags, cross-links, pinned notes, diff preview.
- [x] Notes/Decisions automation: detect decisions in chat, draft entries automatically, hook decisions to tasks/memory.

### UI / Frontend
- [ ] Refactor UI (structural refactor / theme work).

---

## 4. Documentation overhaul
- [x] Root `README.md` simplified and pointed at the docs library.
- [x] `docs/README.md` created as docs index.
- [x] `docs/SYSTEM_OVERVIEW.md` updated to be accurate and current (non-aspirational).
- [x] `docs/USER_MANUAL.md` created with detailed setup and usage.
- [x] `docs/SYSTEM_MATRIX.md` maps features ↔ files ↔ endpoints ↔ tests.
- [x] `docs/TODO_CHECKLIST.md` (this file) created.
- [x] `docs/HYDRATION_2025-12-02.md` aligned with code + docs.
- [x] `docs/DEV_GUIDE.md` created for contributors.
- [x] `docs/AGENT_GUIDE.md` created for AI agents.
- [x] `docs/OPERATIONS_RUNBOOK.md` created with concrete commands and flows.
- [x] `docs/API_REFERENCE.md` added.
- [x] `docs/CONFIG_ENV.md` added.
- [x] `docs/SECURITY_PRIVACY.md` added.
- [x] `docs/DECISIONS_LOG.md` added (separate from per-project decision entities).
- [x] `docs/RELEASE_PROCESS.md` defined.
- [x] `docs/CHANGELOG.md` kept current with each window.

### Ops & Onboarding
- [ ] Write onboarding document for ops.
- [ ] Write onboarding for ops/support teams with rollout checklist and training videos.

---

## 5. QA & CI
- [x] `docs/TEST_PLAN.md` authored with detailed phases and IDs.
- [x] `docs/TEST_REPORT_TEMPLATE.md` authored.
- [x] `docs/TEST_REPORT_2025-12-02.md` completed and updated after fixes.
- [x] `qa/` package created with smoke probes.
- [x] `Makefile` in QA copy with `make ci` target (backend tests + frontend build).
- [~] Port CI configuration back into primary repo once test suite is richer (repo-root `Makefile ci` exists; keep verifying).
- [x] Add coverage reporting and basic performance checks (`COVERAGE_ARGS`, `make perf`).
- [~] Usage/telemetry dashboard QA (Phase 1/2 shipped; Phase 3 long-window analytics pending).

### QA & E2E
- [x] End-to-end chat flow for search and tasks (`qa/tests_e2e/test_chat_search_tasks.py`).
- [x] API regression for chat → tasks auto-add/complete (B-Tasks-E2E).
- [x] Playwright suites green on 8000 (ui-smoke, ui-chat-smoke, ui-extended, tasks-suggestions, tasks-confidence).

---

## 6. Autopilot reliability (current window)
- [x] Wire `auto_update_tasks` to run automatically after `/chat` (with retry/timeout guards).
- [x] Stabilize `auto_update_tasks` (503 mitigation + retry).
- [x] Handle missing task backlog files gracefully (skip/log missing targets).
- [~] Improve task intent extraction to reduce noisy “analysis” tasks; continue tuning dedupe/completion and telemetry-backed confidence scoring.
- [x] Audit snippets for auto-added/completed/deduped tasks (stored in `Task.auto_notes`, shown in Tasks/Usage UI).
- [x] Add dependency hints to new tasks and tighten dedupe thresholds.

---

## 7. Longer-term (v4+)
- [ ] Deeper analytics and dashboards for usage and automation (long-window).
- [ ] Import/export flows for projects (zip bundle including DB subset + docs).
- [ ] Advanced diff/preview UX (multi-file, multi-step).
- [ ] Multi-user / roles model (if and when needed).
- [ ] Large-ingest phase 3 ideas (post-batching: blueprint/doc ingestion parity, resumable/partial jobs, structured job logs, presets, richer telemetry).

---

## 8. Autopilot, Blueprint & Learning (design-only)
These are roadmap-only items (no shipped code); see AUTOPILOT_PLAN / AUTOPILOT_LEARNING docs.
- [ ] Phase 1 – Blueprint & Plan graph (models/endpoints/UI).
- [ ] Phase 2 – Project Brain & context engine.
- [ ] Phase 3 – Execution runs & workers.
- [ ] Phase 4 – ManagerAgent & Autopilot heartbeat.
- [ ] Phase T – Scalable ingestion & token/cost control (blueprint ingestion parity, cost guardrails).
- [ ] Project learning layer (run outcomes, plan refinement, blueprint understanding).

---

## 9. Security & Compliance / Observability & Billing
- [x] Login audit logging pipeline — completed 2025-12-05.
- [ ] Observability & billing dashboards (billing event sink, Grafana alerts).

---

## Completed rollup
- [x] Healthcheck dashboard — completed 2025-12-05.
