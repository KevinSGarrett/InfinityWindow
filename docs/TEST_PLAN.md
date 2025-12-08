# InfinityWindow – End‑to‑End Test Plan (v0 / v1 / v2 Baseline)

_Goal: Systematically test all currently implemented features so we can be highly confident that the “v2” feature set described in `Hydration_File_002.txt`, `To_Do_List_001.txt`, and `docs/PROGRESS.md` is working as expected. This plan is for **exhaustive manual + scripted testing**; it does not assume an existing automated test suite. Refreshed 2025-12-12; extend with new cases as upcoming work lands (auto-mode routing reason, telemetry dashboard v2 exports/time filter, task dependency/audit)._

---

## 1. Scope & assumptions

This test plan covers:

- Backend (`backend/app/...`):
  - Core system & health.
  - Projects, conversations, messages, chat pipeline.
  - Tasks, usage, documents, search, filesystem, AI file edits.
  - Terminal integration, project instructions, decision log, conversation folders, memory items.
- Frontend (`frontend/src/App.tsx` + `App.css`):
  - All tabs and workflows in the 3‑column UI.
  - Right‑column 8‑tab workbench: Tasks, Docs, Files, Search, Terminal, Usage, Notes, Memory.
  - Manual terminal UI, AI proposals, diff/preview, “Remember this”, folders, etc.
- Vector store (`backend/chroma_data`):
  - Message/document embeddings.
  - Memory item embeddings.

- Environment matches `Hydration_File_002.txt`:
  - Windows, root at `C:\InfinityWindow`.
  - Backend expected on **http://127.0.0.1:8000** (`uvicorn app.api.main:app --host 127.0.0.1 --port 8000` from `backend` venv). If port 8000 is occupied, use a temporary port (e.g., 8001) and adjust calls accordingly.
  - Frontend at `http://127.0.0.1:5173` via `npm run dev` from `frontend`.
- **LLM key required**: Chat, embeddings, memory, search, and usage rely on a configured OpenAI/LLM key; fail fast if unset or invalid.
- DB (`backend/infinitywindow.db`) and Chroma data (`backend/chroma_data`) can be **reset** between phases when explicitly noted. Recommend migrating QA to Postgres to remove SQLite lock risk; until then heavier retry/backoff is enabled.
- Large repo ingestion batching E2E is very long-running; “Job History” UI check is flaky under load. We are temporarily deprioritizing that one test while focusing on chat/tasks/memory/instructions fixes.

Out of scope for this plan (future phases / v3+):

- Slack / LibreChat / remote GitHub / multi‑provider / multimodal.
- Huge 600k+ word hierarchical ingestion.
- Multi‑user / auth / RBAC.

---

## 2. Test phases overview

We’ll run tests in phases to keep things organized and to isolate failures:

1. **Phase A – Environment & system sanity**
   - Backend/Frontend startup, health checks, CORS, basic logging.
2. **Phase B – Core data model & CRUD**
   - Projects, conversations, messages, tasks, docs, usage.
   - **Tasks coverage gate**: must pair with `docs/tasks/TEST_PLAN_TASKS.md` and hit ≥98/100 for the task scope (API + UI + chat automation + telemetry).
3. **Phase C – Retrieval & vector store**
   - Message search, doc search, memory item retrieval.
4. **Phase D – Filesystem & AI file edits**
   - /fs/list, /fs/read, /fs/write, /fs/ai_edit, diff/preview.
5. **Phase E – Terminal integration**
   - AI terminal proposals + run, manual runner, history, error handling.
6. **Phase F – Project instructions, decision log, folders, memory items**
   - Instructions injection, decision log persistence, folders, pinned memories.
7. **Phase G – Right‑column UI 2.0 regression**
   - All 8 tabs, layout, links to backend, “Refresh all”, toasts, command palette.
8. **Phase H – Error handling & edge cases**
   - Invalid input, path traversal attempts, timeouts, missing resources.
9. **Phase I – Performance & durability spot checks**
   - Large conversations, many tasks/docs, basic performance sanity.

Each phase below lists **test cases** with:

- ID (e.g., `B-Tasks-01`).
- Preconditions.
- Steps.
- Expected results.

Results and issues for each test should be recorded in a separate test report (see `docs/TEST_REPORT_TEMPLATE.md`).  

**Scoring:** Target ≥98/100 overall. Any critical failure blocks release. For tasks, use the rubric in `docs/tasks/TEST_PLAN_TASKS.md` (also ≥98/100 target).

---

## 3. Phase A – Environment & system sanity

### A-Env-01 – Backend health check

- **Preconditions**:
  - From `C:\InfinityWindow\backend`: venv activated, `uvicorn app.api.main:app --host 127.0.0.1 --port 8000` running.
- **Steps**:
  1. `Invoke-RestMethod http://127.0.0.1:8000/health` (PowerShell) or use browser.
  2. Confirm CORS config by hitting `/health` from `http://127.0.0.1:5173` UI (refresh app header).
- **Expected**:
  - JSON: `{"status":"ok","service":"InfinityWindow","version":"0.3.0"}` (or updated version).
  - Frontend header shows “InfinityWindow vX.Y.Z” without CORS errors.

### A-Env-02 – Frontend startup

- **Preconditions**:
  - From `C:\InfinityWindow\frontend`: `npm install` completed at least once.
- **Steps**:
  1. `npm run dev` and open `http://127.0.0.1:5173` in browser.
  2. Confirm the 3‑column layout renders (Projects/Conversations, Chat, Right workbench).
- **Expected**:
  - No red errors in browser console.
  - Backend version pill visible and correct.

### A-Env-03 – Clean DB + Chroma reset (optional but recommended before full test run)

- **Preconditions**:
  - Backend stopped.
- **Steps**:
  1. Delete `backend\infinitywindow.db`.
  2. Delete `backend\chroma_data` directory.
  3. Restart backend.
  4. Use API to create a fresh “Demo Project” with `local_root_path` = `C:\InfinityWindow`.
- **Expected**:
  - New DB created with current schema (including instructions, decisions, folders, memory_items).
  - No `sqlite3.OperationalError: no such column` errors on startup.

Record any problems under `A-Env-*` in test reports.

---

## 4. Phase B – Core data model & CRUD

### B-Proj-01 – Project CRUD via API

- **Preconditions**:
  - Backend running.
- **Steps**:
  1. `POST /projects` with `{ "name": "Demo Project", "description": "Main InfinityWindow playground", "local_root_path": "C:\\InfinityWindow" }`.
  2. `GET /projects` and confirm the new project exists.
  3. `PATCH /projects/{id}` to change description and/or local_root_path.
- **Expected**:
  - Project is created, listed, and updated correctly.
  - `local_root_path` used later for filesystem and terminal.

### B-Conv-01 – Create/rename conversations (API + UI)

- **Steps**:
  1. From UI: select project, click “+ New chat”, send a message. Confirm a new conversation appears in left sidebar.
  2. Use `GET /projects/{project_id}/conversations` to confirm it in the backend.
  3. Rename via UI (“Rename” → new title) and verify via `PATCH /conversations/{id}` + list reload.
- **Expected**:
  - Conversations appear with correct titles.
  - Renames persist across reloads.

### B-Chat-01 – Chat pipeline basics

- **Steps**:
  1. In UI: send a simple question to the assistant in the Demo Project.
  2. Confirm:
     - User and assistant messages show in UI.
     - `GET /conversations/{id}/messages` returns the same text.
     - `GET /conversations/{id}/usage` returns at least one usage record with tokens and cost.
- **Expected**:
  - Chat works end‑to‑end without errors.
  - Usage panel shows totals and recent calls.

### B-Tasks-01 – Tasks CRUD + auto‑extraction sanity

- **Steps**:
  1. In UI Tasks tab: add a manual task, toggle its status open/done.
  2. Ask the assistant for “TODOs” in the chat and send a message; check if new tasks appear (auto extraction).
  3. Confirm via:
     - `GET /projects/{id}/tasks` for count and fields.
     - UI list matches backend.
- **Expected**:
  - Manual tasks behave correctly.
  - Auto‑extracted tasks appear when appropriate and do not duplicate identical open tasks.
  - Enum validation rejects bad status/priority values (422).

### B-Tasks-02 – Autonomous TODO maintenance loop

- **Purpose**: Ensure the assistant continuously maintains the project TODO list as work progresses (without explicit user commands).
- **Steps**:
  1. Start a fresh conversation and describe several upcoming work items (e.g., “Implement X, Add error handling to Y, Document Z”). Continue chatting so the system has context.
  2. After the reply, call `GET /projects/{id}/tasks` to verify the items were automatically added with status `open`.
  3. In the same conversation, state that one or more items are now finished (e.g., “We completed X and Y; mark them done.”) and continue the flow.
  4. Fetch tasks again and confirm the assistant automatically crossed off completed work, added any follow-up subtasks, and preserved/adjusted ordering as needed.
- **Expected**:
  - TODO items are created automatically from conversation context.
  - When progress/completion is mentioned, the assistant updates task status (done vs open) without being explicitly instructed to edit the list.
  - Tasks appear in a sensible order (highest-priority/newest items surfaced appropriately) or are reordered when dependencies are clarified.
  - Dependency phrasing (“depends on / after / waiting for”) is captured in auto_notes and telemetry details without duplication.

### B-Tasks-03 – Suggested-change queue & telemetry

- **Purpose**: Verify that low-confidence adds/completions are stored as suggestions, can be reviewed via the API, and are reflected in telemetry.
- **Steps**:
  1. In a chat conversation, provide intentionally vague TODO statements (e.g., “Maybe we could consider cleaning some CSS later”) so the maintainer generates low-confidence suggestions instead of immediate tasks.
  2. Call `GET /projects/{id}/task_suggestions` and confirm pending entries exist with `action_type` = `add` or `complete`, confidence values, and payload metadata (priority, blocked reason).
  3. Call `POST /task_suggestions/{id}/approve` for one suggestion and confirm:
     - A real task is added/updated.
     - The suggestion’s status changes to `approved`, and `GET /projects/{id}/tasks` shows the item with the inferred priority / blocked reason.
  4. Call `POST /task_suggestions/{id}/dismiss` for another suggestion and confirm it is removed from the pending list.
  5. Hit `/debug/telemetry` before and after the actions; confirm `auto_suggested`, `auto_added`, `auto_completed`, and `recent_actions[]` reflect the operations (look for suggestion IDs and confidence entries).
- *(Tip: For deterministic QA, you can use `POST /debug/task_suggestions/seed` to insert add/complete suggestions without waiting for a chat conversation.)*
- **Expected**:
  - Low-confidence requests generate suggestions instead of immediate changes.
  - Approve/dismiss endpoints work and mutate the task list accordingly.
  - Telemetry counters and `recent_actions` capture each action with timestamps/confidence.
  - Stale suggestions are cleared when the referenced task is already done.

### B-Tasks-E2E – Chat → tasks auto-add/auto-complete (API)

- **Purpose**: Ensure the post-chat auto-update hook creates tasks from chat and marks them done when completions are mentioned.
- **Steps**:
  1. `POST /chat` with `project_id` and a message containing two TODOs (e.g., “Add login page” and “Fix logout bug”).
  2. `GET /projects/{id}/tasks` and verify both tasks are present and `open`.
  3. `POST /chat` on the same conversation stating that one task is done (e.g., “The login page task is done now.”).
  4. `GET /projects/{id}/tasks` and verify the mentioned task is `done` and the other remains `open`.
- **Expected**:
  - Tasks are added automatically after chat without manual calls to `auto_update_tasks`.
  - Follow-up chat marks the matching task `done` and leaves unrelated tasks `open`.
  - Model override path: when mode/model override is set in the request, the response still triggers auto-update and telemetry shows the chosen model.

### B-Tasks-Noisy – Chat → tasks with noisy conversation (API)

- **Purpose**: Ensure auto-add/complete still works when the conversation includes unrelated chatter.
- **Steps**:
  1. `POST /chat` with a mix of unrelated chatter and two TODOs (e.g., “Finish the payment retry flow” and “Document the new API responses”).
  2. `GET /projects/{id}/tasks` and verify both tasks are present and `open`.
  3. `POST /chat` on the same conversation with noise plus one completion (e.g., “Payment retry flow is done; docs are still pending.”).
  4. `GET /projects/{id}/tasks` and verify the mentioned task is `done` and the other remains `open`.
- **Expected**:
  - Tasks are added despite noisy context.
  - Completion detection closes the right task and leaves others open.

- **Telemetry & Usage quick checks**  
  - `GET /debug/telemetry` before/after chat to see task counters and confidence buckets.  
  - `GET /conversations/{id}/usage` to confirm non-zero cost totals after chat; compare with Usage tab.  
  - Usage tab shows confidence buckets, recent actions with status/priority/blocked_reason/auto_notes/matched_text/task_group, model filter, time filter (all/last5/last10), action/model counts, JSON/CSV export (filtered recent actions), routing reason, and “Last chosen model”/“Next override” cards aligned with recent `/chat` runs.  
  - For exhaustive task automation/UI coverage (target ≥98/100), also run `docs/tasks/TEST_PLAN_TASKS.md` alongside this plan; it aligns with the current green Playwright + API suites on port 8000 and documents stability aids (seed data, refresh-all).
  - Confirm telemetry reset (`reset=true`) zeroes counters and clears recent actions; Usage tab refresh reflects the reset state.

#### Large repo ingestion test harness (B-Docs-01 → B-Docs-07) — long-running

- **Reset & project**: Run `tools/reset_qa_env.py --confirm` (or delete `backend\infinitywindow.db` + `backend\chroma_data`) and create `POST /projects { "name": "Ingestion QA", "local_root_path": "C:\\InfinityWindow" }`.
- **Backend**: Use `http://127.0.0.1:8000` (switch temporarily only if 8000 is occupied).
- **Repository fixture**: Use the real `C:\InfinityWindow` tree or a curated subset (`docs`, `backend\app`, `frontend\src`) so we can exercise tiny, medium, and large jobs.
- **Pre-checks**: Confirm the selected project has `local_root_path` set and that `/projects/{id}/fs/list` returns 200 for the root. Fail fast if the UI shows “local_root_path not configured” or if the status card does not appear within 10 seconds after clicking “Ingest repo”.
- **Current known issue**: The “Job History” UI check may time out under heavy load; if the rest pass, you may defer that single check and log it in the report.
- **Instrumentation**:
  - Capture every `job_id` returned from `POST /projects/{id}/ingestion_jobs`.
  - Poll `GET /projects/{id}/ingestion_jobs/{job_id}` every ~2s while a job is running; paste at least the final payload into the test report.
  - Before and after each scenario, call `/debug/telemetry` and log the `ingestion` dict (`jobs_started/completed/cancelled/failed`, `files_processed`, `files_skipped`, `bytes_processed`, `total_duration_seconds`).
  - Take UI screenshots (status card + job history table) for at least one run per scenario.
- **Automation**: 
  - `qa/ingestion_probe.py` covers the happy path, skip run, and forced failure (smoke tests).
  - `qa/ingestion_e2e_test.py` provides comprehensive E2E API testing covering all B-Docs scenarios (see `AUTOMATED_INGESTION_TESTS.md`).
  - `frontend/tests/ingestion-e2e.spec.ts` provides comprehensive E2E UI testing via Playwright (see `AUTOMATED_INGESTION_TESTS.md`).
  - Manual checks still verify the frontend and telemetry, but automated tests can run all scenarios consistently.

### B-Docs-01 – Docs CRUD + ingestion job happy path

- **Steps**:
  1. In Docs tab: ingest a small text document (name, description, content) via **Ingest text document**.
  2. Expand **Ingest local repo**, set root to `C:\InfinityWindow`, prefix `InfinityWindow/`, and click **Ingest repo**.
  3. Observe the status card transitions `pending → running → completed` and shows non-zero `processed/total` counts while the job runs (screenshot + timestamp).
  4. Poll `GET /projects/{id}/ingestion_jobs/{job_id}` until completion and confirm the JSON (status, `total_items`, `processed_items`, `total_bytes`, timestamps, `error_message=null`) matches the UI; paste the final payload into the test report.
  5. Call `GET /projects/{id}/docs` to confirm repo documents were added (look for names prefixed with `InfinityWindow/`) and record the total doc count delta.
- **Expected**:
  - Text doc and repo docs appear in list with correct IDs/names.
  - Ingestion job status/counts match between API and UI, with no backend errors.
  - Newly ingested files become searchable via `/search/docs` if doc search is enabled.

### B-Docs-02 – Ingestion job reuse & hash skipping

- **Steps**:
  1. Immediately re-run **Ingest repo** with the same root/prefix (new `job_id`).
  2. Confirm the status card and `GET /projects/{id}/ingestion_jobs/{new_job_id}` show `processed_items = 0` (or very small) because nothing changed; log elapsed time (<5s expected).
  3. Modify a single repo file (e.g., add a comment), run ingestion again, and observe that `processed_items` equals the number of changed files (typically 1).
  4. Verify the modified file’s document entry shows an updated timestamp/content via `GET /projects/{id}/docs` and note the doc ID in the report.
- **Expected**:
  - Unchanged repos finish almost instantly with `processed_items = 0`.
  - After editing one file, only that file is reprocessed and reported by both the API and UI.
  - Automated coverage: `qa/ingestion_probe.py` runs the same scenario (initial ingest + skip pass) inside FastAPI’s TestClient.

### B-Docs-03 – Progress metrics (files, bytes, duration)

- **Purpose**: Validate the batching UI and API report accurate counts/timings while a job is running.
- **Steps**:
  1. Start ingesting a medium-sized repo subset (hundreds of files; e.g., include `backend\app` + `frontend\src` globs).
  2. While status = `running`, capture the Docs tab status card twice (T+0s and T+10s) noting status text, processed vs total files, processed vs total bytes, elapsed time.
  3. In parallel, poll `GET /projects/{id}/ingestion_jobs/{job_id}` every ~2s, logging each payload (attach JSON snippets to the report).
  4. After completion, compare UI vs API snapshots to confirm counters/bytes/duration align (allowing for polling delay).
  5. Ensure `/projects/{id}/docs` refresh occurs automatically when the job finishes; note the timestamp of the refresh event.
- **Expected**:
  - UI counters mirror API data; no negative or decreasing values.
  - Duration chip roughly matches `finished_at - started_at`.
  - Docs list shows newly ingested files immediately.

### B-Docs-04 – Cancel endpoint & graceful shutdown

- **Steps**:
  1. Start a large ingest (entire repo with default globs).
  2. Once processed_items > 0, click **Cancel job** (or `POST /projects/{id}/ingestion_jobs/{job_id}/cancel`).
  3. Confirm status switches to `cancelled`, processed counters freeze, and the UI shows a success toast (record elapsed time between clicking Cancel and seeing the new status).
  4. Immediately start another ingest; verify it resumes from the beginning (hash skipping still applies to already processed files) and log `/debug/telemetry` deltas for `jobs_cancelled`, `files_processed`, and `files_skipped`.
- **Expected**:
  - Cancel endpoint returns 200; job row shows `cancelled` and reason “Cancelled by user”.
  - No partial documents remain; re-run completes normally.

### B-Docs-05 – Job history list

- **Steps**:
  1. Execute three jobs: success, cancelled (from B-Docs-04), and forced failure (see B-Docs-06). Ensure each job ID is unique and captured in the report.
  2. Open **Recent ingestion jobs** and click **Refresh**.
  3. Compare table rows to `GET /projects/{id}/ingestion_jobs?limit=20` output (IDs, statuses, files/bytes, durations, finished timestamps, error messages).
  4. Confirm loading and empty states behave (spinner while fetching, placeholder text when no jobs exist); include screenshots for both states.
- **Expected**:
  - Rows are newest-first; metrics match API payload.
  - Error column shows readable text for failed jobs.

### B-Docs-06 – Failure surfacing & telemetry

- **Steps**:
  1. Force a deterministic failure (e.g., temporarily patch `embed_texts_batched`, point to an unreadable root path, or use the failure helper from `qa/ingestion_probe.py`). If earlier runs already hashed every `*.txt` file, create a one-off file with a unique extension (e.g., `force_failure.fail`) and pass `include_globs=["*.fail"]` so at least one item is processed before the failure triggers.
  2. Run ingestion and wait for it to fail.
  3. Validate:
     - UI status card shows `failed` plus the error message (screenshot).
     - API payload contains the same `error_message`, non-zero processed counts, and `finished_at`.
     - `/debug/telemetry` shows `jobs_failed` incremented alongside files/bytes counters (log before/after values).
     - Job history row displays the failure text (attach snippet).
- **Expected**:
  - Failure messaging is clear (no stack traces).
  - Telemetry reflects the failure.
  - Automated coverage: `qa/ingestion_probe.py` forces a RuntimeError to verify this path.

### B-Docs-07 – Ingestion telemetry snapshot/reset

- **Steps**:
  1. Call `/debug/telemetry` before running any jobs; note the full `ingestion` dict.
  2. Execute the scenarios above (success, skip, cancel, failure) in sequence, capturing telemetry snapshots after each to show incremental growth.
  3. After the final scenario, verify `jobs_started`, `jobs_completed`, `jobs_cancelled`, `jobs_failed`, `files_processed`, `files_skipped`, `bytes_processed`, `total_duration_seconds` all increased appropriately (table these deltas in the report).
  4. Call `/debug/telemetry?reset=true` and ensure the ingestion counters reset to zero without affecting LLM/tasks telemetry; record the post-reset payload.
- **Expected**:
  - Counters monotonically increase per job type.
  - Reset query zeroes the ingestion stats so QA can run clean comparisons.

### B-Mode-01 – Mode/model routing sanity

- **Purpose**: Ensure every chat mode (`auto`, `fast`, `deep`, `budget`, `research`, `code`) maps to the intended OpenAI model and succeeds end-to-end.
- **Steps**:
  1. For each mode, call `POST /chat` with a short diagnostic message (`"Mode <X> QA test"`), supplying `project_id` and `mode`.
  2. Record the returned `conversation_id`.
  3. Call `GET /conversations/{conversation_id}/usage` and note `records[].model`.
  4. Compare against the desired mapping (env overrides or `_DEFAULT_MODELS` in `backend/app/llm/openai_client.py`).
- **Expected**:
  - `/chat` responds 200 for every mode.
  - Usage records show the correct model for each logical mode (e.g., `code` → codex tier, `budget` → nano tier, etc.).

### B-Mode-02 – Auto mode adaptive selection

- **Purpose**: Confirm that `mode="auto"` dynamically chooses the best-fit model per task (coding, deep research, lightweight lookup, long-form planning).
- **Steps**:
  1. With `mode="auto"`, send four diagnostic prompts (new conversation per prompt):
     - Coding-heavy, fenced code snippet (expect codex tier).
     - Deep research/literature review (expect deep-research tier).
     - Lightweight greeting (“Ping?”) (expect mini/nano tier).
     - Multi-paragraph architecture/roadmap planning request (expect deep/pro tier).
  2. For each conversation, call `GET /conversations/{conversation_id}/usage` (or inspect backend logs) to capture `records[].model`.
  3. Compare the models chosen for each task type and confirm they align with expectations.
- **Expected**:
  - Auto mode selects codex for code, deep-research models for analysis, nano/mini for trivial asks, and deep/pro for long-form planning.
  - Usage API / logs provide a clear audit trail of the chosen model per prompt.

(Continue Phase B with explicit tests for Usage, etc., as needed.)

---

## 5. Phase C – Retrieval & vector store

### C-MsgSearch-01 – Message search

- **Steps**:
  1. Have a conversation with distinctive phrases (“search test message X”). 
  2. Call `POST /search/messages` with `{ project_id, query: "search test message X", conversation_id, limit: 5 }`.
  3. Verify hits correspond to the expected messages and distances are reasonable.
- **Expected**:
  - At least one hit with matching content.

### C-DocSearch-01 – Document search

- **Steps**:
  1. Ingest a text doc with a unique phrase (“DOC_SEARCH_UNIQUE_TOKEN”). 
  2. `POST /search/docs` with `{ project_id, query: "DOC_SEARCH_UNIQUE_TOKEN", limit: 5 }`.
  3. Verify hits include that doc chunk.
- **Expected**:
  - At least one hit with the unique token.

### C-MemorySearch-01 – Memory item retrieval

- **Steps**:
  1. Create several memory items (some pinned, some not) with distinctive content.
  2. Trigger `/chat` with questions that should recall those memories.
  3. Confirm backend logs / debug output (if enabled) show memory items being used in retrieval.
- **Expected**:
  - Pinned memories are preferentially included in the retrieval context.

---

## 6. Phase D – Filesystem, Usage & AI file edits

### D-FS-01 – List and read files

- **Steps**:
  1. In Files tab: navigate to `scratch/` and click `test-notes.txt`.
  2. Confirm:
     - File list shows correct folders/files.
     - Editor loads file content.
  3. Use `GET /projects/{id}/fs/list` and `GET /projects/{id}/fs/read` for the same `subpath` and cross‑check.
- **Expected**:
  - Paths and contents match disk.

### D-FS-02 – Write file and verify

- **Steps**:
  1. Edit `scratch/test-notes.txt` via UI and click Save.
  2. Confirm content changed on disk (via Notepad or `type` / `Get-Content`).
  3. `GET /projects/{id}/fs/read` to verify new content.
- **Expected**:
  - File is updated and reloads correctly.

### D-AIEdit-01 – AI file edit with preview diff
### D-Usage-01 – Usage API returns records

- **Steps**:
  1. Run several `/chat` calls in the same conversation.
  2. `GET /conversations/{conversation_id}/usage`.
- **Expected**:
  - Summary includes tokens/cost totals.
  - Records list matches the assistant calls made.

### D-Usage-02 – Usage tab dashboard

- **Steps**:
  1. Open Usage tab in the UI; select different conversations via the dropdown.
  2. Review totals, per-model breakdown, recent assistant calls list.
  3. Click “Refresh” and “Refresh & reset” in the telemetry drawer.
- **Expected**:
  - Totals update when selecting a different conversation.
  - Per-model counts match usage records.
  - Telemetry refresh/reset updates the counters displayed.

- **Steps**:
  1. Ask assistant to tweak `scratch/test-notes.txt` (e.g., append “123456789”).
  2. In Files tab: confirm AI file-edit proposal appears with file path and instruction.
  3. Click **Preview edit** and inspect diff and full proposed content.
  4. Click **Apply AI edit** and confirm:
     - File is modified on disk.
     - Diff preview resets / shows applied status.
- **Expected**:
  - Diff shows expected change.
  - File is updated; no backend errors.

---

## 7. Phase E – Terminal integration

### E-Term-01 – AI terminal proposal loop

- **Steps**:
  1. Ask assistant to run a safe diagnostic command (e.g., `dir` in `backend`).
  2. In Terminal tab, confirm AI proposal appears.
  3. Click **Run command** and wait for result.
  4. Confirm:
     - Last terminal run panel shows correct command, CWD, exit code, stdout/stderr.
     - A structured “I ran the terminal command you proposed…” message is posted back into the conversation.
- **Expected**:
  - No errors; assistant’s next reply incorporates the command output.

### E-Term-02 – Manual terminal runner + history

- **Steps**:
  1. In Terminal tab, run a manual command (e.g., `dir scratch` with CWD = root).
  2. Confirm:
     - Output appears in Last terminal run.
     - Entry is added to manual command history with Load button.
  3. Click **Load** on a history entry and re‑run.
- **Expected**:
  - History loads commands/cwds correctly.
  - Runner behaves as expected; errors appear inline, not as alerts.

---

## 8. Phase F – Instructions, decisions, folders, memory

### F-Inst-01 – Instructions CRUD + prompt injection

- **Steps**:
  1. In Notes tab, under “Project instructions”, enter a distinctive instruction block (e.g., “Always respond with ‘INSTRUCTION_TEST_TOKEN’ in system prompts.”) and click Save.
  2. Reload instructions via the Refresh button in the Notes tab and via `GET /projects/{id}/instructions`.
  3. Start a new conversation in the same project; ask the assistant something simple.
  4. Inspect backend logs or instrument temporarily (if needed) to confirm `project.instruction_text` is added to the system message.
- **Expected**:
  - Saved instructions persist and reload correctly.
  - System prompt for `/chat` includes the instruction text for this project.

### F-Dec-01 – Decision log CRUD

- **Steps**:
  1. In Notes tab, add a decision with title “DecisionLogTest1”, category “Architecture”, and some details.
  2. Check “Link to current conversation” and ensure a conversation is selected, then save.
  3. Refresh the decision log via the Notes tab and via `GET /projects/{id}/decisions`.
- **Expected**:
  - Decision entry appears in the list with correct title, category, details, created_at.
  - `source_conversation_id` is set correctly in the backend.

### F-Fold-01 – Conversation folders CRUD + usage

- **Steps**:
  1. Create two folders in UI (e.g., “Backend”, “Frontend”) with distinct colors.
  2. Move several conversations into these folders via UI and/or `PATCH /conversations/{id}` with `folder_id`.
  3. Use `GET /projects/{id}/conversation_folders` and `GET /projects/{id}/conversations` to confirm folder metadata.
  4. Run a `/search/messages` scoped to a specific `folder_id` and verify only conversations from that folder are returned.
- **Expected**:
  - Folders can be created, renamed, archived, and deleted via API/UI.
  - Conversations show correct `folder_id`, `folder_name`, `folder_color` in UI and API.
  - Message search respects optional `folder_id` filter.

### F-Mem-01 – Memory items CRUD + retrieval

- **Steps**:
  1. In Memory tab, create several memory items with distinctive titles and content (e.g., “MEM_TEST_ALPHA”, “MEM_TEST_BETA”), some pinned, some not.
  2. Confirm via `GET /projects/{id}/memory_items` that fields are correct (tags, category, pinned flags, timestamps).
  3. Ask the assistant a question that should recall “MEM_TEST_ALPHA”; verify response references that memory and, if pinned, appears reliably across multiple chats.
- **Expected**:
  - Memory items are created, listed, updated (pin/unpin), and deleted correctly.
  - `/chat` shows evidence that relevant memories are being injected into the retrieval context (especially pinned ones).

---

## 9. Phase G – Notes, decisions, folders, memory

### G-Inst-01 – Project instructions CRUD + prompt injection

(Same as previous section.)

### G-Inst-02 – Pinned note + diff/preview

- **Steps**:
  1. In Notes tab, add/edit the pinned note and change instructions without saving.
  2. Confirm the “Unsaved changes” banner and “View last saved instructions” diff.
  3. Save and reload via UI/API to ensure pinned note and instructions persist.
- **Expected**:
  - Pinned note shows immediately; diff displays previous instructions; saving clears the banner.

### G-Dec-01 – Decision log CRUD (API)

(Same as previous section.)

### G-Dec-02 – Decision filters & actions (UI)

- **Steps**:
  1. Seed decisions with various statuses/categories/tags.
  2. In Notes tab, apply status/category/tag/search filters.
  3. Use inline actions: change status, edit tags, copy text, open linked conversation.
  4. Use follow-up task/memory buttons and verify the backend updates (`follow_up_task_id`, new memory item).
- **Expected**:
  - Filters narrow the list correctly; inline edits persist (confirmed via refresh/API).
  - Follow-up task/memory hooks create the linked records.
  - “Open conversation” jumps to the correct chat.

### G-Dec-03 – Decision automation & drafts

- **Steps**:
  1. Prompt the assistant to emit “Decision: … / We decided …”.
  2. Refresh decisions; confirm banner and `Draft/Auto` chips for the new entries.
  3. Mark recorded/dismiss; ensure banner clears; confirm follow-up hooks still work.
- **Expected**:
  - Draft decisions appear automatically; confirm/dismiss updates backend state.
  - Banner disappears once drafts are resolved.

### G-Tasks-02 – Suggestions drawer & priority UI

- **Steps**:
  1. Seed several tasks with different priorities and blocked reasons; ensure the Tasks tab shows the new chips (critical/high/low + “Blocked by …”) and audit notes under each item.
  2. Trigger at least two pending suggestions (one add, one complete) so the Tasks tab displays the “Suggested changes” drawer with a non-zero badge.
  3. Open the drawer, verify the telemetry counters (auto-added/completed/suggested) and the list of pending suggestions with confidence, priority, and blocked text.
  4. Approve one suggestion and dismiss another via the UI buttons; confirm toast notifications appear, list refreshes, and the main task list reflects the change (new task added or task marked done with audit note).
- **Expected**:
  - Priority and blocked chips render for existing tasks; audit notes are visible under tasks touched by automation.
  - Suggestions drawer shows correct counts, telemetry, and pending entries; approving/dismissing updates both the drawer and the task list.

### G-Fold-01 – Conversation folders CRUD + usage

(Same as previous section.)

### G-Mem-01 – Memory items CRUD + retrieval

(Same as previous section.)

---

## 10. Phase H – Error handling & edge cases

Examples (to be expanded as needed):

- Invalid project_id / conversation_id in API calls → 404 with clear `detail`.
- `fs/list` or `fs/read` with illegal `subpath`/`file_path` (absolute path, `..`) → 400 with clear `detail`.
- Terminal timeouts (e.g., intentionally long‑running command with low timeout) → exit_code -1 and “[Command timed out…]” in stderr.
- Non‑UTF‑8 file attempts for `/fs/read` → 400 “File is not valid UTF‑8 text; cannot be read as text.”

### H-Debug-01 – Telemetry endpoint sanity

- **Purpose**: Confirm `/debug/telemetry` exposes auto-mode and autonomous TODO counters and supports resetting between runs.
- **Steps**:
  1. Call `GET /debug/telemetry` before starting smoke tests; note `llm.auto_routes` and task counters.
  2. Send at least one auto-mode chat (ideally code + research prompts) and describe TODO items so the maintainer runs.
  3. Call `/debug/telemetry` again and confirm the counters changed accordingly.
  4. Call `/debug/telemetry?reset=true` and verify all counters return to zero.
- **Expected**:
  - Response includes `llm` (auto route + fallback stats) and `tasks` (auto_added / auto_completed / auto_deduped).
  - `reset=true` zeroes both sets of counters for the next QA run.

---

## 11. Phase I – Performance & durability spot checks

Basic, manual stress tests:

- Create a project with:
  - Many conversations (e.g., 50+) and messages (hundreds).
  - Many tasks/docs/memory items.
  - Several terminal runs and AI file edits.
- Verify:
  - UI remains responsive (no obvious hangs).
  - Search and usage queries still return reasonable results.
  - No obvious memory leak symptoms (process not ballooning during trivial usage).

---

## 12. How to record results

- For each test case, use `docs/TEST_REPORT_TEMPLATE.md` (or a dated copy) to record:
  - Test ID, description, date, environment.
  - Result: Pass / Fail / Blocked.
  - Any logs, screenshots, or error messages.
  - Follow‑up items (bug reports, doc updates, future test ideas).
- For every new issue discovered, add a corresponding entry to `docs/ISSUES_LOG.md` (matching the ISSUE-00x ID used in the test report) with a short summary, fix, and verification reference.

The goal is that, after running this plan once end‑to‑end, we have:

- A clear list of **actual failures** to fix.
- High confidence that the v0/v1/v2 stack matches the behavior described in `Hydration_File_002.txt` and `docs/PROGRESS.md`.

---

## 13. Phase J – Autopilot & Blueprint [design-only]

> The Autopilot/Blueprint features referenced here are **designs only** (see `AUTOPILOT_PLAN.md`, `AUTOPILOT_LEARNING.md`).  
> These tests become active once the corresponding models/endpoints/UI are implemented.

### J-Blueprint-01 – Large blueprint ingestion & Plan tree

- **Preconditions**:
  - Blueprint/Plan ingestion pipeline implemented.
  - A large blueprint document available (e.g., test spec with unique tokens per section).
- **Steps**:
  1. Ingest the blueprint as a `Document` and create a `Blueprint` for a project.
  2. Call `POST /blueprints/{id}/generate_plan` and wait for completion.
  3. `GET /blueprints/{id}` and verify:
     - A nested PlanNode tree exists (phases/epics/features/stories).
     - Offsets/anchors are present for nodes with underlying text.
  4. Use UI Plan tree (Tasks tab) to inspect nodes and generate tasks for at least one feature.
- **Expected**:
  - Plan tree is stable and deterministic for the same blueprint input.
  - Generated tasks are linked back to PlanNodes and appear in the Tasks tab.

### J-Autopilot-01 – Semi‑auto run lifecycle

- **Preconditions**:
  - ExecutionRun/ExecutionStep models and endpoints implemented.
  - ManagerAgent can start runs for simple “hello world” tasks.
- **Steps**:
  1. Create a sandbox project and a tiny feature (“Write hello file”). Generate a corresponding task.
  2. Set `autonomy_mode="semi_auto"` and `max_parallel_runs=1` on the project.
  3. In chat, ask: “Start work on the ‘Write hello file’ task in semi_auto mode.”
  4. Call `/projects/{id}/autopilot_tick` until a run is created and reaches `awaiting_approval` for a `write_file` step.
  5. Approve the step via `/runs/{run_id}/advance` or the UI and verify:
     - File contents match expectation.
     - Run transitions to `completed`.
     - Linked task is marked `done`.
- **Expected**:
  - Autopilot never runs unsafe commands automatically.
  - All file edits are logged as ExecutionSteps with rollback data.

### J-Autopilot-02 – Full‑auto with rollback safety

- **Preconditions**:
  - Same as J-Autopilot-01, with `autonomy_mode="full_auto"` allowed in a safe sandbox project.
- **Steps**:
  1. Seed a feature that intentionally triggers a small refactor (multiple file edits).
  2. Enable `full_auto` and trigger Autopilot via `/autopilot_tick` or UI controls.
  3. Let a run advance far enough to make several file changes.
  4. Manually inspect diffs in the Runs panel and Files tab.
  5. Call `/runs/{run_id}/rollback` (or click “Revert run” in the UI) and verify that:
     - All files touched by that run are restored to their original content.
     - Run status becomes `aborted` with an appropriate message.
- **Expected**:
  - No edits remain after rollback; git diff is clean.
  - Autopilot respects command allowlists and alignment gating throughout.


