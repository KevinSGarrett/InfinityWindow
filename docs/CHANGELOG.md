# InfinityWindow Changelog

This changelog records notable changes to InfinityWindow over time.  
It is intentionally high‑level; see `docs/PROGRESS.md` for detailed, per‑window notes.

---

## 2025‑12‑02 – QA & Documentation Foundation

- **Search & vector store**
  - Fixed message search regression by adjusting `folder_id` handling in Chroma metadata.
  - Added backend smoke probe for message search.

- **Model routing & chat modes**
  - Implemented `_infer_auto_submode` for smarter `auto` mode routing (`code`/`research`/`fast`/`deep`).
  - Added model fallback logic and telemetry counters.
  - Added QA probe for mode/model routing.

- **Tasks automation**
  - Upgraded autonomous TODO maintenance:
    - Detects completion phrases and marks tasks as done.
    - Performs semantic dedupe when adding new tasks.
    - Sorts tasks with open items first by recency.
  - Added telemetry for auto‑added, auto‑completed, and auto‑deduped tasks.
  - Added QA probe for tasks auto‑loop.

- **Right‑hand UI & tests**
  - Adopted 8‑tab right‑column layout (Tasks, Docs, Files, Search, Terminal, Usage, Notes, Memory).
  - Improved layout and restored left column header.
  - Added Playwright UI tests:
    - Right‑column tab activation.
    - Files tab browsing and editor behavior.
    - Notes and Memory tab content rendering.

- **QA & CI**
  - Created `qa/` smoke suite (`run_smoke.py` + probes).
  - Established QA copy (`C:\InfinityWindow_QA`) and `Makefile` with `ci` target.
  - Documented full test plan and example report (`docs/TEST_PLAN.md`, `docs/TEST_REPORT_2025-12-02.md`).

- **Docs overhaul seed**
  - Rewrote root `README.md` to be a concise overview and quickstart.
  - Added `docs/README.md` as documentation index.
  - Added:
    - `docs/SYSTEM_OVERVIEW.md` (initial), `docs/USER_MANUAL.md`.
    - `docs/SYSTEM_MATRIX.md`, `docs/TODO_CHECKLIST.md`, `docs/HYDRATION_2025-12-02.md`.
    - `docs/DEV_GUIDE.md`, `docs/AGENT_GUIDE.md`, `docs/OPERATIONS_RUNBOOK.md`.
    - `docs/API_REFERENCE.md`, `docs/CONFIG_ENV.md`, `docs/SECURITY_PRIVACY.md`.
    - This changelog.
- **Search & Usage UX**
  - Search tab now includes conversation/folder/document filters, grouped results, and one-click “open in chat/docs” actions.
  - Usage tab adds a conversation selector, aggregate metrics (tokens/cost/calls), per-model breakdown, richer recent-call list, and the shared routing/tasks telemetry drawer.
- **Notes & decisions**
  - Notes tab gained pinned notes, an instructions diff preview, decision filters (status/category/tag/search), inline editing, follow-up task/memory hooks, and clipboard exports.
  - Backend now stores decision status/tags/follow-up metadata and auto-detects “Decision…” statements in chat, saving them as drafts for human review. (Requires recreating the SQLite DB to pick up the new columns.)

## 2025‑12‑03 – QA sync & tasks intelligence regression fix

- **Frontend Tasks tab**
  - Removed legacy copies of `handleApproveTaskSuggestion` / `handleDismissTaskSuggestion` that were still defined in `frontend/src/App.tsx`, eliminating the Vite overlay and restoring the suggestion drawer actions.
  - Re-ran `tests/tasks-suggestions.spec.ts` to cover priority chips, blocked reasons, and approve/dismiss flows.

- **QA workflow hardening**
  - Documented the `robocopy` + `tools/reset_qa_env.py --confirm` process for refreshing `C:\InfinityWindow_QA` before every test pass.
  - Captured the new workflow and spot-check results in `PROGRESS.md`, `OPERATIONS_RUNBOOK.md`, and `TEST_REPORT_2025-12-03.md`.

- **Issue tracking**
  - Added `docs/ISSUES_LOG.md` to centralize all ISSUE-00x entries from the dated test reports, including the new tasks-tab regression.

## 2025‑12‑03 – Autopilot & Blueprint design docs (no runtime change)

- **Autopilot & Blueprint design**
  - Added high‑level Autopilot design docs under `docs/`:
    - `AUTOPILOT_PLAN.md` – Blueprint/Plan graph, Project Brain, ExecutionRuns/ManagerAgent, scalable ingestion.
    - `AUTOPILOT_LEARNING.md` – Project Learning Layer (difficulty/rework/risk metrics, retrospectives, refine_plan).
    - `AUTOPILOT_LIMITATIONS.md` – scope, safety rules, autonomy modes, filesystem/terminal guardrails.
    - `AUTOPILOT_EXAMPLES.md` – usage scenarios (blueprint bootstrapping, feature runs, “CEO mode”, safe failure/rollback).
    - `MODEL_MATRIX.md` – design matrix for chat modes and Autopilot roles → model IDs and env vars.
  - Extended existing docs (`SYSTEM_OVERVIEW.md`, `SYSTEM_MATRIX.md`, `API_REFERENCE.md`, `CONFIG_ENV.md`, `DEV_GUIDE.md`, `AGENT_GUIDE.md`, `TEST_PLAN.md`, `TEST_REPORT_TEMPLATE.md`, `PROGRESS.md`, `TODO_CHECKLIST.md`) to reference these designs while clearly marking them as **not yet implemented**.
  - No backend or frontend behavior was changed in this window; these docs are a roadmap for future Autopilot/Blueprint work.

## 2025‑12‑04 – Documentation consistency sweep

- Aligned docs with current backend/frontend behavior for:
  - Project root path field name (`local_root_path`).
  - Filesystem endpoints (`/projects/{id}/fs/list|read|write|ai_edit`).
  - Usage endpoint (`GET /conversations/{id}/usage`) and the Usage tab behavior.
  - Memory API routes (`/projects/{id}/memory` + `/memory_items/{id}`).  
- Standardized right‑column descriptions on the eight‑tab layout (Tasks, Docs, Files, Search, Terminal, Usage, Notes, Memory).
- Updated QA docs so Phase H is reserved for error handling and Autopilot/Blueprint tests live under Phase J (design‑only).
- Clarified Autopilot sections remain design‑only and that `CONFIG_ENV.md` / `openai_client.py` are canonical for chat‑mode defaults.

## 2025‑12‑04 – Repo ingestion batching & jobs

- **Embedding pipeline**
  - Added `embed_texts_batched` with `MAX_EMBED_TOKENS_PER_BATCH` / `MAX_EMBED_ITEMS_PER_BATCH` caps so we never exceed provider limits during ingestion.
  - Documented the new env vars in `CONFIG_ENV.md`.
- **Persistent ingestion state**
  - Added `IngestionJob` + `FileIngestionState` tables to track progress and skip unchanged files via SHA-256 digests.
- **APIs & UI**
  - Added `POST /projects/{project_id}/ingestion_jobs` and `GET /projects/{project_id}/ingestion_jobs/{job_id}`.
  - Wired the Docs tab to show live status/error messages while polling the job endpoint.
  - Updated `SYSTEM_OVERVIEW.md`, `SYSTEM_MATRIX.md`, `API_REFERENCE.md`, `USER_MANUAL.md`, `PROGRESS.md`, and `TODO_CHECKLIST.md` to capture the new flow.
- **UX & QA polish**
  - Added cancel endpoint, job history listing, and richer telemetry (files/bytes/duration).
  - Docs tab now shows live counters plus the last 20 jobs.
  - Extended `qa/ingestion_probe.py` to cover both the happy path and a forced failure so error reporting stays healthy.
- **Bug fixes & QA**
  - Fixed `discover_repo_files` so every matched file is collected (previously only the last file per directory was added).
  - Added `qa/ingestion_probe.py` to the smoke suite so ingestion jobs (and hash-skipping) are exercised automatically, and created a scripted harness (`temp_ingest_plan.py`) to run the entire B-Docs suite in QA.

Future changes should append new dated sections here, with a brief description and links to detailed notes in `docs/PROGRESS.md`.

## 2025‑12‑06 – Tasks, search, filesystem/terminal fixes and docs sync

- **Tasks & automation**
  - Added project-scoped task create (`POST /projects/{project_id}/tasks`), task delete (`DELETE /tasks/{task_id}`), and tasks overview (`GET /projects/{project_id}/tasks/overview` for tasks + suggestions).
  - Added auto-update hook after `/chat` with retry; exposed manual `POST /projects/{project_id}/auto_update_tasks`.
  - Validated task status/priority enums; cleaned stale suggestions; removed test artifacts via delete endpoint.
- **Search**
  - Fixed memory search to include `title` in Chroma metadata and responses; removed duplicate handler.
- **Filesystem**
  - `GET /projects/{project_id}/fs/read` now accepts `subpath` alias; AI edit accepts `instructions` alias.
- **Terminal**
  - Scoped terminal run no longer requires `project_id` in body; runtime check injects path param.
- **Docs & pricing**
  - Synced `API_REFERENCE.md` and `API_REFERENCE_UPDATED.md` with live endpoints and aliases; added pointer from legacy ref to updated guide.
  - Added pricing entries for `gpt-5-nano`, `gpt-5-pro`, `gpt-5.1-codex`; usage cost now reflects these models.
- **Telemetry & usage**
  - `/debug/telemetry` documents task suggestion confidence stats; usage now reports non-zero cost with pricing table updates.


