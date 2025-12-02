# InfinityWindow – End‑to‑End Test Plan (v0 / v1 / v2 Baseline)

_Goal: Systematically test all currently implemented features so we can be highly confident that the “v2” feature set described in `Hydration_File_002.txt`, `To_Do_List_001.txt`, and `docs/PROGRESS.md` is working as expected. This plan is for **exhaustive manual + scripted testing**; it does not assume an existing automated test suite._

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

Assumptions:

- Environment matches `Hydration_File_002.txt`:
  - Windows, root at `C:\InfinityWindow`.
  - Backend at `http://127.0.0.1:8000` via `uvicorn app.api.main:app --reload` from `backend` venv.
  - Frontend at `http://127.0.0.1:5173` via `npm run dev` from `frontend`.
- DB (`backend/infinitywindow.db`) and Chroma data (`backend/chroma_data`) can be **reset** between phases when explicitly noted.

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

---

## 3. Phase A – Environment & system sanity

### A-Env-01 – Backend health check

- **Preconditions**:
  - From `C:\InfinityWindow\backend`: venv activated, `uvicorn app.api.main:app --reload` running.
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

### B-Docs-01 – Docs CRUD + ingestion

- **Steps**:
  1. In Docs tab: ingest a small text document (name, description, content).
  2. Ingest a local repo (`C:\InfinityWindow`, prefix `InfinityWindow/`).
  3. `GET /projects/{id}/docs` to confirm documents exist.
- **Expected**:
  - Text doc and repo docs appear in list with correct IDs/names.
  - No errors in backend logs.

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

## 6. Phase D – Filesystem & AI file edits

### D-FS-01 – List and read files

- **Steps**:
  1. In Files tab: navigate to `scratch/` and click `test-notes.txt`.
  2. Confirm:
     - File list shows correct folders/files.
     - Editor loads file content.
  3. Use `GET /projects/{id}/fs/list` and `GET /projects/{id}/fs/read` for the same path and cross‑check.
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

## 9. Phase G – Right‑column UI 2.0 regression

For each tab (`Tasks`, `Docs`, `Files`, `Search`, `Terminal`, `Usage`, `Notes`, `Memory`):

- Verify:
  - Correct header, toolbar, and content.
  - No missing sections.
  - Reasonable spacing and scroll behavior.
- Use the **“Refresh all”** button and confirm:
  - Tasks, docs, files list, instructions, decisions, folders, memory items, usage, and messages all refresh without errors.

Document any visual or behavioral issues by tab ID (e.g., `G-Files-Spacing-01`).

---

## 10. Phase H – Error handling & edge cases

Examples (to be expanded as needed):

- Invalid project_id / conversation_id in API calls → 404 with clear `detail`.
- `fs/list` or `fs/read` with illegal `subpath`/`file_path` (absolute path, `..`) → 400 with clear `detail`.
- Terminal timeouts (e.g., intentionally long‑running command with low timeout) → exit_code -1 and “[Command timed out…]” in stderr.
- Non‑UTF‑8 file attempts for `/fs/read` → 400 “File is not valid UTF‑8 text; cannot be read as text.”

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

The goal is that, after running this plan once end‑to‑end, we have:

- A clear list of **actual failures** to fix.
- High confidence that the v0/v1/v2 stack matches the behavior described in `Hydration_File_002.txt` and `docs/PROGRESS.md`.


