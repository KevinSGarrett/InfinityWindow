# InfinityWindow API Reference (High Level)

This document lists the **most important HTTP endpoints** exposed by the FastAPI backend.  
It is not an exhaustive OpenAPI spec, but a practical reference for development and QA.

> Base URL (dev): `http://127.0.0.1:8000`

---

## 1. Projects & conversations

> Note: A more current, detailed guide is available at `docs/API_REFERENCE_UPDATED.md`. Use that for the latest endpoints and payload examples; this file remains as the legacy quick reference. Base dev URL: `http://127.0.0.1:8000`.

### 1.1 Projects

- **GET `/projects`**  
  List all projects.

- **POST `/projects`**  
  Create a project. Typical body:

  ```json
  {
    "name": "My Project",
    "local_root_path": "C:\\Path\\To\\Repo",
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

- **GET `/projects/{project_id}/tasks/overview`**  
  Returns both tasks and pending task suggestions (low-confidence add/complete) in one call.

- **POST `/projects/{project_id}/tasks`**  
  Create a new task.

- **PATCH `/tasks/{task_id}`**  
  Update a task (e.g., change `status` or `description`).

- **DELETE `/tasks/{task_id}`**  
  Delete a task (helpful for cleaning artifacts).

- **POST `/projects/{project_id}/auto_update_tasks`**  
  Trigger autonomous task maintenance based on recent conversation history. (Scoped route; body need not include `project_id`.)

- **GET `/projects/{project_id}/tasks/overview`**  
  Returns both tasks and pending low-confidence suggestions (add/complete) in one call.

---

## 3. Docs, notes, decisions, memory

### 3.1 Docs

- **GET `/projects/{project_id}/docs`**  
- **POST `/projects/{project_id}/docs`** (metadata only: `title`, `description`)  
- **POST `/projects/{project_id}/docs/text`** (text ingest: `name`, `text`, optional `description`)  
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
- **PATCH `/memory_items/{memory_id}` / DELETE**  

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

- **POST `/search/docs`**
- **POST `/search/memory`** (returns `memory_id`, `title`, `content`, `distance`)

---

## 5. Filesystem

- **GET `/projects/{project_id}/fs/list`**

  List files and directories under the project’s `local_root_path`. Query parameters typically include:
  - `subpath` – path relative to project root.

- **GET `/projects/{project_id}/fs/read`**

  Read file content from under the project root. Query parameters:
  - `file_path` (preferred) or `subpath` – file path relative to project root.

- **PUT `/projects/{project_id}/fs/write`**

  Write updated file content back to disk under the project root.

- **POST `/projects/{project_id}/fs/ai_edit`**

  Accepts AI‑proposed edits or manual file updates, returns a diff/preview, and (when requested) applies them under the project root. Accepts `instruction` (alias: `instructions`).

---

## 6. Ingestion jobs

Large repo/document ingests are kicked off via ingestion jobs so the UI can show progress and the backend can batch embeddings safely. The POST endpoint queues the job and returns immediately; poll the status endpoints for progress and, if needed, request cancellation.

- **POST `/projects/{project_id}/ingestion_jobs`**

  Body:

  ```json
  {
    "kind": "repo",
    "source": "C:\\InfinityWindow",
    "name_prefix": "InfinityWindow/",
    "include_globs": ["*.py", "*.md"]
  }
  ```

  - `kind` currently supports `"repo"`.
  - `source` must be a local path reachable by the backend.
  - Optional `name_prefix`/`include_globs` customize document names and filters.
  - Returns the created job (`status` will be `pending` and transitions to `running` once the background worker picks it up).

- **GET `/projects/{project_id}/ingestion_jobs/{job_id}`**

  - Returns job status (`pending` | `running` | `completed` | `failed` | `cancelled`), `total_items`, `processed_items`, `total_bytes`, `processed_bytes`, optional `error_message`, timestamps, and any metadata recorded during the run.
  - Poll this endpoint every ~2s to drive the Docs tab progress indicator.

- **GET `/projects/{project_id}/ingestion_jobs?limit=20`**

  - Lists the most recent ingestion jobs (default limit 20) so the UI can show job history / audit trails.

- **POST `/projects/{project_id}/ingestion_jobs/{job_id}/cancel`**

  - Request cancellation for a running job. The job stops after finishing the current file and returns status `cancelled`.

Job metadata is stored in the `ingestion_jobs` table; per-file digests live in `file_ingestion_state` so subsequent ingests skip unchanged files.

---

## 7. Terminal

- **POST `/projects/{project_id}/terminal/run`**

  Run a shell command in a controlled context. Body includes:

  ```json
  {
    "command": "pytest -q",
    "cwd": "backend"
  }
  ```

  Returns stdout/stderr and exit code. On the scoped path, `project_id` comes from the URL (not required in the body).

- **GET `/projects/{project_id}/terminal/history`**

  Retrieve recent manual commands and their results.

---

## 8. Usage & telemetry

- **GET `/conversations/{conversation_id}/usage`**  
  Returns usage/cost summaries for a conversation (used by the Usage tab).

- **GET `/debug/telemetry`**

  Returns telemetry for:
  - LLM model routing (auto mode routes, fallback counts).
  - Task automation (auto‑added, auto‑completed, auto‑deduped).

Used by QA to verify that heuristics are behaving as expected.

- **GET `/debug/docs_status`**

  Diagnostics guardrail for canonical docs. Returns:

  ```json
  {
    "docs": [
      {"path": "docs/REQUIREMENTS_CRM.md", "exists": true, "size_bytes": 1234}
    ],
    "missing": []
  }
  ```

  `docs` enumerates `CANONICAL_DOC_PATHS` from `backend/app/api/main.py` (path, exists, size_bytes). `missing` lists any docs that are absent or empty. QA/CI keep this green via `qa/tests_docs/test_docs_existence.py` and `qa/tests_api/test_docs_status.py`.

---

## 9. Health & misc

- **GET `/health`**

  Basic health check endpoint used by scripts and operators.

---

## 10. Notes for implementers

- For exact request/response schemas, consult:
  - Pydantic models in `backend/app/api/main.py` and related modules.
  - SQLAlchemy models in `backend/app/db/models.py`.
- When you add or change endpoints:
  - Update this file.
  - Update `docs/SYSTEM_MATRIX.md` (feature ↔ endpoint mapping).
  - Add or adjust QA coverage in `docs/TEST_PLAN.md` and/or `qa/` probes.

---

## 11. Planned Autopilot & Blueprint APIs [design-only]

> The endpoints in this section are **not yet implemented**.  
> They are documented here so future Autopilot/Blueprint work can align with the rest of the API surface.

### 10.1 Blueprint & Plan

- **POST `/projects/{project_id}/blueprints`**  
  Create a `Blueprint` for a given `Document` and project.

- **GET `/projects/{project_id}/blueprints`**  
  List blueprints for a project.

- **GET `/blueprints/{blueprint_id}`**  
  Return blueprint metadata plus a nested PlanNode tree.

- **PATCH `/blueprints/{blueprint_id}`**  
  Update title/description/status or mark a blueprint as active.

- **POST `/blueprints/{blueprint_id}/generate_plan`**  
  Run the outline/PlanNode generation pipeline for a large blueprint document.

- **PATCH `/plan_nodes/{id}`**  
  Edit PlanNode fields (title, summary, status, priority, risk, order, etc.).

- **POST `/plan_nodes/{plan_node_id}/generate_tasks`**  
  Generate tasks for a specific PlanNode (feature/story level).

- **POST `/blueprints/{blueprint_id}/generate_all_tasks`**  
  (Optional) Generate tasks for all feature/story PlanNodes in a blueprint.

### 10.2 Runs & Autopilot

- **POST `/projects/{project_id}/runs`**  
  Create an `ExecutionRun` linked to a project (and optional task/conversation).

- **GET `/projects/{project_id}/runs`**  
  List runs for a project, optionally filtered by status.

- **GET `/runs/{run_id}`**  
  Fetch a run and its ordered `ExecutionStep`s.

- **POST `/runs/{run_id}/advance`**  
  Approve/skip/abort the next pending step in a run.

- **POST `/runs/{run_id}/rollback`**  
  Restore all files touched by a run using stored rollback data.

- **POST `/projects/{project_id}/autopilot_tick`**  
  ManagerAgent heartbeat: advance existing runs or start new ones, respecting project autonomy settings.

- **GET `/projects/{project_id}/manager/plan`**  
  Return the Manager’s view of the plan (active phase, next tasks, active runs, rationale).

- **POST `/projects/{project_id}/refine_plan`**  
  Ask the Manager to run a retrospective and refine the plan based on learning signals.

### 10.3 Learning & Metrics

- **POST `/projects/{project_id}/snapshot/refresh`**  
  Build or update a `ProjectSnapshot` for a project.

- **GET `/projects/{project_id}/snapshot`**  
  Fetch snapshot text and key metrics JSON.

- **GET `/projects/{project_id}/learning_metrics`**  
  Return aggregate learning metrics (average cycle time, difficulty, fragile areas, plan deviation rate, blocked tasks count).

