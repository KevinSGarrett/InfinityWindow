# InfinityWindow – System Overview (Current System)

This document describes **what InfinityWindow actually does today**: its architecture, core features, automation, and QA/operations story.  
For detailed setup and usage steps, see `docs/USER_MANUAL.md`. For a feature‑to‑code map, see `docs/SYSTEM_MATRIX.md`.

---

## 1. What InfinityWindow Is

InfinityWindow is a **local AI workbench for long‑running projects**.

You work inside **projects**, and each project has:

- Conversations and messages.
- Tasks (project TODO list).
- Documents and long‑term memory items.
- Project instructions and a decision log (Notes).
- Access to the local filesystem and a terminal scoped to the project root.
- Usage and telemetry information.

The assistant is meant to be a **project co‑pilot**:

- It talks to you in natural language.
- It can see and update structured project state (tasks, docs, memory).
- It can propose file edits and terminal commands, which you review and apply.

---

## 2. High-Level Architecture

### 2.1 Backend (FastAPI + SQLite + Chroma)

- **Framework**: FastAPI application in `backend/app/api/main.py`.
- **Database**: SQLite (`backend/infinitywindow.db`) via SQLAlchemy models in `backend/app/db/models.py`.
- **Vector store**: Chroma collections under `backend/chroma_data/`, managed by helpers in `backend/app/vectorstore/chroma_store.py`.
- **LLM client**: `backend/app/llm/openai_client.py` wraps model selection and calls to the OpenAI API (or compatible provider).

Main backend responsibilities:

- CRUD for projects, conversations, messages, tasks, docs, memory, decisions.
- Chat endpoint that:
  - Loads conversation history.
  - Calls the LLM with the right system instructions and context.
  - Persists the assistant’s reply.
- Search endpoints over messages (and, where implemented, docs/memory) using Chroma.
- Filesystem and terminal endpoints scoped to the project root.
- Telemetry endpoint (`/debug/telemetry`) exposing model routing and task automation counters.

### 2.2 Frontend (React + Vite)

- **Framework**: React + TypeScript with Vite in `frontend/`.
- **Main app**: `frontend/src/App.tsx`:
  - Left column: project selector + conversation list + “New chat”.
  - Middle column: chat view with mode selector and input.
  - Right column: tabbed workbench (Tasks, Docs, Files, Search, Terminal, Usage, Notes, Memory).
- **Styling**: `frontend/src/App.css` for the 3‑column layout and right‑tab UI.
- **UI tests**: Playwright tests in `frontend/tests/` validate the right‑column tabs and key panels.

The frontend talks to the backend via JSON APIs described in `docs/API_REFERENCE.md`.

---

## 3. Core Features (Today)

### 3.1 Projects, Conversations, Messages

**Data model** (see `models.py`):

- `Project`: name, description, local root path, and other metadata.
- `Conversation`: belongs to a project; groups messages into threads.
- `Message`: role (`user` / `assistant`), content, timestamps, and links to conversations and projects.

**Backend behavior**:

- Project and conversation CRUD endpoints in `app/api/main.py`.
- Chat endpoint:
  - Accepts a new user message (and optional `mode`).
  - Builds a message history.
  - Calls the LLM via `openai_client.generate_reply_from_history`.
  - Stores both user and assistant messages in the database.
  - For user/assistant messages that should be searchable, creates embeddings and stores them in Chroma.

**Frontend behavior**:

- Left column:
  - Select project from dropdown.
  - See conversations for the selected project.
  - Click to open a conversation; click “+ New chat” to start one.
- Middle column:
  - Shows messages for the active conversation.
  - Lets you pick a chat mode and send new messages.

---

### 3.2 Tasks / TODOs (Project Tasks)

**Data model**:

- `Task`:
  - `id`, `project_id`, `description`.
  - `status` (e.g., `open`, `done`).
  - Timestamps (including `updated_at`).

**Backend behavior** (`app/api/main.py`):

- Endpoints to list and create/update tasks.
- `list_project_tasks`:
  - Returns tasks for a project sorted by:
    - Status: open tasks first.
    - Recency: most recently updated first.
- `auto_update_tasks_from_conversation`:
  - Examines recent conversation lines.
  - Uses keyword and fuzzy matching to:
    - Add new tasks for TODO‑like statements.
    - Detect completion phrases (e.g., “X is done”, “Y is fixed”) and mark matching tasks as `done`.
    - Avoid adding duplicates via normalization, similarity scores, and token overlap.
  - Updates telemetry counters recording how many tasks were added, completed, or deduped.

**Frontend behavior** (Tasks tab in `App.tsx`):

- Shows the project’s tasks (open first, then done).
- Lets you:
  - Create new tasks manually.
  - Change status (e.g., toggling open/done) where wired in.
- Reflects the effects of the autonomous task updater when it runs after conversations.

---

### 3.3 Docs, Notes, Decisions, Memory

**Docs**:

- `Document` model for project‑scoped documents.
- Endpoints for listing, creating, and updating docs.
- Docs tab in the right column shows and edits these documents.

**Notes & Project Instructions**:

- `Project` has instruction text and a last‑updated timestamp.
- Endpoints to get/update project instructions.
- Notes tab shows:
  - An editor for instructions.
  - The last‑updated time.
  - Anything else the frontend renders for quick reference.

**Decision Log**:

- `Decision` (or equivalent model) records structured decisions per project.
- Endpoints to list/add decisions.
- Notes tab includes a simple decision list (title, details, timestamps) wired to these endpoints.

**Memory Items**:

- `MemoryItem` model holds long‑term, project‑scoped facts:
  - Title, content, tags, and timestamps.
- Chroma collection for memory embeddings in `chroma_store.py`.
- Endpoints under `/projects/{project_id}/memory` manage items.
- Memory tab:
  - Lists memory items.
  - Shows their titles/content.

Some endpoints and retrieval logic are focused on memory search for chat; these are kept aligned with `docs/SYSTEM_MATRIX.md` and `docs/API_REFERENCE.md`.

---

### 3.4 Filesystem Integration

**Scope**:

- All file operations are relative to a project’s `local_root_path`.
- The backend rejects paths that attempt to escape this root (e.g., via `..`).

**Endpoints** (see `API_REFERENCE.md`):

- List a directory subtree.
- Read file content.
- Write file content or apply an AI‑proposed edit under a safe join.

**Frontend (Files tab)**:

- Shows a tree or list view of files under the project root.
- Lets you:
  - Navigate into subdirectories.
  - Open a file into an editor pane.
  - Toggle “Show original” vs edited content.
  - See an “unsaved changes” indicator.
  - Save changes back to the backend.

AI file‑edit behavior is currently implemented via API calls behind this Files UI rather than complex multi‑hunk diff UIs; see `docs/SYSTEM_MATRIX.md` for the exact endpoints used today.

---

### 3.5 Terminal Integration

**Backend**:

- Endpoint to run commands in a subprocess with:
  - `cwd` constrained under the project root.
  - Timeouts and trimmed output.
- Endpoint to list recent manual terminal history.

**Frontend (Terminal tab)**:

- Input for a command and working directory.
- Output pane showing stdout/stderr and exit code.
- Basic history UI so you can re‑run past commands.

The assistant can propose commands in natural language; you copy or adapt them into the Terminal tab and run them explicitly.

---

### 3.6 Search

**Messages**:

- Embeddings for messages are stored in the Chroma “messages” collection.
- `POST /search/messages`:
  - Takes a project ID and query string.
  - Returns matching messages with metadata.

**Docs/Memory**:

- Where implemented, similar endpoints exist for searching docs and memory collections.
- The Search tab (right column) surfaces these searches in a unified UI.

Search has been explicitly tested and fixed so that message search behaves correctly in the “QA 2025‑12‑02” test run (see `docs/TEST_REPORT_2025-12-02.md`).

---

### 3.7 Usage & Telemetry

**Usage**:

- The backend tracks basic usage information per call (tokens, model, cost) and can aggregate this per project/conversation.
- The Usage tab shows a simple view into this data so you can monitor costs.

**Telemetry**:

- `openai_client.py` maintains `_LLM_TELEMETRY_COUNTERS`:
  - Counts how often `auto` routes to each sub‑mode.
  - Counts model fallback attempts and successes.
- `app/api/main.py` maintains `_TASK_TELEMETRY_COUNTERS`:
  - Counts auto‑added, auto‑completed, auto‑deduped tasks.
- `GET /debug/telemetry` returns these counters in a JSON payload for inspection and QA.

---

### 3.8 Right-Hand Workbench UI

The right‑hand column is organized into **eight tabs**:

- **Tasks** – project TODO list and statuses.
- **Docs** – project documents.
- **Files** – filesystem browser and file editor.
- **Search** – unified search UI for messages/docs/memory (where implemented).
- **Terminal** – shell command runner and history.
- **Usage** – usage/cost overview.
- **Notes** – project instructions and decision log.
- **Memory** – long‑term memory items.

Additional behaviors:

- Keyboard shortcuts (Alt+1..8) switch directly to each tab.
- A “Refresh all” control refreshes data for all right‑hand panels.
- Search tab provides filters (conversation, folder, document), grouped results, and “open in” shortcuts to jump into conversations or the Docs tab.
- Usage tab includes a conversation selector, aggregate metrics (tokens/cost/calls), per-model breakdown, recent call list, and the shared routing/tasks telemetry drawer.
- Notes tab adds pinned notes, an instructions diff preview, decision status/tag filters, inline editing, follow-up task hooks, and memory/clipboard exports for each decision card.

Playwright tests (`right-column.spec.ts`, `files-tab.spec.ts`, `notes-memory.spec.ts`) guard against regressions in this layout.

---

## 4. Automation & Model Routing

### 4.1 Chat Modes & Auto Mode

Supported modes:

- `auto`, `fast`, `deep`, `budget`, `research`, `code`.

**Routing logic** (`openai_client.py`):

- If a specific `model` is given, it is used as‑is.
- Otherwise:
  - For non‑`auto` modes, a default model is chosen based on `_DEFAULT_MODELS` and any `OPENAI_MODEL_*` overrides.
  - For `auto`:
    - `_infer_auto_submode` examines the latest user prompt:
      - Code‑like structure → route to `code`.
      - Long/research‑like prompts → route to `research`.
      - Very short/simple prompts → route to `fast`.
      - Everything else → route to `deep`.
    - Telemetry is updated with the chosen sub‑mode.

The built‑in defaults in `_DEFAULT_MODELS` (when env overrides are not set) are:

- `auto` → `gpt-4.1`
- `fast` → `gpt-4.1-mini`
- `deep` → `gpt-5.1`
- `budget` → `gpt-4.1-nano`
- `research` → `o3-deep-research`
- `code` → `gpt-5.1-codex`

**Fallbacks**:

- If the chosen model fails (e.g., unavailable or unauthorized), the client:
  - Tries a configured `OPENAI_MODEL_AUTO` as a fallback.
  - Then tries a configured `OPENAI_MODEL_FAST` as a last resort.
  - Logs fallback attempts in telemetry.

This behavior has been verified via the `qa/mode_routing_probe.py` smoke test and the mode tests in `docs/TEST_PLAN.md`.

---

### 4.2 Autonomous Task Maintenance

Summarized earlier under Tasks, but from an automation standpoint:

- **Inputs**:
  - Recent conversation messages for a project.
- **Outputs**:
  - New tasks (when explicit or implied TODOs are detected).
  - Status changes to `done` (based on completion‑like language).
- **Guards**:
  - Normalization + fuzzy matching to avoid:
    - Duplicate tasks.
    - Marking unrelated tasks as done.
- **Telemetry**:
  - Counters for how many tasks were added/completed/deduped, to monitor behavior over time.

The “Autonomous TODO maintenance” behavior is intentionally conservative and operates as a helper rather than a full auto‑planner. Manual edits in the Tasks tab always take precedence.

### 4.3 Decision Capture Drafts

- Watches recent assistant replies for statements like “Decision: …” or “We decided to …”.
- When detected:
  - Creates a draft decision (status `draft`, marked `Auto`) linked to the source conversation.
  - Surfaces a banner in the Notes tab to review/confirm/dismiss.
- Humans can still attach follow-up tasks, save to memory, or copy/export these drafts, ensuring conversational agreements become trackable decisions with almost no effort.

---

## 5. QA, Operations, and Evolution

### 5.1 QA Artifacts

- **Test plan**: `docs/TEST_PLAN.md` – detailed manual+automated test cases.
- **Test reports**: `docs/TEST_REPORT_*.md` – records of actual runs (e.g., `2025-12-02`).
- **Smoke tests**: `qa/run_smoke.py` runs:
  - Message search probe.
  - Task auto‑loop probe.
  - Mode routing probe.
- **UI tests**: Playwright specs in `frontend/tests/`.

### 5.2 Operations

- **Day‑to‑day running**:
  - Backend: `uvicorn app.api.main:app --reload`.
  - Frontend: `npm run dev`.
- **QA environment**:
  - Copy of the repo in `C:\InfinityWindow_QA`.
  - `Makefile` with `ci` target to run backend tests and frontend build.
- **Resets**:
  - `tools/reset_qa_env.py` safely backs up and deletes DB + Chroma in QA (only when uvicorn is not running).

Details live in `docs/OPERATIONS_RUNBOOK.md`.

### 5.3 Roadmap & Future Work

Planned and partially implemented features are tracked in:

- `docs/PROGRESS.md` – by window and version (v3/v4+).
- `docs/TODO_CHECKLIST.md` – checkbox view of outstanding work.

These documents are the canonical place to see what is **planned** vs. what is implemented today.

---

InfinityWindow is evolving, but the features and behaviors described above reflect the current, working system. For anything implementation‑specific, consult the code referenced in `docs/SYSTEM_MATRIX.md` and use the QA artifacts to understand how correctness is defined and tested.***

