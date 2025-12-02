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
- [~] **CI routine** (`make ci` in QA copy) defined and documented.  
- [ ] **Expand automated test coverage** beyond smoke (backend + frontend).  

---

## 2. v3 – Intelligence & automation

These items are described conceptually in `PROGRESS.md` under v3/v4+. This checklist tracks implementation status.

- [~] **Task‑aware auto‑mode routing**  
  - [x] Heuristic `_infer_auto_submode` for `auto` (`code`/`research`/`fast`/`deep`).  
  - [x] Telemetry counters for routes + fallbacks.  
  - [ ] Refine heuristics using real telemetry data.  
  - [ ] Add UI surface to inspect chosen model and override if needed.  

- [~] **Autonomous TODO intelligence**  
  - [x] Completion detection (“X is done” → mark tasks done).  
  - [x] Semantic dedupe when adding new tasks.  
  - [x] Basic ordering heuristics (open first, then by `updated_at`).  
  - [ ] Confidence scores + telemetry for auto actions (add/complete).  
  - [ ] Suggested-change queue / confirmation flow for low-confidence additions or completions.  
  - [ ] Priority & grouping heuristics (Critical / Blocked / Ready) instead of pure recency.  
  - [ ] Dependency tracking and smarter duplicate detection beyond simple similarity.  
  - [ ] Usage/telemetry dashboard showing auto-added / auto-completed / dismissed counts and accuracy samples.  
  - [ ] Audit trail snippets when the maintainer closes a task (“Closed automatically on …”).  
  - [ ] Context-aware extraction prompts (feed project goals, sprint focus, blockers).  
  - [ ] Additional QA around noisy projects and long histories.  

- [ ] **Enhanced retrieval & context shaping**  
  - [ ] Per‑feature retrieval tuning (tasks vs docs vs memory).  
  - [ ] Configurable retrieval strategies via `CONFIG_ENV.md`.  

---

## 3. v3/v4 – UX and right‑column improvements

- [x] **Right‑column 8‑tab model** (Tasks, Docs, Files, Search, Terminal, Usage, Notes, Memory).  
- [x] **Global “Refresh all”** for right‑hand panels.  
- [~] **Right‑column layout polish** (spacing, typography, panel ergonomics).  
- [x] **Search tab UX**: filters, result grouping, “open in…” affordances.  
- [x] **Usage tab UX**: better aggregation, per-project and per-conversation summaries.  
- [x] **Notes/Decisions UX**: richer metadata, tags, cross-links, pinned notes, and diff preview.  
- [x] **Notes/Decisions automation**: detect decision statements, draft entries automatically, and hook decisions to tasks/memory.  

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

---

## 5. QA & CI

- [x] `docs/TEST_PLAN.md` authored with detailed phases and IDs.  
- [x] `docs/TEST_REPORT_TEMPLATE.md` authored.  
- [x] `docs/TEST_REPORT_2025-12-02.md` completed and updated after fixes.  
- [x] `qa/` package created with smoke probes.  
- [~] `Makefile` in QA copy with `make ci` target (backend tests + frontend build).  
- [ ] Port CI configuration back into primary repo once test suite is richer.  
- [ ] Add coverage reporting and basic performance checks.  

---

## 6. Longer‑term (v4+)

These are “nice to have” or larger projects captured in `PROGRESS.md`.

- [ ] Deeper analytics and dashboards for usage and automation.  
- [ ] Import/export flows for projects (zip bundle including DB subset + docs).  
- [ ] Advanced diff/preview UX (multi‑file, multi‑step).  
- [ ] Multi‑user / roles model (if and when needed).  

Use this checklist in combination with `PROGRESS.md` when planning work for the next window. When an item is completed, update both this file and the relevant section in `PROGRESS.md`.


