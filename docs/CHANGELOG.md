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

Future changes should append new dated sections here, with a brief description and links to detailed notes in `docs/PROGRESS.md`.


