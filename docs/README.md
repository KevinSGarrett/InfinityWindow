# InfinityWindow – Documentation Index

This directory contains the main documentation set for InfinityWindow.  
Use this index as the starting point whether you are a **user**, **developer**, **operator**, or **AI agent** working in the repo.

---

## 1. Getting started (setup & usage)

- **`USER_MANUAL.md`**  
  Complete, step‑by‑step guide for:
  - Installing prerequisites (Python, Node, Git).
  - Setting up backend and frontend.
  - Creating projects and using every tab (Tasks, Docs, Files, Search, Terminal, Usage, Notes, Memory).
  - Running a QA/staging copy.

- **`SYSTEM_OVERVIEW.md`**  
  High‑level description of what InfinityWindow is today, the main concepts (projects, conversations, tasks, docs, memory, decisions), and how the pieces fit together, aligned with the current code and QA docs.

---

## 2. Architecture & design

- **`SYSTEM_MATRIX.md`**  
  Matrix catalogue that answers “where is everything and what does it do?”:
  - Features ↔ backend modules ↔ frontend components ↔ key endpoints ↔ test IDs.
  - Data models ↔ DB tables ↔ API routes ↔ UI surfaces.

- **`AUTOPILOT_PLAN.md`**  
  High‑level design for the future Autopilot system: Blueprint/Plan graph, Project Brain/context builder, ExecutionRuns/Steps, ManagerAgent, workers, and scalable ingestion.

- **`AUTOPILOT_LEARNING.md`**  
  Design for the Project Learning Layer (how future versions will use run/task signals to refine plan ordering, priorities, and risks over time).

- **`AUTOPILOT_LIMITATIONS.md`**  
  Scope and safety contract for Autopilot (what it will and will not be allowed to do, filesystem/terminal guardrails, autonomy modes).

- **`AUTOPILOT_EXAMPLES.md`**  
  End‑to‑end example workflows for Autopilot once implemented (blueprint‑driven bootstrapping, feature implementation, “CEO mode”, safe failure/rollback).

- **`MODEL_MATRIX.md`**  
  Design matrix mapping chat modes and Autopilot roles (manager, workers, summaries, intent, alignment, research) to specific model IDs and env vars.

- **`RIGHT_COLUMN_UI_PLAN.md`**  
  Design notes and iteration plans for the right‑hand workbench (Tasks, Docs, Files, Search, Terminal, Usage, Notes, Memory).

- **`PROGRESS.md`**  
  Progress log and roadmap:
  - What was implemented in each window.
  - Planned v3/v4/v5+ features.
  - Links to QA fixes and follow‑up work.

- **`CHANGELOG.md`**  
  Human‑readable history of notable changes per version/window (features added, issues fixed, behavioral changes).

---

## 3. Operations, QA & runbooks

- **`TEST_PLAN.md`**  
  End‑to‑end test plan (Phases A–I) covering:
  - Environment sanity.
  - Projects/conversations/messages.
  - Tasks/docs/search/memory.
  - Filesystem & AI edits.
  - Terminal, notes, decisions, folders.
  - Performance spot checks.

- **`TEST_REPORT_TEMPLATE.md`**  
  Template for recording QA runs based on `TEST_PLAN.md`.

- **`TEST_REPORT_2025-12-02.md`**  
  Example completed QA report from a full run against the QA environment, including identified issues and resolutions.

- **`TEST_REPORT_2025-12-03.md`**  
  Focused QA note capturing the tasks-intelligence Playwright regression (Tasks tab + suggestion drawer) and the fixes that unblocked it after syncing QA.

- **`OPERATIONS_RUNBOOK.md`**  
  Practical operations guide:
  - Starting/stopping backend & frontend.
  - Using `tools/reset_qa_env.py` to reset DB + Chroma.
  - Running backend smoke tests (`qa/run_smoke.py`).
  - Running Playwright UI tests (`npm run test:e2e`).
  - Handling backups and QA copies (e.g., `C:\InfinityWindow_QA`).

- **`TODO_CHECKLIST.md`**  
  Actionable checklist of open work items grouped by phase (v2/v3/v4), distilled from `PROGRESS.md` and QA reports.

- **`ISSUES_LOG.md`**  
  Running ledger of every issue/bug encountered during development + QA, how it was fixed, and where the fix was verified (kept in sync with the dated test reports).

---

## 4. Development & contribution

- **`DEV_GUIDE.md`**  
  For developers extending InfinityWindow:
  - How to run backend/frontend in dev mode.
  - How to add new endpoints, models, and UI tabs.
  - Coding conventions and patterns already in use.
  - How to run tests and interpret telemetry.

- **`AGENT_GUIDE.md`**  
  For AI agents working in this repo:
  - Which tools/scripts are safe to use.
  - Where to find system context (overview, matrix, hydration).
  - How to update docs and avoid destructive operations.

- **`DECISIONS_LOG.md`**  
  Global, repo‑level architectural and process decisions that apply across projects.

- **`RELEASE_PROCESS.md`**  
  Lightweight but concrete process for closing a window / cutting a release (tests, docs, CI, tagging).

---

## 5. Configuration, API & security

- **`CONFIG_ENV.md`**  
  All configuration knobs and environment variables:
  - `OPENAI_*` model envs.
  - CORS origins.
  - Ports and paths.
  - Any feature flags.

- **`API_REFERENCE.md`** (legacy quick reference; see `API_REFERENCE_UPDATED.md` for the current, complete guide)  
  Concise reference for the most important REST endpoints:
  - Projects, conversations, chat.
  - Tasks, docs, memory, decisions, folders.
  - Filesystem & terminal.
  - Telemetry (`/debug/telemetry`).

- **`API_REFERENCE_UPDATED.md`**  
  Primary, up-to-date API reference with full request/response shapes and recent fixes.

- **`SECURITY_PRIVACY.md`**  
  Current understanding of:
  - What data is stored (and where).
  - How API keys and secrets are handled.
  - Known limitations and areas for future hardening.

---

## 6. Hydration & long‑term context

- **`HYDRATION_2025-12-02.md`**  
  Updated hydration/rehydration file derived from `Hydration_File_002.txt`, reflecting:
  - Current feature set and architecture.
  - Known behaviors and invariants.
  - Where to find plans, docs, and QA artifacts.

Older text files at the repo root (e.g., `Hydration_File_001.txt`, `Hydration_File_002.txt`, `Project_Plan_00x_*.txt`) will be gradually migrated or summarized here so that this directory becomes the single source of truth.

---

## 7. How to use this docs folder

- **New users**: start with `USER_MANUAL.md`, then skim `SYSTEM_OVERVIEW.md`.
- **Developers**: read `SYSTEM_OVERVIEW.md`, `SYSTEM_MATRIX.md`, and `DEV_GUIDE.md` (when available), then consult `API_REFERENCE.md` and `CONFIG_ENV.md` as needed.
- **Operators / QA**: use `TEST_PLAN.md`, `TEST_REPORT_TEMPLATE.md`, and `OPERATIONS_RUNBOOK.md`.
- **AI agents**: load `HYDRATION_*.md`, `SYSTEM_OVERVIEW.md`, `SYSTEM_MATRIX.md`, `AUTOPILOT_PLAN.md`, and `AGENT_GUIDE.md` first, then follow instructions there.

As the documentation overhaul continues, this index will be kept up to date so all important knowledge about InfinityWindow is discoverable from one place.


