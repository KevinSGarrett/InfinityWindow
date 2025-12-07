# InfinityWindow Developer Guide

This guide is for developers extending or maintaining InfinityWindow.

---

## 1. Developer environment

### 1.1 Backend

From `backend/`:

- Create a virtual environment and install dependencies:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

- Configure environment variables in `backend/.env`:
  - `OPENAI_API_KEY=...`
  - Optional model overrides (see `docs/CONFIG_ENV.md` when filled).

- Run the app:

```powershell
uvicorn app.api.main:app --reload
```

The app listens on `http://127.0.0.1:8000`.

### 1.2 Frontend

From `frontend/`:

```powershell
npm install
npm run dev
```

Open the URL reported by Vite (default `http://127.0.0.1:5173/`).

---

## 2. Code structure (backend)

- `app/api/main.py`
  - FastAPI `app` instance.
  - All HTTP endpoints:
    - Projects, conversations, messages.
    - Tasks, docs, memory, decisions.
    - Filesystem and terminal.
    - Search and telemetry.
  - Helper functions such as `auto_update_tasks_from_conversation`.

- `app/db/models.py`
  - SQLAlchemy models and relationships.
  - Each model maps closely to a UI concept:
    - `Project` ↔ project dropdown.
    - `Conversation` / `Message` ↔ chat thread.
    - `Task` ↔ Tasks tab.
    - `Document` ↔ Docs tab.
    - `MemoryItem` ↔ Memory tab.
    - `Decision` ↔ decision log in Notes tab.

- `app/llm/openai_client.py`
  - LLM client wrapper.
  - Mode → model routing logic (including `auto` heuristics).
  - Telemetry counters for routes and fallbacks.

- `app/vectorstore/chroma_store.py`
  - Abstraction over Chroma collections:
    - Messages, docs, memory embeddings.
  - Central place to fix ingestion/query issues.

When adding a new feature, try to:

- Keep HTTP surface in `app/api/main.py`.
- Reuse or extend models in `app/db/models.py`.
- Add any new vector‑store behavior in `chroma_store.py`.

### 2.1 Planned Autopilot modules (design)

The Autopilot design introduces several new backend modules that **do not exist yet** but are referenced in `AUTOPILOT_PLAN.md`:

- `backend/app/services/blueprints.py` – Blueprint & PlanNode ingestion/generation helpers.
- `backend/app/services/conversation_summaries.py` – rolling conversation summaries.
- `backend/app/services/snapshot.py` – ProjectSnapshot generation.
- `backend/app/llm/context_builder.py` – builds structured context bundles for chat and workers.
- `backend/app/services/alignment.py` – alignment checks for risky edits/commands.
- `backend/app/services/runs.py` – ExecutionRun/ExecutionStep orchestration and rollback helpers.
- `backend/app/services/workers.py` – code/test/doc worker wrappers over Files/Terminal/Search tools.
- `backend/app/llm/intent_classifier.py` – classifies chat messages into START_BUILD / PAUSE_AUTOPILOT / etc.
- `backend/app/services/manager.py` – ManagerAgent implementation (Autopilot brain).

When you start implementing these, keep them small and focused, mirroring the existing patterns for API modules and services. Update `SYSTEM_MATRIX.md`, `API_REFERENCE.md`, and `CONFIG_ENV.md` as new endpoints, models, and env vars go live.

---

## 3. Code structure (frontend)

Currently, most UI logic lives in `frontend/src/App.tsx`:

- Left column:
  - Project selector and conversation list.
  - New chat button.
- Middle column:
  - Chat messages and input.
  - Mode selector (auto/fast/deep/budget/research/code).
- Right column:
  - 8 tabs driven by local state, each rendering a panel:
    - Tasks, Docs, Files, Search, Terminal, Usage, Notes, Memory.

As the app grows, consider refactoring:

- Extract per‑tab components (e.g., `Tabs/TasksPanel.tsx`, `Tabs/FilesPanel.tsx`).
- Extract shared hooks for data fetching.

CSS is managed primarily in `frontend/src/App.css`.  
Playwright tests live under `frontend/tests/`.

---

## 4. Patterns and conventions

- **API layer**:
  - Keep request/response models well‑typed in Python (Pydantic) and in TypeScript (interfaces/types) where applicable.
  - Prefer explicit endpoints over “do everything” generics for clarity.

- **Docs alignment**:
  - When APIs change, update `docs/API_REFERENCE_UPDATED.md` (primary), keep `docs/API_REFERENCE.md` pointers intact, and log fixes in `docs/ISSUES_LOG.md`.

- **Telemetry**:
  - For new automated behaviors (e.g., routing, task automation), consider adding simple counters.
  - Expose important counters via `/debug/telemetry`.

- **Error handling**:
  - Use FastAPI’s exception types and appropriate status codes.
  - For long‑running operations, surface progress in logs and/or telemetry.

- **Testing**:
  - For backend logic, favor small, focused tests (where present) plus the smoke probes in `qa/`.
  - For UI changes, add or extend Playwright specs when feasible.

---

## 5. Running tests

### 5.1 Backend smoke tests

From repo root (with backend venv active):

```powershell
python -m qa.run_smoke
```

This runs:

- Message search probe.
- Task auto‑loop probe.
- Mode routing probe.

### 5.2 Frontend tests

From `frontend/`:

```powershell
npm run build          # typecheck + build
npx playwright install # first time only
npm run dev -- --port 5174  # in one terminal
npm run test:e2e            # in another
```

---

## 6. Making changes safely

1. **Understand the feature**:
   - Read relevant sections in `docs/SYSTEM_OVERVIEW.md` and `docs/SYSTEM_MATRIX.md`.
   - Skim related tests and QA entries in `docs/TEST_PLAN.md`.

2. **Change the smallest thing that can work**:
   - Prefer a focused patch that affects a single area (backend, frontend, docs).
   - Update any inline comments or doc references that become incorrect.

3. **Update docs and roadmap**:
   - If you add/remove capabilities, reflect them in:
     - `docs/PROGRESS.md`.
     - `docs/TODO_CHECKLIST.md`.
     - `docs/SYSTEM_MATRIX.md` (if new endpoints/models are involved).

4. **Verify with tests**:
   - Run `qa/run_smoke.py` for backend‑affecting changes.
   - Run Playwright specs if you touched UI flows.
   - Current dev defaults: backend on 8000; frontend on 5173/5174; `npm run test:e2e` (covers tasks-confidence, tasks-suggestions, ui-smoke/chat-smoke/extended, ui-accessibility-phase3); API suite via `PowerShell: $env:PYTHONPATH='..'; pytest tests_api` (upstream SQLAlchemy utcnow warnings only). Telemetry reset: `GET /debug/telemetry?reset=true` clears counters.

5. **Avoid breaking QA helpers**:
   - Keep `tools/reset_qa_env.py` working: if DB paths or ports change, update the script.

---

## 7. Where to go next

- For a high‑level picture: `docs/SYSTEM_OVERVIEW.md`.
- For cross‑referencing: `docs/SYSTEM_MATRIX.md`.
- For specific behaviors: search within `backend/app/api/main.py` and `frontend/src/App.tsx`.
- For project evolution history: `docs/PROGRESS.md` and future `docs/CHANGELOG.md`.

Use this guide as your starting point, then dive into the referenced files for detail.


