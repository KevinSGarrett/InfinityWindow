# InfinityWindow – System Overview (Current System)

This document describes **what InfinityWindow actually does today**: its architecture, core features, automation, and QA/operations story.  
For detailed setup and usage steps, see `docs/USER_MANUAL.md`. For a feature‑to‑code map, see `docs/SYSTEM_MATRIX.md`. For developer workflow and Git/GitHub steps, see `docs/DEVELOPMENT_WORKFLOW.md`.

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
- Usage endpoint (`/conversations/{id}/usage`) with cost/tokens per conversation; `/debug/telemetry?reset=true` clears task/LLM counters.

### 2.2 Frontend (React + Vite)

- **Framework**: React + TypeScript with Vite in `frontend/`.
- **Main app**: `frontend/src/App.tsx`:
  - Left column: project selector + conversation list + “New chat”.
  - Middle column: chat view with mode selector and input.
  - Right column: tabbed workbench (Tasks, Docs, Files, Search, Terminal, Usage, Notes, Memory).
- **Styling**: `frontend/src/App.css` for the 3‑column layout and right‑tab UI.
- **UI tests**: Playwright tests in `frontend/tests/` validate the right‑column tabs and key panels.

The frontend talks to the backend via JSON APIs described in `docs/API_REFERENCE_UPDATED.md` (primary) and the legacy quick reference `docs/API_REFERENCE.md`.

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
- Endpoints for listing, creating, updating, and deleting docs (see `API_REFERENCE_UPDATED.md`).
- Docs tab in the right column shows and edits these documents.

**Notes & Project Instructions**:

- `Project` has instruction text and a last‑updated timestamp.
- Endpoints to get/update project instructions.
- Notes tab shows:
  - An editor for instructions.
  - The last‑updated time.
  - Anything else the frontend renders for quick reference.

**Decision Log**:

- `Decision` records structured decisions per project.
- Endpoints to list/add/patch/delete decisions.
- Notes tab includes a decision list (title, details, status/tags, timestamps) wired to these endpoints.

**Memory Items**:

- `MemoryItem` model holds long‑term, project‑scoped facts:
  - Title, content, tags, timestamps, optional pinned flag.
- Chroma collection for memory embeddings in `chroma_store.py` stores `title` in metadata for memory search.
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

**Endpoints** (see `API_REFERENCE_UPDATED.md`):

- `GET /projects/{id}/fs/list` – list a directory subtree.
- `GET /projects/{id}/fs/read` – read file content (`file_path` or `subpath`).
- `PUT /projects/{id}/fs/write` – write file content (optional create dirs).
- `POST /projects/{id}/fs/ai_edit` – apply/preview AI edit (`instruction` or `instructions`).

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
  - Scoped variant injects `project_id` from the path (body `project_id` optional).
- Endpoint to list recent manual terminal history (stub/placeholder).

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

- Search endpoints for docs and memory collections.
- Memory search returns `memory_id`, `title`, `content`, `distance`.
- The Search tab (right column) surfaces these searches in a unified UI.

Search has been explicitly tested and fixed so that message search behaves correctly in the “QA 2025‑12‑02” test run (see `docs/TEST_REPORT_2025-12-02.md`). Memory search was fixed to include `title` and remove duplicate handlers (2025‑12‑06).

---

### 3.7 Repo & Document Ingestion

**Data model additions**:

- `Document` (described above) stores the ingested file/text.
- `IngestionJob` tracks long-running repo/document ingests (kind, `source`, status, counts, error).
- `FileIngestionState` stores SHA‑256 digests per project/path so subsequent ingests skip unchanged files.

**Backend pipeline**:

- `ingest_text_document` chunks text, calls `embed_texts_batched`, writes chunks + embeddings to Chroma/SQLite.
- `embed_texts_batched` (in `app/llm/embeddings.py`) enforces `MAX_EMBED_TOKENS_PER_BATCH` (50k default) and `MAX_EMBED_ITEMS_PER_BATCH` (256 default) so embedding calls stay within provider limits.
- `ingest_repo_job` runs via FastAPI background tasks:
  - Discovers files, hashes them, and skips unchanged files based on `FileIngestionState`.
  - Streams progress back to the DB (`processed_items`, `processed_bytes`, timestamps).
  - Supports cancellation by honoring the `cancel_requested` flag between files.
- Telemetry counters capture jobs started/completed/failed/cancelled plus total bytes processed so `/debug/telemetry` can report ingest health.

**Endpoints**:

- `POST /docs/text` / `POST /projects/{id}/docs/text` – ingest ad-hoc pasted text (Docs tab).
- `POST /projects/{id}/ingestion_jobs` – queue a repo ingest (currently `kind="repo"`).
- `GET /projects/{id}/ingestion_jobs/{job_id}` – poll progress/results (files and bytes processed, timestamps, errors).
- `GET /projects/{id}/ingestion_jobs` – job history (status, duration, errors) for auditing.
- `POST /projects/{id}/ingestion_jobs/{job_id}/cancel` – request cancellation.

**Frontend (Docs tab)**:

- Text ingest form for quick notes/specs.
- Repo ingest form:
  - Input for root path + optional name prefix.
-  - Button triggers `POST /ingestion_jobs` and immediately returns to show live status.
-  - Progress panel displays status, processed files, bytes, duration, and a Cancel button for running jobs.
-  - Job history table (last 20 jobs) with status, bytes, duration, and any errors.
- Once a job completes, the Docs list auto-refreshes so newly ingested files appear immediately.

This batching infrastructure is also the foundation for future blueprint ingestion (Phase T); only repo ingestion is live today.

**CI vs dev vector store**:
- Dev/prod use a persistent Chroma store under `backend/chroma_data` (configurable via `_CHROMA_PATH` in `chroma_store.py`).
- CI/QA runs set `VECTORSTORE_MODE=stub` to use an in-memory vector store that mirrors the API surface without writing to disk; ingestion/tests stay deterministic even on read-only filesystems.

---

### 3.8 Usage & Telemetry

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

### 3.9 Right-Hand Workbench UI

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
- Usage tab includes a conversation selector, aggregate metrics (tokens/cost/calls), per-model breakdown, recent call list, and the shared routing/tasks telemetry drawer (task suggestion confidence, etc.).
- Usage tab charts cover task action types, model usage, confidence buckets, and auto-mode routes; charts, list, and JSON/CSV exports all share the same filters/time window for recent actions, with inline error/empty states and clipboard fallbacks for exports.
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

## 5. Planned: Autopilot, Blueprint Graph & Learning Layer [design-only]

> The features in this section are **designs for future versions**, captured in `docs/AUTOPILOT_PLAN.md` and related docs.  
> They are **not** present in the current codebase and should be treated as roadmap items.

### 5.1 Blueprint & Plan graph (future)

- Introduces `Blueprint` and `PlanNode` models so large specs (e.g., 500k‑word documents) can be ingested into a structured plan:
  - Phases → epics → features → stories → task specs.
- PlanNodes link back to blueprint text via anchors and offsets and forward to `Task`s via linking tables.
- Planned UI:
  - Blueprint selector and Plan tree in the Tasks tab.
  - “Generate tasks for this node” actions that create structured tasks from PlanNodes.

### 5.2 ExecutionRuns, ExecutionSteps & workers (future)

- Adds `ExecutionRun` / `ExecutionStep` models to track multi‑step automations:
  - Each run belongs to a project (and optionally a conversation/task) and has a type and status.
  - Steps log tool calls (`read_file`, `write_file`, `run_terminal`, `search_docs/messages`, etc.), inputs, outputs, and rollback data.
- Planned worker agents (code/test/docs) will:
  - Use existing Files/Terminal/Search endpoints.
  - Record all actions as ExecutionSteps.
  - Support “Revert run” by replaying rollback data.
- Planned UI:
  - A Runs panel/tab listing runs, statuses, and steps.
  - Diff viewers for code edits and alignment badges for risky operations.

### 5.3 ManagerAgent & Autonomy modes (future)

- A ManagerAgent will:
  - Select candidate tasks based on PlanNodes, dependencies, difficulty, and risk.
  - Start/advance runs subject to `Project.max_parallel_runs` and `autonomy_mode` (`"off" | "suggest" | "semi_auto" | "full_auto"`).
  - Use an intent classifier to react to messages like “start building”, “pause autopilot”, “adjust plan”.
  - Expose `/projects/{id}/autopilot_tick` as a heartbeat endpoint called by the frontend.
- Planned UI additions:
  - Autopilot dropdown (Off / Suggest / Semi / Full) and Pause/Resume toggle in the header.
  - Status pill showing whether Autopilot is idle, running, waiting for approval, or in error.
  - “Explain current plan” button that surfaces ManagerAgent’s view of phases, tasks, and runs.

### 5.4 Learning layer & plan refinement (future)

- ExecutionRuns and Tasks will accumulate learning signals:
  - `Task.difficulty_score`, `Task.rework_count`, “planned vs actual” PlanNodes.
  - `PlanNode.learned_priority`, `PlanNode.learned_risk_level`, inferred dependencies.
  - `ExecutionRun.outcome` and `learning_notes` for each run.
- ManagerAgent will periodically run retrospectives and `refine_plan`:
  - Re‑order tasks and phases.
  - Split/merge tasks.
  - Suggest blueprint pivots when new versions are uploaded.
- A `/projects/{id}/learning_metrics` endpoint will expose aggregate metrics for the UI and QA.

For full details, see:

- `docs/AUTOPILOT_PLAN.md`
- `docs/AUTOPILOT_LEARNING.md`
- `docs/AUTOPILOT_LIMITATIONS.md`
- `docs/MODEL_MATRIX.md`

---

## 6. QA, Operations, and Evolution

### 6.1 QA Artifacts

- **Test plan**: `docs/TEST_PLAN.md` – detailed manual+automated test cases.
- **Test reports**: `docs/TEST_REPORT_*.md` – records of actual runs (e.g., `2025-12-02`).
- **Smoke tests**: `qa/run_smoke.py` runs:
  - Message search probe.
  - Task auto‑loop probe.
  - Mode routing probe.
- **UI tests**: Playwright specs in `frontend/tests/`.

### 6.2 Operations

- **Day‑to‑day running**:
  - Backend: `uvicorn app.api.main:app --reload`.
  - Frontend: `npm run dev`.
- **QA environment**:
  - Copy of the repo in `C:\InfinityWindow_QA`.
  - `Makefile` with `ci` target to run backend tests and frontend build.
- **Resets**:
  - `tools/reset_qa_env.py` safely backs up and deletes DB + Chroma in QA (only when uvicorn is not running).

Details live in `docs/OPERATIONS_RUNBOOK.md`.

### 6.3 Roadmap & Future Work

Planned and partially implemented features are tracked in:

- `docs/PROGRESS.md` – by window and version (v3/v4+).
- `docs/TODO_CHECKLIST.md` – checkbox view of outstanding work.

These documents are the canonical place to see what is **planned** vs. what is implemented today. Autopilot/Blueprint/Learning work is tracked there under future phases until it ships.

---

InfinityWindow is evolving, but the features and behaviors described in sections 1–4 reflect the current, working system. Autopilot and related plans in section 5 are **designs**; consult the code referenced in `docs/SYSTEM_MATRIX.md` and the QA artifacts for what is actually implemented today.

