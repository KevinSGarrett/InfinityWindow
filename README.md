# InfinityWindow – AI Workbench for Long‑Running Projects <!-- omit in toc -->

InfinityWindow is a local AI workbench for **long‑running, project‑scale work**.  
It keeps your conversations, tasks, docs, files, decisions, and memory **in one place**, and lets an AI co‑pilot operate over the *real* project (DB, files, terminal, vector store) instead of a single chat window.

This repo contains:

- A **FastAPI backend** (`backend/`) with projects, conversations, tasks, docs, memory items, filesystem + terminal integration, model routing, telemetry, and QA helpers.
- A **React + TypeScript frontend** (`frontend/`) with a 3‑column UI (Projects / Chat / Right‑hand workbench tabs).
- An evolving **documentation and QA library** under `docs/` and `qa/`.

## Build / CI status
[![CI](https://github.com/KevinSGarrett/InfinityWindow/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/KevinSGarrett/InfinityWindow/actions/workflows/ci.yml)

CI runs `make ci` (backend API tests + frontend build) on `main` using stubbed LLM + vector store dependencies, so no external API keys are required in CI.

---

## 1. Quick start

This is the “get it running locally” path. For exhaustive setup and feature coverage, see `docs/USER_MANUAL.md`.

### 1.1 Prerequisites

- **OS**: Windows 10/11 (project is developed/tested on Windows).
- **Backend**:
  - Python 3.11+ (3.12 confirmed to work).
  - `pip` available on `PATH`.
- **Frontend**:
  - Node.js (current LTS) + npm.
- **Other**:
  - Git (optional but recommended).
  - OpenAI API key (or compatible provider) for LLM calls.

### 1.2 Backend (FastAPI)

From `C:\InfinityWindow_Recovery\backend`:

```powershell
# Create and activate a venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install backend dependencies
pip install -r requirements.txt

# Configure environment (create backend/.env)
echo OPENAI_API_KEY=sk-... >> .env
# Optional: model overrides (see docs/CONFIG_ENV.md once created)
```

Run the backend:

```powershell
uvicorn app.api.main:app --reload
```

Backend will listen on `http://127.0.0.1:8000`. You can verify with:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

### 1.3 Frontend (React + Vite)

From `C:\InfinityWindow_Recovery\frontend`:

```powershell
npm install
npm run dev
```

By default Vite will serve on `http://127.0.0.1:5173/` (or the port you choose). Open that URL in your browser.

You should see:

- Left column: **Project selector + Conversations**.
- Middle: **Chat** with mode selector (`auto`, `fast`, `deep`, `budget`, `research`, `code`).
- Right: **Tabbed workbench** (Tasks, Docs, Files, Search, Terminal, Usage, Notes, Memory).

### 1.4 Minimal workflow

1. Ensure the backend is running on `:8000` and frontend dev server is running.
2. In the UI, pick a project from the dropdown (or use the default “Demo Project”).
3. Click **“+ New chat”** and send a message in the middle column.
4. Open the **Tasks**, **Docs**, **Files**, **Notes**, and **Memory** tabs on the right to explore each feature.

For detailed, step‑by‑step instructions (including QA/staging copies, CI, and reset helpers), see `docs/USER_MANUAL.md` and `docs/OPERATIONS_RUNBOOK.md` (once created).

---

## 2. Core capabilities (high level)

InfinityWindow is built around a few core ideas:

- **Project‑centric workspace**: everything is scoped to a project with its own tasks, docs, conversations, decisions, and memory.
- **Real memory & retrieval**: messages, docs, and memory items are embedded into a vector store (Chroma) and retrieved as context for each reply.
- **Local filesystem + terminal integration**: the AI can propose file edits and terminal commands, but you stay in control; all writes are constrained to the project root.
- **AI‑assisted TODOs and decisions**: a tasks tab and a structured decision log keep long‑running work organized.
- **Usage & telemetry**: per‑conversation usage records and `/debug/telemetry` let you see how models are being used and how well automation is behaving.

For a deeper architectural overview, see `docs/SYSTEM_OVERVIEW.md` (to be refreshed) and `docs/SYSTEM_MATRIX.md` (catalogue of features and where they live).

---

## 3. Repository layout (short map)

- `backend/`
  - `app/api/main.py` – FastAPI app, API endpoints (projects, chat, tasks, docs, search, filesystem, terminal, memory, telemetry).
  - `app/db/models.py` – SQLAlchemy models (Project, Conversation, Message, Task, Document, MemoryItem, UsageRecord, Decision, Folder).
  - `app/llm/openai_client.py` – LLM client, mode/model routing, pricing, telemetry helpers.
  - `app/vectorstore/chroma_store.py` – Chroma client, collections and helpers for messages, docs, memory.
  - `tools/reset_qa_env.py` – Guarded helper to reset SQLite + Chroma in a QA copy.

- `frontend/`
  - `src/App.tsx` – main React app (3‑column layout, right‑hand tabs, all UI behavior).
  - `src/App.css` – layout and styling for the workbench.
  - `playwright.config.ts` + `tests/` – UI regression tests (right‑column tabs, Files, Notes, Memory).

- `docs/`
  - `PROGRESS.md` – progress log + roadmap + QA notes.
  - `TEST_PLAN.md` – end‑to‑end test plan.
  - `TEST_REPORT_TEMPLATE.md` – template for recording QA runs.
  - `TEST_REPORT_2025-12-02.md` – example completed QA report.
  - `USER_MANUAL.md` – complete setup & usage manual (high detail).
  - `SYSTEM_OVERVIEW.md` – system‑level overview (will be refreshed).
  - `RIGHT_COLUMN_UI_PLAN.md` – notes and plans for the right‑column UI.
  - `README.md` (inside `docs/`) – **documentation index** (to be added as part of the overhaul).

- `qa/`
  - `run_smoke.py` – backend smoke suite (message search, tasks auto‑loop, mode routing).
  - `message_search_probe.py`, `tasks_autoloop_probe.py`, `mode_routing_probe.py` – individual smoke probes.

Other planning/history files live in the repo root (`Hydration_File_*.txt`, `Project_Plan_*.txt`) and will be consolidated into updated markdown docs under `docs/`.

---

## 4. Documentation

InfinityWindow is in the process of moving to a more extensive, organized documentation system. The key entry points (some existing, some being created) are:

- `docs/README.md` – **docs index**: lists all documentation, grouped by audience (users, developers, operators, agents).
- `docs/USER_MANUAL.md` – full installation + usage manual.
- `docs/SYSTEM_OVERVIEW.md` – architectural overview and main concepts.
- `docs/SYSTEM_MATRIX.md` – matrix catalogue of features, data models, endpoints, UI components, and test IDs.
- `docs/PROGRESS.md` – progress log and roadmap (v2/v3/v4+).
- `docs/TODO_CHECKLIST.md` – structured checklist of outstanding work (by phase).
- `docs/HYDRATION_*.md` – up‑to‑date hydration/rehydration files for AI agents and maintainers.
- `docs/TEST_PLAN.md`, `docs/TEST_REPORT_TEMPLATE.md`, `docs/TEST_REPORT_*.md` – QA plans and results.
- `docs/OPERATIONS_RUNBOOK.md` – how to run, reset, and maintain the system (including QA copies).
- `docs/DEV_GUIDE.md` – how to extend the backend/frontend safely.
- `docs/AGENT_GUIDE.md` – how AI agents should interact with this repo (tools, guardrails, references).
- `docs/API_REFERENCE.md` – concise reference to important REST endpoints.
- `docs/CONFIG_ENV.md` – configuration and environment variables (ports, models, CORS, etc.).
- `docs/SECURITY_PRIVACY.md` – current data, storage, and security considerations.

Once the documentation overhaul is complete, all of these will be discoverable from `docs/README.md`.

---

## 5. Testing & QA

- **Backend smoke tests**: from `C:\InfinityWindow_Recovery` (backend venv active):

  ```powershell
  python -m qa.run_smoke
  ```

  This checks:
  - Message search (`/search/messages`).
  - Autonomous TODO maintenance behavior.
  - Mode/model routing and fallback logic.

- **Frontend UI tests (Playwright)**: from `C:\InfinityWindow_Recovery\frontend`:

  ```powershell
  npm install
  npx playwright install
  npm run dev -- --host 127.0.0.1 --port 5174  # in one terminal
  npm run test:e2e                              # in another
  ```

  Current specs exercise:
  - Right‑column tab activation.
  - Files tab: browsing + editor + “Show original”.
  - Notes tab: seeded instructions + decision log.
  - Memory tab: seeded pinned memory item.

For the full QA plan and historical reports, see `docs/TEST_PLAN.md` and `docs/TEST_REPORT_2025-12-02.md`.

---

## 6. Contributing / extending

This project is under active development and is currently focused on:

- Stabilizing the v2 feature set (projects, tasks, docs, memory, files, terminal, usage).
- Hardening retrieval and model routing behavior.
- Expanding the right‑column UX and automation around TODOs and telemetry.

If you’re extending the system:

- **Start with** `docs/DEV_GUIDE.md` and `docs/SYSTEM_MATRIX.md` (once created) to understand where features live.
- Use the QA smoke suite and Playwright tests to validate changes before committing.
- Keep `docs/PROGRESS.md` and `docs/TODO_CHECKLIST.md` updated so future maintainers (and AI agents) have accurate context.

InfinityWindow is meant to feel like an **operating system for your long‑running projects**; this repo is both the implementation and the evolving documentation for how that OS works.

