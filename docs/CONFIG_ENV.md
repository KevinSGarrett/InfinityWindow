# InfinityWindow Configuration & Environment

This document describes the **main configuration knobs and environment variables** used by InfinityWindow.

---

## 1. Backend environment variables

Backend configuration is typically provided via a `.env` file in `backend/` or through the process environment.

### 1.1 Core

- **`OPENAI_API_KEY`** (required)  
  API key for the OpenAI (or compatible) API.

- **`DATABASE_URL`** (optional)  
  SQLAlchemy connection string.  
  Default in development: SQLite file in `backend/infinitywindow.db`.

- **`CHROMA_PERSIST_DIR`** (optional)  
  Filesystem path where Chroma stores its collections.  
  Default in development: `backend/chroma_data/`.

### 1.2 Model selection

InfinityWindow uses **chat modes** (`auto`, `fast`, `deep`, `budget`, `research`, `code`) which map to underlying models in `app/llm/openai_client.py`.

You can override the defaults via:

- **`OPENAI_MODEL_AUTO`**
- **`OPENAI_MODEL_FAST`**
- **`OPENAI_MODEL_DEEP`**
- **`OPENAI_MODEL_BUDGET`**
- **`OPENAI_MODEL_RESEARCH`**
- **`OPENAI_MODEL_CODE`**

If unset, `_DEFAULT_MODELS` in `openai_client.py` are used:

- `auto` → `gpt-4.1`
- `fast` → `gpt-4.1-mini`
- `deep` → `gpt-5.1`
- `budget` → `gpt-4.1-nano`
- `research` → `o3-deep-research`
- `code` → `gpt-5.1-codex`

Examples of explicit overrides you might set in `backend/.env`:

```text
OPENAI_MODEL_AUTO=gpt-5.1
OPENAI_MODEL_FAST=gpt-4.1-mini
OPENAI_MODEL_DEEP=gpt-5-pro
OPENAI_MODEL_BUDGET=gpt-4.1-nano
OPENAI_MODEL_RESEARCH=o3-deep-research
OPENAI_MODEL_CODE=gpt-5.1-codex
```

These same model IDs can also be typed directly into the **Model override** input beside the Mode selector in the UI when you want to force a specific model for a particular request.

The `auto` mode uses `_infer_auto_submode` to pick between:

- `code` – code‑heavy prompts.
- `research` – long, research‑flavored prompts.
- `fast` – short, simple prompts.
- `deep` – everything else.

### 1.3 CORS & networking

- **`CORS_ALLOW_ORIGINS`** (optional)  
  Comma‑separated list of allowed origins.  
  In development, the app is configured to allow:
  - `http://localhost:5173` / `http://127.0.0.1:5173`
  - `http://localhost:5174` / `http://127.0.0.1:5174` (for Playwright / alternative ports)

- **`HOST` / `PORT`** (optional)  
  Used if you customize how uvicorn is launched. Default development command:

  ```powershell
  uvicorn app.api.main:app --reload --host 127.0.0.1 --port 8000
  ```

---

## 2. Frontend configuration

The frontend is a Vite + React app. Common configuration points:

- **Dev server port**  
  - Default: `5173`.  
  - For Playwright tests, it’s common to run on `5174`:

    ```powershell
    npm run dev -- --host 127.0.0.1 --port 5174
    ```

- **Playwright baseURL** (`frontend/playwright.config.ts`)  
  Must match the dev server URL:

  ```ts
  use: {
    baseURL: 'http://127.0.0.1:5174',
    // ...
  }
  ```

---

## 3. QA / CI configuration

- **QA copy location**  
  - `C:\InfinityWindow_QA` (mirrors primary repo).

- **Makefile (QA)**  
  - Located at `C:\InfinityWindow_QA\Makefile`.  
  - Defines `ci` target:
    - Runs backend tests (via `pytest`) in `backend/`.
    - Runs `npm run build` in `frontend/`.

- **Reset script**  
  - `tools/reset_qa_env.py`:
    - Assumes backend DB and Chroma live under `backend/`.
    - Checks for port 8000 usage before proceeding.

If you move directories or change DB/Chroma locations, update:

- `reset_qa_env.py`
- Any hard‑coded paths in QA tooling.

---

## 4. Logging & telemetry

InfinityWindow uses simple logging/prints and in‑memory counters for telemetry:

- **LLM telemetry** (`_LLM_TELEMETRY_COUNTERS` in `openai_client.py`):
  - Tracks auto‑mode routes and fallback attempts.

- **Task telemetry** (`_TASK_TELEMETRY_COUNTERS` in `app/api/main.py`):
  - Tracks auto‑added, auto‑completed, auto‑deduped tasks.

Expose via:

- **`GET /debug/telemetry`**

No special env vars are required for telemetry today, but future work may add toggles here.

---

## 5. Extending configuration

When adding new configurable behavior:

1. Define a clear environment variable name (or config field).
2. Document it in this file (`docs/CONFIG_ENV.md`).
3. Use safe defaults when the variable isn’t set.
4. Avoid hard‑coding environment‑specific paths or secrets in the code.


