# InfinityWindow System Matrix

This document is a **catalogue of where everything lives and what it does**.  
Use it when you need to answer questions like:

- “Where is the code for \<feature\>?”  
- “Which endpoint backs this UI?”  
- “What data model does this feature use?”  
- “Which tests cover this behavior?”

---

## 1. Feature → Backend → Frontend → Data → Tests

### 1.1 Projects, conversations, messages

| Area            | Element                                                                 | Notes |
|----------------|-------------------------------------------------------------------------|-------|
| **Backend**    | `app/api/main.py` – project & conversation routes                      | Project CRUD, conversation CRUD, message posting, search. |
|                | `app/db/models.py` – `Project`, `Conversation`, `Message`              | Core entities; `Conversation` links messages to projects and folders. |
|                | `app/vectorstore/chroma_store.py`                                      | Message embeddings collection and helpers. |
| **Frontend**   | `frontend/src/App.tsx`                                                 | Project selector, conversation list, chat panel. |
|                | (other `frontend/src/*` components as the app is decomposed)           | UI is currently centralized in `App.tsx`. |
| **Data**       | SQLite DB (`backend/infinitywindow.db`)                                | Tables for projects, conversations, messages, tasks, docs, memory, usage, etc. |
|                | Chroma store (`backend/chroma_data/`)                                  | Vector index for messages/docs/memory search. |
| **API**        | `POST /projects` / `GET /projects` / `GET /projects/{id}`              | Project lifecycle. |
|                | `POST /projects/{id}/conversations`                                    | Create conversation. |
|                | `POST /chat` (or equivalent chat endpoint)                             | Append message + generate reply via LLM. |
|                | `POST /search/messages`                                                | Vector search over messages with filters. |
| **Tests / QA** | `qa/message_search_probe.py`                                           | Seeds a conversation and asserts search results. |
|                | `qa/run_smoke.py`                                                      | Runs message search probe along with other smoke tests. |
|                | `docs/TEST_PLAN.md` – C‑MsgSearch‑01                                   | Manual test case for message search. |

---

### 1.2 Tasks / TODOs (project tasks)

| Area            | Element                                                                 | Notes |
|----------------|-------------------------------------------------------------------------|-------|
| **Backend**    | `app/api/main.py` – task endpoints                                     | `list_project_tasks`, create/update tasks, `auto_update_tasks_from_conversation`. |
|                | `app/db/models.py` – `Task`                                            | Fields: `id`, `project_id`, `description`, `status`, timestamps. |
| **Frontend**   | `frontend/src/App.tsx` – Tasks tab                                     | Renders task list, statuses, controls for add/update. |
| **API**        | `GET /projects/{project_id}/tasks`                                     | Returns tasks sorted by status + recency. |
|                | `GET /projects/{project_id}/tasks/overview`                            | Returns tasks + pending suggestions. |
|                | `POST /projects/{project_id}/tasks`                                    | Create task. |
|                | `PATCH /tasks/{task_id}`                                               | Update status/description/priority/blocked_reason. |
|                | `DELETE /tasks/{task_id}`                                              | Delete task. |
|                | `POST /projects/{project_id}/auto_update_tasks`                        | Auto‑maintenance based on conversations (also runs post‑chat when enabled). |
| **Automation** | `auto_update_tasks_from_conversation` in `app/api/main.py`            | Auto‑adds tasks, dedupes, marks tasks done based on completion phrases. |
| **Telemetry**  | `TASK_TELEMETRY_COUNTERS` in `app/api/main.py`                         | Counts auto‑added/auto‑completed/auto‑deduped tasks. |
| **Tests / QA** | `qa/tasks_autoloop_probe.py`                                           | Verifies auto‑add and auto‑complete behavior in a clean project. |
|                | `docs/TEST_PLAN.md` – B‑Tasks‑02                                       | Manual test for autonomous TODO maintenance loop. |

---

### 1.3 Docs / project documents

| Area            | Element                                                                 | Notes |
|----------------|-------------------------------------------------------------------------|-------|
| **Backend**    | `app/api/main.py` – document endpoints                                 | CRUD for project documents and their content. |
|                | `app/db/models.py` – `Document`                                        | Stores project‑scoped docs (title, content, metadata). |
|                | `app/vectorstore/chroma_store.py` – docs collection                    | Embeddings and search for project docs. |
| **Frontend**   | `frontend/src/App.tsx` – Docs tab                                      | Lists project docs, detail view, editing. |
| **API**        | `GET /projects/{project_id}/docs`                                      | Fetch docs for a project. |
|                | `POST /projects/{project_id}/docs`                                     | Create doc. |
|                | `PATCH /docs/{doc_id}` / `DELETE /docs/{doc_id}`                       | Update/delete. |
|                | `POST /search/docs` (if implemented)                                   | Vector search over docs. |
| **Tests / QA** | `docs/TEST_PLAN.md` – D‑Docs‑0x                                        | Manual verification of docs creation/search. |

---

### 1.4 Memory items

| Area            | Element                                                                 | Notes |
|----------------|-------------------------------------------------------------------------|-------|
| **Backend**    | `app/api/main.py` – memory endpoints                                   | CRUD for long‑term memory items per project. |
|                | `app/db/models.py` – `MemoryItem`                                      | Stores title, content, tags, project link. |
|                | `app/vectorstore/chroma_store.py` – memory collection                  | Embeddings and search for memory items. |
| **Frontend**   | `frontend/src/App.tsx` – Memory tab                                    | Displays and manages memory items. |
| **API**        | `GET /projects/{project_id}/memory`                                    | List memory items. |
|                | `POST /projects/{project_id}/memory`                                   | Create memory item. |
|                | `DELETE /memory/{memory_id}` / `PATCH /memory/{memory_id}`             | Manage items. |
| **Tests / QA** | `frontend/tests/notes-memory.spec.ts`                                  | Seeds memory items via API and asserts UI rendering. |
|                | `docs/TEST_PLAN.md` – F‑Memory‑0x                                      | Manual memory tests. |

---

### 1.5 Notes, instructions, decision log

| Area            | Element                                                                 | Notes |
|----------------|-------------------------------------------------------------------------|-------|
| **Backend**    | `app/api/main.py` – instructions & decision endpoints                  | Project instructions, decisions (title, body, tags). |
|                | `app/db/models.py` – `Decision` / instructions fields                  | Store per‑project guidance and decisions. |
| **Frontend**   | `frontend/src/App.tsx` – Notes tab                                     | Shows project instructions + decision log. |
| **API**        | `GET /projects/{project_id}/instructions`                              | Read instructions. |
|                | `PUT /projects/{project_id}/instructions`                              | Update instructions. |
|                | `GET /projects/{project_id}/decisions` / `POST /projects/{project_id}/decisions` | Manage decisions. |
| **Tests / QA** | `frontend/tests/notes-memory.spec.ts`                                  | Verifies instructions + decision log in UI. |
|                | `docs/TEST_PLAN.md` – E‑Notes‑0x / G‑Dec‑0x                            | Manual notes/decision tests and automation. |

---

### 1.6 Filesystem integration

| Area            | Element                                                                 | Notes |
|----------------|-------------------------------------------------------------------------|-------|
| **Backend**    | `app/api/main.py` – filesystem routes                                  | List directory tree, open file, save file, AI edit proposals. |
| **Frontend**   | `frontend/src/App.tsx` – Files tab                                     | Tree view, file editor panel, AI edit diff UI. |
| **API**        | `GET /projects/{project_id}/fs/list`                                   | List files from project root. |
|                | `GET /projects/{project_id}/fs/read`                                   | Load file content (`file_path` or `subpath`). |
|                | `PUT /projects/{project_id}/fs/write`                                  | Write file content (optional create dirs). |
|                | `POST /projects/{project_id}/fs/ai_edit`                               | AI edit proposal (`instruction` or `instructions` alias). |
| **Tests / QA** | `frontend/tests/files-tab.spec.ts`                                     | Navigates tree, opens file, toggles “Show original”, verifies unsaved state. |
|                | `docs/TEST_PLAN.md` – F‑Files‑0x                                       | Files & AI edit tests. |

---

### 1.7 Terminal integration

| Area            | Element                                                                 | Notes |
|----------------|-------------------------------------------------------------------------|-------|
| **Backend**    | `app/api/main.py` – terminal routes                                    | Execute commands in a controlled shell, stream output. |
| **Frontend**   | `frontend/src/App.tsx` – Terminal tab                                  | Input box + output pane; can show AI‑proposed commands. |
| **API**        | `POST /projects/{project_id}/terminal/run`                             | Run command (scoped path injects `project_id`; body `project_id` optional). |
|                | `GET /projects/{project_id}/terminal/history`                          | Past manual commands (stub/placeholder). |
| **Tests / QA** | `docs/TEST_PLAN.md` – G‑Term‑0x                                        | Manual terminal tests. |

---

### 1.8 Search (messages, docs, memory)

| Area            | Element                                                                 | Notes |
|----------------|-------------------------------------------------------------------------|-------|
| **Backend**    | `app/vectorstore/chroma_store.py`                                      | Collections + add/query helpers. |
|                | `app/api/main.py` – search endpoints                                   | HTTP layer for text + filters. |
| **Frontend**   | `frontend/src/App.tsx` – Search tab                                    | Unified search UI (messages/docs/memory) with conversation/folder/document filters, grouped results, and “open in” actions. |
| **API**        | `POST /search/messages` / `POST /search/docs` / `POST /search/memory`  | Vector search entrypoints (memory search returns `memory_id`, `title`, `content`, `distance`). |
| **Tests / QA** | `qa/message_search_probe.py`                                           | Regression guard for message search. |
|                | `docs/TEST_PLAN.md` – C‑MsgSearch‑01                                   | Manual search test. |

---

### 1.9 Model routing & chat modes

| Area            | Element                                                                 | Notes |
|----------------|-------------------------------------------------------------------------|-------|
| **Backend**    | `app/llm/openai_client.py`                                              | `_DEFAULT_MODELS`, `_infer_auto_submode`, `generate_reply_from_history`. |
|                | `app/api/main.py` – chat endpoint                                      | Forwards `mode` and `model` parameters. |
| **Frontend**   | `frontend/src/App.tsx` – mode selector                                 | Dropdown for `auto`, `fast`, `deep`, `budget`, `research`, `code`. |
| **API**        | `POST /chat` (or equivalent) with `{ "mode": "auto" | "fast" | ... }`  | Mode selection. |
| **Telemetry**  | `_LLM_TELEMETRY_COUNTERS` in `openai_client.py`                        | Counts auto‑routes, fallback attempts, successes. |
| **Debug API**  | `GET /debug/telemetry` in `app/api/main.py`                            | Exposes routing + task telemetry. |
| **Tests / QA** | `qa/mode_routing_probe.py`                                             | Patches `_call_model` and asserts routed model choices per scenario. |
|                | `docs/TEST_PLAN.md` – B‑Mode‑01/02                                     | Manual mode & auto‑routing tests. |

---

### 1.10 UI layout / right‑hand workbench

| Area            | Element                                                                 | Notes |
|----------------|-------------------------------------------------------------------------|-------|
| **Frontend**   | `frontend/src/App.tsx`                                                 | All right‑tab panels (Tasks, Docs, Files, Search, Terminal, Usage, Notes, Memory). |
|                | `frontend/src/App.css`                                                 | Layout for 3‑column view, right‑tabs toolbar, panel content. |
| **Docs**       | `docs/RIGHT_COLUMN_UI_PLAN.md`                                         | Design intentions and future improvements. |
| **Tests / QA** | `frontend/tests/right-column.spec.ts`                                  | Ensures each tab button activates correctly (has `active` class). |

### 1.11 Notes & decisions

| Area          | Element                                                                 | Notes |
|---------------|-------------------------------------------------------------------------|-------|
| **Backend**   | `app/api/main.py` – instructions & decision endpoints                  | Supports pinned notes, decision status/tags, follow-up task links, draft flags. |
| **Frontend**  | `frontend/src/App.tsx` – Notes tab                                     | Pinned note editor, instructions diff, decision filters, follow-up task/memory buttons, draft banners. |
| **Automation**| `auto_capture_decisions_from_conversation` (in `app/api/main.py`)       | Detects “Decision…” phrases in chat and creates draft decisions automatically. |

### 1.12 Repo & document ingestion

| Area            | Element                                                                 | Notes |
|----------------|-------------------------------------------------------------------------|-------|
| **Backend**    | `app/ingestion/docs_ingestor.py`                                        | Chunks text docs and writes chunks/embeddings. |
|                | `app/ingestion/github_ingestor.py`                                      | Walks local repos, hashes files, tracks progress/cancel requests. |
|                | `app/llm/embeddings.py` – `embed_texts_batched`                         | Enforces `MAX_EMBED_TOKENS_PER_BATCH` / `MAX_EMBED_ITEMS_PER_BATCH`. |
|                | `app/api/main.py` – `/docs/text`, `/projects/{id}/ingestion_jobs*`     | Queues jobs, exposes status/history/cancel endpoints, surfaces telemetry. |
| **Frontend**   | `frontend/src/App.tsx` – Docs tab                                      | Text ingest form + repo ingest form with live status, cancel button, and history table. |
| **Data**       | `documents`, `document_chunks`, `ingestion_jobs`, `file_ingestion_state` | Job records + per-file digests to skip unchanged files. |
| **API**        | `POST /docs/text` / `POST /projects/{id}/ingestion_jobs` / `GET /projects/{id}/ingestion_jobs` / `POST /projects/{id}/ingestion_jobs/{job_id}/cancel` | Kick off, monitor, list, and cancel ingests. |
| **Tests / QA** | `qa/ingestion_probe.py` (happy path + forced failure), `docs/TEST_PLAN.md` – D-Ingest-01 (manual) | Automated probe covers batching/skipping/cancel errors; manual plan double-checks UI flows. |

---

## 2. Data models → Tables → Usage

| Model        | Table / Storage             | Used by                                      |
|-------------|-----------------------------|----------------------------------------------|
| `Project`   | `projects` table            | Projects dropdown, scoping for all features. |
| `Conversation` | `conversations`          | Chat threads per project.                    |
| `Message`   | `messages`                  | Stored chat messages + embeddings.           |
| `Task`      | `tasks`                     | Tasks tab, auto‑maintenance loop.            |
| `Document`  | `documents`                 | Docs tab, retrieval.                         |
| `MemoryItem`| `memory_items`              | Memory tab, retrieval.                       |
| `Decision`  | `decisions`                 | Decision log in Notes tab.                   |
| `UsageRecord` (or similar) | `usage`      | Usage tab, cost tracking.                    |
| `IngestionJob` | `ingestion_jobs`         | Tracks repo ingestion progress/status/error for Docs tab. |
| `FileIngestionState` | `file_ingestion_state` | Stores per-project path hashes to skip unchanged files. |

Vector store collections are stored under `backend/chroma_data/` and are accessed via helper functions in `chroma_store.py`.

---

## 3. Testing matrix (where to look)

| Area                 | Automated / Scripted                         | Manual / Docs                              |
|----------------------|----------------------------------------------|--------------------------------------------|
| Backend regressions  | `qa/run_smoke.py` and individual probes      | `docs/TEST_PLAN.md` (Phase A/B/C…)         |
| UI regressions       | `frontend/tests/*.spec.ts` (Playwright)      | `docs/TEST_PLAN.md` (UI sections)          |
| CI                   | `Makefile` (in QA copy) – `make ci`          | `docs/PROGRESS.md` – CI run log            |
| QA history           | N/A                                          | `docs/TEST_REPORT_*.md`                    |

Use this matrix together with `SYSTEM_OVERVIEW.md` when you need to trace a feature end‑to‑end or decide where to make a change safely.

---

## 4. Planned: Autopilot & Blueprint Data Models [design-only]

> These models/tables are **not yet present** in `backend/app/db/models.py`.  
> They are planned for future Autopilot/Blueprint work (see `AUTOPILOT_PLAN.md`).

| Planned Model         | Purpose                                      | Notes |
|-----------------------|----------------------------------------------|-------|
| `Blueprint`           | Links a project to a large spec document     | Tracks versioning and references a `Document` containing the raw blueprint text. |
| `PlanNode`            | Nodes in the Blueprint plan tree             | Represents phases/epics/features/stories/task_specs; stores doc anchors, offsets, status, priority, risk. |
| `PlanNodeTaskLink`    | Many‑to‑many link between PlanNodes and tasks | Allows a PlanNode to have multiple Tasks and vice versa. |
| `TaskDependency`      | Declares task‑to‑task dependencies           | Used by ManagerAgent to ensure prerequisites are complete. |
| `BlueprintIngestionJob` | Tracks long‑running blueprint ingestion   | Status/progress/error metadata for large document ingestion. |
| `ConversationSummary` | Rolling summary per conversation             | Short/detailed summaries used by the context builder. |
| `ProjectSnapshot`     | Snapshot doc & key metrics per project       | Backing for “project status” views in Notes/Usage tabs. |
| `ExecutionRun`        | One multi‑step automation                    | Links to `Project` (+ optional `Task`/`Conversation`), stores type/status/error/touched files. |
| `ExecutionStep`       | Atomic step in a run                         | Records tool, input/output payloads, alignment info, rollback data, status. |
| `BlueprintSectionSummary` | Per‑PlanNode summaries                  | Short/detailed summaries of blueprint sections to keep context small. |

---

## 5. Planned: Autopilot & Blueprint Endpoints [design-only]

> These endpoints are **not yet implemented** in `app/api/main.py`.  
> They are listed here so future work can wire them consistently with the rest of the system.

### 5.1 Blueprint & Plan

| Endpoint                                   | Purpose                                        |
|--------------------------------------------|------------------------------------------------|
| `POST /projects/{project_id}/blueprints`   | Create a blueprint for a given doc + project. |
| `GET /projects/{project_id}/blueprints`    | List blueprints for a project.                |
| `GET /blueprints/{blueprint_id}`           | Get blueprint details + PlanNode tree.        |
| `PATCH /blueprints/{blueprint_id}`         | Update blueprint metadata or active status.   |
| `POST /blueprints/{blueprint_id}/generate_plan` | Run ingestion pipeline, build PlanNodes. |
| `PATCH /plan_nodes/{id}`                   | Edit PlanNode fields (title, summary, status, etc.). |
| `POST /plan_nodes/{plan_node_id}/generate_tasks` | Generate tasks from a specific PlanNode. |
| `POST /blueprints/{blueprint_id}/generate_all_tasks` | Bulk generate tasks for all feature/story PlanNodes. |

### 5.2 Runs & Autopilot

| Endpoint                                   | Purpose                                        |
|--------------------------------------------|------------------------------------------------|
| `POST /projects/{project_id}/runs`         | Create a new `ExecutionRun` for a task/conversation. |
| `GET /projects/{project_id}/runs`          | List runs for a project (optionally filter by status). |
| `GET /runs/{run_id}`                       | Fetch run details + ordered steps.            |
| `POST /runs/{run_id}/advance`              | Approve/skip/abort the next pending step.     |
| `POST /runs/{run_id}/rollback`             | Restore all files touched by a run.           |
| `POST /projects/{project_id}/autopilot_tick` | Manager heartbeat: start/advance runs while respecting autonomy. |
| `GET /projects/{project_id}/manager/plan`  | Explain current plan (active phase, next tasks, active runs). |
| `POST /projects/{project_id}/refine_plan`  | Ask ManagerAgent to refine plan based on learning signals. |

### 5.3 Learning & Metrics

| Endpoint                                      | Purpose                                        |
|-----------------------------------------------|------------------------------------------------|
| `POST /projects/{project_id}/snapshot/refresh` | Refresh `ProjectSnapshot` for a project.      |
| `GET /projects/{project_id}/snapshot`         | Fetch snapshot text + key metrics JSON.       |
| `GET /projects/{project_id}/learning_metrics` | Aggregate learning metrics for UI/QA.         |

### 5.4 Ingestion Jobs & Batching

| Endpoint                                             | Purpose                                        |
|------------------------------------------------------|------------------------------------------------|
| `POST /projects/{project_id}/ingestion_jobs`         | Create an ingestion job (repo/docs/blueprint). |
| `GET /projects/{project_id}/ingestion_jobs/{job_id}` | Check job progress and status.                 |

---

## 6. Testing matrix (where to look)

| Area                 | Automated / Scripted                         | Manual / Docs                              |
|----------------------|----------------------------------------------|--------------------------------------------|
| Backend regressions  | `qa/run_smoke.py` and individual probes      | `docs/TEST_PLAN.md` (Phase A/B/C/…)        |
| UI regressions       | `frontend/tests/*.spec.ts` (Playwright)      | `docs/TEST_PLAN.md` (UI sections)          |
| CI                   | `Makefile` (in QA copy) – `make ci`          | `docs/PROGRESS.md` – CI run log            |
| QA history           | N/A                                          | `docs/TEST_REPORT_*.md`                    |

Use this matrix together with `SYSTEM_OVERVIEW.md` when you need to trace a feature end‑to‑end or decide where to make a change safely. For Autopilot/Blueprint work, also consult `AUTOPILOT_PLAN.md`, `AUTOPILOT_LEARNING.md`, `AUTOPILOT_LIMITATIONS.md`, and `MODEL_MATRIX.md`.