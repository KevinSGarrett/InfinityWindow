# InfinityWindow Hydration – 2025‑12‑02

This file is a **high‑signal briefing** for humans and AI agents working in this repo.  
It describes what the system is, what exists today, where the important code lives, and how to behave safely.

> When this file and the code disagree, the code is the source of truth.  
> When this file and older text files (`Hydration_File_*.txt`) disagree, this file wins.

---

## 1. What InfinityWindow is

InfinityWindow is a **local AI workbench for long‑running projects**.  
It combines:

- A **FastAPI backend** (`backend/`) with:
  - Projects, conversations, messages, tasks, docs, memory, decisions, usage.
  - Vector search (Chroma) over messages/docs/memory.
  - Filesystem and terminal integration, guarded to project roots.
  - Model routing and telemetry for multiple chat modes.
  - QA helpers and a guarded QA reset script.
- A **React + TypeScript frontend** (`frontend/`) with:
  - 3‑column layout: projects / chat / right‑hand workbench.
  - Right‑hand tabs: Tasks, Docs, Files, Search, Terminal, Usage, Notes, Memory.
- A growing **documentation + QA library** under `docs/` and `qa/`.

The “OS for long‑running projects” metaphor: InfinityWindow tries to keep **all** relevant state (conversations, tasks, docs, code, decisions, memory) in one coherent window so AI can help you maintain and evolve complex work over time.

---

## 2. Current architecture snapshot

### 2.1 Backend

- Entry point: `backend/app/api/main.py`
  - Defines the FastAPI app, CORS, and all HTTP routes.
  - Exposes:
    - Project, conversation, message endpoints.
    - Task, doc, memory, decision, folder endpoints.
    - Filesystem and terminal endpoints.
    - Search endpoints (`/search/messages`, etc.).
    - Debug telemetry endpoint (`/debug/telemetry`).

- Data models: `backend/app/db/models.py`
  - Core SQLAlchemy models:
    - `Project`, `Conversation`, `Message`
    - `Task`, `Document`, `MemoryItem`, `Decision`
    - `IngestionJob` + `FileIngestionState` (repo ingestion progress + per-file SHA cache)
    - Usage/auxiliary models as needed.
  - Backed by SQLite DB at `backend/infinitywindow.db` in dev/QA.

- Vector store: `backend/app/vectorstore/chroma_store.py`
  - Manages Chroma collections for messages, docs, memory.
  - Provides `add_*_embedding` and query helpers.
  - Important fix: only includes `folder_id` metadata when non‑`None` to avoid Chroma errors.
- Tasks/search fixes (2025-12-06):
  - Task upkeep now runs automatically after `/chat` (configurable via `AUTO_UPDATE_TASKS_AFTER_CHAT`); manual `POST /projects/{id}/auto_update_tasks` remains.
  - Added task delete (`DELETE /tasks/{task_id}`) and tasks overview (`GET /projects/{id}/tasks/overview` for tasks + suggestions).
  - Memory search stores/returns `title`; duplicate handler removed.
  - Filesystem read accepts `file_path` or `subpath`; AI edit accepts `instruction` or `instructions`.
  - Terminal scoped run no longer needs `project_id` in body; path param is injected.
- Pricing/usage:
  - Pricing table includes `gpt-5-nano`, `gpt-5-pro`, `gpt-5.1-codex`; usage cost reflects these.
- Repo/document ingestion:
  - `app/llm/embeddings.py` exposes `embed_texts_batched`, honoring `MAX_EMBED_TOKENS_PER_BATCH` / `MAX_EMBED_ITEMS_PER_BATCH`.
  - `app/ingestion/docs_ingestor.py` + `app/ingestion/github_ingestor.py` handle text and repo ingestion via `IngestionJob` records.
  - `POST /projects/{id}/ingestion_jobs` queues work; `GET /projects/{id}/ingestion_jobs/{job_id}` reports progress/errors; `GET /projects/{id}/ingestion_jobs` lists history; `POST /projects/{id}/ingestion_jobs/{job_id}/cancel` requests cancellation.
  - Telemetry counters (jobs started/completed/failed/cancelled, bytes processed) feed into `/debug/telemetry`.

- LLM integration: `backend/app/llm/openai_client.py`
  - Wraps the OpenAI (or compatible) client.
  - Maintains `_DEFAULT_MODELS` per mode (`auto`, `fast`, `deep`, `budget`, `research`, `code`).
  - Implements `_infer_auto_submode` for task‑aware routing:
    - `code` vs `research` vs `fast` vs `deep`, based on prompt content/length.
  - Handles model fallback:
    - Tries primary model, then `OPENAI_MODEL_AUTO`, then `OPENAI_MODEL_FAST`.
  - Tracks telemetry in `_LLM_TELEMETRY_COUNTERS`.

- Tasks auto‑loop: `auto_update_tasks_from_conversation` in `app/api/main.py`
  - Reads recent conversation text, detects:
    - **Completion phrases** → mark tasks as done.
    - **New TODO descriptions** → add new tasks.
  - Uses normalization, fuzzy matching, and token overlap to:
    - Avoid duplicates.
    - Link completion lines back to existing tasks.
  - Keeps task ordering sane:
    - `list_project_tasks` sorts by `status` (open first) then `updated_at` (most recent first).

- QA helper: `tools/reset_qa_env.py`
  - Safely resets SQLite DB + Chroma data:
    - Checks port 8000 is not in use.
    - Creates timestamped backups before deleting.

### 2.2 Frontend

- Main app: `frontend/src/App.tsx`
  - Renders:
    - Left: project selector + conversation list + “New chat”.
    - Middle: chat messages + mode selector + input box.
    - Right: 8 tabs:
      - **Tasks** – project tasks list.
      - **Docs** – project documents.
      - **Files** – project filesystem browser + editor + AI diffs.
      - **Search** – cross‑cutting search.
      - **Terminal** – manual command execution.
      - **Usage** – usage/cost overview.
      - **Notes** – project instructions + decision log.
      - **Memory** – long‑term memory items.
  - Handles keyboard shortcuts (e.g., Alt+1..8 for right‑tab switching).
  - Provides a “Refresh all” button for the right‑hand panels.

- Styles: `frontend/src/App.css`
  - Defines the 3‑column layout and right‑tabs toolbar/panels.

- E2E tests: `frontend/tests/*.spec.ts`
  - `right-column.spec.ts` – verifies each right tab activates correctly.
  - `files-tab.spec.ts` – verifies file browsing + editor behaviors.
  - `notes-memory.spec.ts` – verifies Notes and Memory tabs populate from seeded API data.

---

## 3. QA & testing snapshot

- **Backend smoke suite**: `qa/run_smoke.py`
  - `qa/message_search_probe.py` – ensures `/search/messages` works end‑to‑end.
  - `qa/tasks_autoloop_probe.py` – tests auto‑add/auto‑complete tasks for a seeded project.
  - `qa/mode_routing_probe.py` – asserts correct model routing per scenario.

- **Manual test plan**: `docs/TEST_PLAN.md`
  - Phased plan (A–H) covering environment, CRUD, search, tasks, docs, memory, files, terminal, modes, telemetry.

- **Test reports**:
  - `docs/TEST_REPORT_2025-12-02.md` – documented run with issues and resolutions.
  - `docs/TEST_REPORT_TEMPLATE.md` – reusable format for future runs.

- **CI (QA copy)**:
  - `C:\InfinityWindow_QA\Makefile` with `ci` target:
    - Backend tests (`pytest`) and frontend build (`npm run build`).

---

## 4. Documentation landscape

Key docs (current and in progress):

- Root `README.md` – concise overview and quickstart.
- `docs/README.md` – docs index.
- `docs/SYSTEM_OVERVIEW.md` – high‑level architecture + feature description (to be refreshed for strict accuracy).
- `docs/USER_MANUAL.md` – detailed setup and usage manual.
- `docs/SYSTEM_MATRIX.md` – this is the detailed “where is everything” map.
- `docs/TODO_CHECKLIST.md` – checklist view of the roadmap.
- `docs/PROGRESS.md` – authoritative progress log and roadmap.
- `docs/TEST_PLAN.md`, `docs/TEST_REPORT_TEMPLATE.md`, `docs/TEST_REPORT_*.md` – QA artifacts.

Additional docs being built out:

- `docs/DEV_GUIDE.md`, `docs/AGENT_GUIDE.md`, `docs/OPERATIONS_RUNBOOK.md`.
- `docs/API_REFERENCE.md`, `docs/CONFIG_ENV.md`, `docs/SECURITY_PRIVACY.md`.
- `docs/CHANGELOG.md`, `docs/DECISIONS_LOG.md`, `docs/RELEASE_PROCESS.md`.

Autopilot & blueprint design docs (roadmap only, not implemented yet):

- `docs/AUTOPILOT_PLAN.md` – high‑level Autopilot architecture and phases.
- `docs/AUTOPILOT_LEARNING.md` – Project Learning Layer design.
- `docs/AUTOPILOT_LIMITATIONS.md` – Autopilot scope and guardrails.
- `docs/AUTOPILOT_EXAMPLES.md` – usage scenarios once Autopilot is available.
- `docs/MODEL_MATRIX.md` – model/env routing for chat modes and Autopilot roles.

This hydration file is meant to point you to those documents rather than duplicate them.

---

## 5. Behavioral guidelines for AI agents

If you are an AI agent operating in this repo:

1. **Safe writes**
   - Respect user‑defined safe‑write rules:
     - Prefer writing within `docs/**`, `tests/**`, `tools/**`, and project‑specific plugin paths.
     - Do NOT create arbitrary demo/test files outside explicitly allowed areas.
   - Keep changes coherent and minimal; avoid mass rewrites unless explicitly requested.

2. **Testing discipline**
   - After substantive backend or frontend changes, run:
     - Backend smoke: `python -m qa.run_smoke`.
     - Frontend: `npm run build` (and Playwright tests when relevant).
   - For QA copies, use `make ci` as defined in the QA Makefile.
   - Record results in `docs/PROGRESS.md` CI log section when appropriate.

3. **Docs synchronization**
   - When you add features or fix issues:
     - Update `docs/PROGRESS.md` (what changed, which window).
     - Update `docs/TODO_CHECKLIST.md` and any relevant roadmap or QA docs.
   - Keep `SYSTEM_MATRIX.md` in sync when introducing new endpoints/features.

4. **Avoid destructive operations**
   - Do NOT:
     - Delete user data (projects, conversations, tasks, docs, memory) unless explicitly requested.
     - Drop DB tables or re‑initialize Chroma without backing up and confirming scope.
   - Use `tools/reset_qa_env.py` only in clearly designated QA copies (e.g., `C:\InfinityWindow_QA`), not on the primary working environment, unless instructed.

5. **Clarity and traceability**
   - Prefer small, well‑documented patches over large, opaque ones.
   - When making complex changes:
     - Reference the files and sections you’re editing.
     - Update documentation in the same window whenever possible.

---

## 6. High‑level mental model

When you think about InfinityWindow, keep this model in mind:

- **State**:
  - Persistent: DB (projects, messages, tasks, docs, memory, decisions, usage).
  - Semi‑persistent: embeddings (Chroma collections).
  - Ephemeral: active chat prompts, in‑flight AI suggestions.

- **Flows**:
  - User acts in UI → frontend calls backend → backend reads/writes DB + vector store → LLM called (if needed) → response persisted and reflected in UI.
  - Automation (tasks, auto‑mode routing) piggybacks on these flows via helper functions and telemetry.

- **Boundaries**:
  - Backend API contracts: defined in `app/api/main.py` and `API_REFERENCE.md` (once filled).
  - Frontend UI contracts: right‑hand tabs correspond to specific endpoints and data models.
  - Docs & QA contracts: `PROGRESS.md` + `TEST_PLAN.md` define what “done and working” means.

Use this file as your first stop when you need to rehydrate context quickly before working in the repo. Then jump into `SYSTEM_OVERVIEW.md`, `SYSTEM_MATRIX.md`, and `USER_MANUAL.md` for more depth.


