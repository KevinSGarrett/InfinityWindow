# InfinityWindow API Reference (High Level)

This document lists the **most important HTTP endpoints** exposed by the FastAPI backend.  
It is not an exhaustive OpenAPI spec, but a practical reference for development and QA.

> Base URL (dev): `http://127.0.0.1:8000`

---

## 1. Projects & conversations

### 1.1 Projects

- **GET `/projects`**  
  List all projects.

- **POST `/projects`**  
  Create a project. Typical body:

  ```json
  {
    "name": "My Project",
    "root_path": "C:\\Path\\To\\Repo",
    "description": "Optional description"
  }
  ```

- **GET `/projects/{project_id}`**  
  Get project details.

### 1.2 Conversations & messages

- **GET `/projects/{project_id}/conversations`**  
  List conversations for a project.

- **POST `/projects/{project_id}/conversations`**  
  Create a conversation (e.g., “Architecture”, “Bugs”).

- **GET `/conversations/{conversation_id}/messages`**  
  List messages in a conversation.

- **POST `/chat`** (or equivalent chat endpoint)  
  Append a new user message and generate an assistant reply. Body typically includes:

  ```json
  {
    "project_id": 1,
    "conversation_id": 42,
    "mode": "auto",
    "message": "User content here"
  }
  ```

---

## 2. Tasks / TODOs

- **GET `/projects/{project_id}/tasks`**  
  List tasks for a project, sorted by status (`open` first) and recency.

- **POST `/projects/{project_id}/tasks`**  
  Create a new task.

- **PATCH `/tasks/{task_id}`**  
  Update a task (e.g., change `status` or `description`).

- **POST `/projects/{project_id}/auto_update_tasks`** *(name may vary)*  
  Trigger autonomous task maintenance based on recent conversation history.

---

## 3. Docs, notes, decisions, memory

### 3.1 Docs

- **GET `/projects/{project_id}/docs`**  
- **POST `/projects/{project_id}/docs`**  
- **GET `/docs/{doc_id}` / PATCH / DELETE**  

Used by the Docs tab to manage project documents.

### 3.2 Project instructions & decision log

- **GET `/projects/{project_id}/instructions`**  
- **PUT `/projects/{project_id}/instructions`**  

Manage per‑project instructions.

- **GET `/projects/{project_id}/decisions`**  
- **POST `/projects/{project_id}/decisions`**  
- **PATCH `/decisions/{decision_id}` / DELETE**  

Decision log items visible in the Notes tab.

### 3.3 Memory

- **GET `/projects/{project_id}/memory`**  
- **POST `/projects/{project_id}/memory`**  
- **PATCH `/memory/{memory_id}` / DELETE**  

Manage long‑term memory items for a project.

---

## 4. Search

### 4.1 Message search

- **POST `/search/messages`**

  Body (simplified example):

  ```json
  {
    "project_id": 1,
    "query": "search terms",
    "limit": 20
  }
  ```

  Returns top‑K matching messages from the vector store.

### 4.2 Docs & memory search

If implemented, similar shapes:

- **POST `/search/docs`**
- **POST `/search/memory`**

---

## 5. Filesystem

- **GET `/projects/{project_id}/files`**

  Query parameters typically include:
  - `path` – path relative to project root.

  Returns directory tree listing for the Files tab.

- **GET `/projects/{project_id}/files/content`**

  Query parameters:
  - `path` – file path relative to project root.

  Returns file content for editing.

- **POST `/projects/{project_id}/files/apply_edit`**

  Accepts AI‑proposed edits or manual file updates, applies them to disk under the project root.

---

## 6. Terminal

- **POST `/projects/{project_id}/terminal/run`**

  Run a shell command in a controlled context. Body includes:

  ```json
  {
    "command": "pytest -q",
    "cwd": "backend"
  }
  ```

  Returns stdout/stderr and exit code.

- **GET `/projects/{project_id}/terminal/history`**

  Retrieve recent manual commands and their results.

---

## 7. Usage & telemetry

- **GET `/projects/{project_id}/usage`** *(name may vary)*  
  Returns usage/cost summaries for a project (used by Usage tab).

- **GET `/debug/telemetry`**

  Returns telemetry for:
  - LLM model routing (auto mode routes, fallback counts).
  - Task automation (auto‑added, auto‑completed, auto‑deduped).

Used by QA to verify that heuristics are behaving as expected.

---

## 8. Health & misc

- **GET `/health`**

  Basic health check endpoint used by scripts and operators.

---

## 9. Notes for implementers

- For exact request/response schemas, consult:
  - Pydantic models in `backend/app/api/main.py` and related modules.
  - SQLAlchemy models in `backend/app/db/models.py`.
- When you add or change endpoints:
  - Update this file.
  - Update `docs/SYSTEM_MATRIX.md` (feature ↔ endpoint mapping).
  - Add or adjust QA coverage in `docs/TEST_PLAN.md` and/or `qa/` probes.


