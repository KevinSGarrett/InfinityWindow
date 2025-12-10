# InfinityWindow API Reference (Updated)

This version reflects the latest backend behavior after 2025-12-06 fixes. Base URL (dev): `http://127.0.0.1:8000`.

---

## 2025-12-10 – Project archive API
- `DELETE /projects/{id}` now **archives** projects (soft delete) instead of 405. Archived projects remain readable (conversations/tasks/docs/usage) but may reject new writes while archived.
- `GET /projects` defaults to active projects; pass `include_archived=true` to include archived ones. `GET /projects/{id}` returns archived rows for audit.
- Retrieval debug note: `GET /conversations/{id}/debug/retrieval_context` returns **404** when the conversation id is missing; this is expected and not a regression.

---

## 1. Projects & Conversations

### 1.1 Projects
- **GET `/projects`**  
  List projects. Archived projects are hidden by default; pass `include_archived=true` to include them.

- **POST `/projects`**  
  Create a project. Body:
  ```json
  {
    "name": "My Project",
    "local_root_path": "C:\\Path\\To\\Repo",
    "description": "Optional description"
  }
  ```
  Notes:
  - `local_root_path` is required and must point to an existing path; invalid or missing paths return 400.
  - `name` must be unique; duplicate names return 409.

- **GET `/projects/{project_id}`**  
  Get project details.

- **PATCH `/projects/{project_id}`**  
  Update `name`, `description`, `local_root_path`, or `instruction_text`.

- **DELETE `/projects/{project_id}`**  
  Archive (soft delete) a project. Returns 200/204. Archived projects stay readable but are excluded from `GET /projects` unless `include_archived=true`; write operations may be rejected while archived.

### 1.2 Conversations & messages
- **GET `/projects/{project_id}/conversations`**  
  List conversations for a project.

- **POST `/conversations`**  
  Create a conversation. Body:
  ```json
  {
    "project_id": 1,
    "title": "Architecture",
    "folder_id": null
  }
  ```

- **GET `/conversations/{conversation_id}/messages`**  
  List messages in a conversation.

- **POST `/chat`**  
  Append a new user message and generate an assistant reply. Body:
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
  List tasks for a project (open first, then recency/priority).

- **GET `/projects/{project_id}/tasks/overview`**  
  Convenience response with both `tasks` and pending `task suggestions` (low-confidence add/complete). Query: `suggestion_status` (default `pending`), `suggestion_limit` (default 50, max 200). See section 8.1 for suggestion approve/dismiss actions.

- **POST `/projects/{project_id}/tasks`**  
  Create a task scoped to the project. Body:
  ```json
  {
    "description": "Add README",
    "priority": "normal",
    "blocked_reason": null,
    "auto_notes": null
  }
  ```
  (The project_id comes from the path.)

- **POST `/tasks`**  
  Global variant (body must include `project_id`).

- **PATCH `/tasks/{task_id}`**  
  Update `description`, `status`, `priority`, `blocked_reason`, `auto_notes`.

- **DELETE `/tasks/{task_id}`**  
  Delete a task by id (used to clean up artifacts).

- **POST `/projects/{project_id}/auto_update_tasks`**  
  Trigger automatic TODO extraction from the most recent conversation in the project. Returns 400 if no conversations exist.
  - The `/chat` endpoint now attempts an automatic auto-update after each reply (config flag `AUTO_UPDATE_TASKS_AFTER_CHAT`, defaults to `true`). Failures are logged and retried once; the explicit endpoint remains available for manual retries.

Notes:
- `status` is validated (e.g., `open`, `in_progress`, `blocked`, `done`); invalid values return 422.
- `priority` accepts `critical`, `high`, `normal`, `low`.
- `auto_confidence`, `auto_last_action`, `auto_last_action_at`, and `auto_notes` are returned on tasks to surface automation metadata; confidence chips appear in the Tasks UI.

---

## 3. Docs, notes, decisions, memory

### 3.1 Docs
- **GET `/projects/{project_id}/docs`**  
  List documents for a project.

- **POST `/projects/{project_id}/docs`**  
  Create a metadata-only document. Body:
  ```json
  {
    "title": "Design notes",
    "description": "Optional description"
  }
  ```

- **POST `/projects/{project_id}/docs/text`**  
  Ingest text as a document. Body:
  ```json
  {
    "name": "Design notes",
    "text": "Full text content",
    "description": "Optional description"
  }
  ```

- **POST `/docs/text`**  
  Ingest text with explicit `project_id`.

- **POST `/docs/upload_text_file`**  
  Multipart upload for text/markdown/log files.

- **GET `/docs/{doc_id}`** / **PATCH** / **DELETE**  
  Fetch, update, or delete a document.

### 3.2 Project instructions & decision log
- **GET `/projects/{project_id}/instructions`**  
  Returns `project_id`, `instruction_text`, `instruction_updated_at`, `pinned_note_text`.

- **PUT `/projects/{project_id}/instructions`**  
  Update instructions and optional pinned note. Body:
  ```json
  {
    "instruction_text": "Keep responses concise.",
    "pinned_note_text": "Important project note"
  }
  ```

- **GET `/projects/{project_id}/decisions`**  
  List decisions (drafts first, newest first).

- **POST `/projects/{project_id}/decisions`**  
  Create a decision. Body (examples):
  ```json
  {
    "title": "Choose database",
    "details": "Use Postgres in prod",
    "category": "architecture",
    "status": "recorded",
    "tags": ["db", "architecture"],
    "is_draft": false,
    "source_conversation_id": 10,
    "follow_up_task_id": null
  }
  ```

- **PATCH `/decisions/{decision_id}`**  
  Update title/details/category/status/tags/is_draft/follow_up_task_id.

- **DELETE `/decisions/{decision_id}`**  
  Delete a decision.

### 3.3 Memory
- **GET `/projects/{project_id}/memory`**  
  List active memory items (non-superseded, non-expired), pinned first.

- **POST `/projects/{project_id}/memory`**  
  Create a memory item. Body:
  ```json
  {
    "title": "Key facts",
    "content": "Important details",
    "tags": ["qa", "memory"],
    "pinned": false,
    "expires_at": null,
    "source_conversation_id": null,
    "source_message_id": null,
    "supersedes_memory_id": null
  }
  ```

- **GET `/memory_items/{memory_id}`**  
  Fetch a single memory item.

- **PATCH `/memory_items/{memory_id}`**  
  Update title/content/tags/pinned/expires_at/source refs/superseded_by_id.

- **DELETE `/memory_items/{memory_id}`**  
  Delete a memory item (also removes embedding).

---

## 4. Search

### 4.1 Message search
- **POST `/search/messages`**
  ```json
  {
    "project_id": 1,
    "query": "search terms",
    "limit": 20
  }
  ```

### 4.2 Docs & memory search
- **POST `/search/docs`**  
  Semantic search across document chunks. Optional `document_id` to scope.

- **POST `/search/memory`**  
  Semantic search across memory items. Returns `memory_id`, `title`, `content`, `distance`.

---

## 5. Filesystem

- **GET `/projects/{project_id}/fs/list`**  
  List files/dirs under project root. Query: `subpath` (relative).

- **GET `/projects/{project_id}/fs/read`**  
  Read a file. Query: `file_path` (preferred) or `subpath`.

- **PUT `/projects/{project_id}/fs/write`**  
  Write file content. Body:
  ```json
  {
    "file_path": "docs/fs_test.txt",
    "content": "new text",
    "create_dirs": false
  }
  ```

- **POST `/projects/{project_id}/fs/ai_edit`**  
  Body includes `file_path`, `instruction` (alias: `instructions`), optional `apply_changes` to write back, and optional `include_diff`.

---

## 6. Ingestion jobs

- **POST `/projects/{project_id}/ingestion_jobs`**  
  Kick off a repo/doc ingestion job (returns immediately). Body includes `kind` (`"repo"`), `source` path, optional `name_prefix`, `include_globs`. Requires project `local_root_path`.

- **GET `/projects/{project_id}/ingestion_jobs/{job_id}`**  
  Poll job status and metrics (`status`, items/files processed, bytes, error).

- **GET `/projects/{project_id}/ingestion_jobs?limit=20`**  
  List recent jobs (default limit 20) for history/audit.

- **POST `/projects/{project_id}/ingestion_jobs/{job_id}/cancel`**  
  Request cancellation of a running job (stops after current file).

---

## 7. Terminal

- **POST `/projects/{project_id}/terminal/run`**  
  Run a shell command under the project root (optional `cwd`). Body (no project_id needed when using the scoped path):
  ```json
  {
    "command": "pytest -q",
    "cwd": "backend",
    "timeout_seconds": 60
  }
  ```
  Returns `stdout`, `stderr`, `exit_code`, and resolved `cwd`.

- **GET `/projects/{project_id}/terminal/history`**  
  Placeholder: currently returns an empty list after validating the project; extend later to store recent runs.

---

## 8. Usage & telemetry

- **GET `/conversations/{conversation_id}/usage`**  
  Returns per-conversation usage records with totals and cost estimate.

- **GET `/debug/telemetry`**  
  Returns telemetry for LLM routing (`auto_routes`, `fallback_attempts`, `fallback_success`) and task automation. Task automation now includes confidence stats (`min/max/avg/count` with buckets) and the latest task suggestions (pending add/complete items with confidence and payload) to aid QA of low-confidence flows. Optional `reset=true` query param clears counters after returning the snapshot.

### 8.1 Task suggestions & overview
- **GET `/projects/{project_id}/task_suggestions`**  
  List task suggestions (low-confidence add/complete). Query: `status` (default `pending`), `limit` (default 50, max 200). Returns `TaskSuggestionRead` with payload decoded plus task metadata when available.

- **POST `/task_suggestions/{suggestion_id}/approve`** / **POST `/task_suggestions/{suggestion_id}/dismiss`**  
  Approve or dismiss a suggestion. Approving an `add` creates the task; approving a `complete` marks the target task done with an audit note.

- **GET `/projects/{project_id}/tasks/overview`**  
  Convenience endpoint returning both `tasks` and `suggestions` (pending by default) in one call. Query: `suggestion_status`, `suggestion_limit`.

Retrieval debug: `GET /conversations/{id}/debug/retrieval_context` returns **404** for missing conversation IDs; treat this as expected when the conversation does not exist.

Notes on modes:
- Mode → model defaults (overridable via `OPENAI_MODEL_<MODE>`): `auto:gpt-4.1`, `fast:gpt-4.1-mini`, `deep:gpt-5.1`, `budget:gpt-4.1-nano`, `research:o3-deep-research`, `code:gpt-5.1-codex`.
- `research` (`o3-deep-research`) requires at least one tool (`web_search_preview`, `mcp`, or `file_search`). Without tools, OpenAI returns 400 and the request will fall back to the next candidate model. Configure tools or point `OPENAI_MODEL_RESEARCH` to a non-tool model if you just need plain chat.
- Cost estimation uses the pricing table in `backend/app/llm/pricing.py`. Models without an entry are counted as $0. Added entries for `gpt-5-pro`, `gpt-5-nano`, and `gpt-5.1-codex`; adjust as your billing changes.

---

## 9. Health & misc

- **GET `/health`**  
  Basic health check endpoint for operators/automation.

---

## 10. Notes for implementers

- For exact request/response schemas, consult:
  - Pydantic models in `backend/app/api/main.py` and related modules.
  - SQLAlchemy models in `backend/app/db/models.py`.
- When adding/changing endpoints:
  - Update this file.
  - Update `docs/SYSTEM_MATRIX.md` (feature ↔ endpoint mapping).
  - Add/adjust QA coverage in `docs/TEST_PLAN.md` and/or `qa/` probes.

---

## 11. Planned Autopilot & Blueprint APIs (design-only)

> These endpoints are **not yet implemented**; documented for future alignment.

### 11.1 Blueprint & Plan
- **POST `/projects/{project_id}/blueprints`** — Create a `Blueprint` for a project document.
- **GET `/projects/{project_id}/blueprints`** — List blueprints.
- **GET `/blueprints/{blueprint_id}`** — Fetch blueprint metadata + PlanNode tree.
- **PATCH `/blueprints/{blueprint_id}`** — Update title/description/status or mark active.
- **POST `/blueprints/{blueprint_id}/generate_plan`** — Generate outline/PlanNode tree.
- **PATCH `/plan_nodes/{id}`** — Edit PlanNode fields (title, summary, status, priority, risk, order, etc.).
- **POST `/plan_nodes/{plan_node_id}/generate_tasks`** — Generate tasks for a PlanNode.
- **POST `/blueprints/{blueprint_id}/generate_all_tasks`** — Generate tasks for all feature/story PlanNodes.

### 11.2 Runs & Autopilot
- **POST `/projects/{project_id}/runs`** — Create an `ExecutionRun` (optionally linked to task/conversation).
- **GET `/projects/{project_id}/runs`** — List runs, optional status filter.
- **GET `/runs/{run_id}`** — Fetch a run and ordered `ExecutionStep`s.
- **POST `/runs/{run_id}/advance`** — Approve/skip/abort the next pending step.
- **POST `/runs/{run_id}/rollback`** — Restore files touched by a run using rollback data.
- **POST `/projects/{project_id}/autopilot_tick`** — ManagerAgent heartbeat to advance or start runs.
- **GET `/projects/{project_id}/manager/plan`** — Manager’s view of plan (phase, next tasks, active runs, rationale).
- **POST `/projects/{project_id}/refine_plan`** — Retrospective to refine plan based on learning signals.

### 11.3 Learning & Metrics
- **POST `/projects/{project_id}/snapshot/refresh`** — Build/update a `ProjectSnapshot`.
- **GET `/projects/{project_id}/snapshot`** — Fetch snapshot text and metrics JSON.
- **GET `/projects/{project_id}/learning_metrics`** — Aggregate metrics (cycle time, difficulty, fragile areas, plan deviation, blocked count).

---

Notes:
- Trailing slashes are not required; stick to the paths above to avoid 307 redirects.
- Auto-update tasks runs best-effort; it will no-op if no recent conversation exists.***

