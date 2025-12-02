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
|                | `POST /projects/{project_id}/tasks`                                    | Create task. |
|                | `PATCH /tasks/{task_id}` (or similar)                                  | Update status/description. |
|                | `POST /projects/{project_id}/auto_update_tasks` (internal / helper)    | Auto‑maintenance based on conversations. |
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
|                | `docs/TEST_PLAN.md` – E‑Notes‑0x                                       | Manual notes/decision tests. |

---

### 1.6 Filesystem integration

| Area            | Element                                                                 | Notes |
|----------------|-------------------------------------------------------------------------|-------|
| **Backend**    | `app/api/main.py` – filesystem routes                                  | List directory tree, open file, save file, AI edit proposals. |
| **Frontend**   | `frontend/src/App.tsx` – Files tab                                     | Tree view, file editor panel, AI edit diff UI. |
| **API**        | `GET /projects/{project_id}/files`                                     | List files from project root. |
|                | `GET /projects/{project_id}/files/content`                             | Load file content. |
|                | `POST /projects/{project_id}/files/apply_edit`                         | Apply AI‑proposed edits. |
| **Tests / QA** | `frontend/tests/files-tab.spec.ts`                                     | Navigates tree, opens file, toggles “Show original”, verifies unsaved state. |
|                | `docs/TEST_PLAN.md` – F‑Files‑0x                                       | Files & AI edit tests. |

---

### 1.7 Terminal integration

| Area            | Element                                                                 | Notes |
|----------------|-------------------------------------------------------------------------|-------|
| **Backend**    | `app/api/main.py` – terminal routes                                    | Execute commands in a controlled shell, stream output. |
| **Frontend**   | `frontend/src/App.tsx` – Terminal tab                                  | Input box + output pane; can show AI‑proposed commands. |
| **API**        | `POST /projects/{project_id}/terminal/run`                             | Run command. |
|                | `GET /projects/{project_id}/terminal/history`                          | Past manual commands. |
| **Tests / QA** | `docs/TEST_PLAN.md` – G‑Term‑0x                                        | Manual terminal tests. |

---

### 1.8 Search (messages, docs, memory)

| Area            | Element                                                                 | Notes |
|----------------|-------------------------------------------------------------------------|-------|
| **Backend**    | `app/vectorstore/chroma_store.py`                                      | Collections + add/query helpers. |
|                | `app/api/main.py` – search endpoints                                   | HTTP layer for text + filters. |
| **Frontend**   | `frontend/src/App.tsx` – Search tab                                    | Unified search UI (messages/docs/memory) with conversation/folder/document filters, grouped results, and “open in” actions. |
| **API**        | `POST /search/messages` / `POST /search/docs` / `POST /search/memory`  | Vector search entrypoints. |
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


