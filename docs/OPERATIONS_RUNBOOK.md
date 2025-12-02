# InfinityWindow Operations Runbook

This runbook describes how to **run, reset, and validate** InfinityWindow in day‑to‑day use and in a QA/staging copy.

---

## 1. Environments

- **Primary development environment**
  - Location: `C:\InfinityWindow`
  - Purpose: day‑to‑day development and usage.

- **QA / staging environment**
  - Location: `C:\InfinityWindow_QA`
  - Purpose: clean testing of features and full test plan runs.
  - Contains a `Makefile` with a `ci` target for backend tests + frontend build.

Keep these environments separate. Do not run destructive resets (DB/Chroma deletion) on the primary environment unless explicitly required.

---

## 2. Starting and stopping services

### 2.1 Backend (FastAPI)

From `C:\InfinityWindow\backend`:

```powershell
cd C:\InfinityWindow\backend
.\.venv\Scripts\Activate.ps1   # if not already active
uvicorn app.api.main:app --reload
```

To stop:

- Press `Ctrl + C` in the terminal running uvicorn.

To check health:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

### 2.2 Frontend (Vite dev server)

From `C:\InfinityWindow\frontend`:

```powershell
cd C:\InfinityWindow\frontend
npm install           # first time
npm run dev
```

To stop:

- Press `Ctrl + C` in the terminal running `npm run dev`.

Open the app at the URL Vite reports (default `http://127.0.0.1:5173/`).

---

## 3. QA / staging operations

### 3.1 Cloning a QA copy

To create or refresh a QA copy:

1. Ensure `C:\InfinityWindow` is up to date (e.g. `git pull`).
2. Copy the directory to create `C:\InfinityWindow_QA` (using Explorer or `robocopy`).
3. Adjust any environment‑specific settings if needed (e.g. `.env`).

### 3.2 Running CI in QA (`make ci`)

From `C:\InfinityWindow_QA`:

```powershell
cd C:\InfinityWindow_QA
make ci
```

This:

- Runs backend tests (via `pytest`) in `backend/`.
- Builds the frontend (`npm run build`) in `frontend/`.

Record the result in `docs/PROGRESS.md` under the CI run log.

---

## 4. Resetting QA DB and Chroma safely

Use `tools/reset_qa_env.py` to reset the QA environment.

> **Never** run this script in the primary environment unless you fully understand the consequences.

Steps:

```powershell
cd C:\InfinityWindow_QA
.\backend\.venv\Scripts\Activate.ps1   # if a venv exists
python tools/reset_qa_env.py
```

The script:

- Checks that port 8000 is not in use (ensuring uvicorn is not running).
- Backs up `backend/infinitywindow.db` and `backend/chroma_data/` with timestamps.
- Deletes the active DB and Chroma data so they will be recreated cleanly next run.

After running:

- Start the backend and frontend again (see sections above).
- Run `qa/run_smoke.py` to verify core behavior.

---

## 5. Running the QA smoke suite

From `C:\InfinityWindow` or `C:\InfinityWindow_QA` (with backend venv active):

```powershell
python -m qa.run_smoke
```

This runs:

- Message search probe.
- Tasks auto‑loop probe.
- Mode routing probe.

If any probe fails:

- Check logs for specifics.
- Cross‑reference `docs/TEST_PLAN.md` and `docs/TEST_REPORT_2025-12-02.md`.
- Open the relevant backend modules (`chroma_store.py`, `openai_client.py`, `app/api/main.py`) to investigate.

---

## 6. Running Playwright UI tests

From `C:\InfinityWindow\frontend` (or QA equivalent):

1. Install dependencies (first run):

```powershell
npm install
npx playwright install
```

2. Start the dev server in one terminal:

```powershell
npm run dev -- --host 127.0.0.1 --port 5174
```

3. Run tests in another terminal:

```powershell
npm run test:e2e
```

Playwright specs currently cover:

- Right‑column tabs.
- Files tab (browsing + editor).
- Notes + Memory tabs.

---

## 7. Troubleshooting common issues

- **SQLite “no such column” errors**:
  - Usually due to schema changes without DB migration.
  - Fix: stop backend, back up and delete `backend/infinitywindow.db`, restart backend to recreate schema (or use `reset_qa_env.py` in QA).

- **Chroma file‑lock errors when deleting `chroma_data`**:
  - Cause: backend still running and holding file handles.
  - Fix: stop uvicorn first, then delete or use reset script.

- **PowerShell JSON / quoting errors with `Invoke-RestMethod`**:
  - Use here‑strings (`@' ... '@`) for JSON payloads to avoid escaping hell.

- **Playwright connection refused (`ERR_CONNECTION_REFUSED`)**:
  - Ensure `npm run dev` is running.
  - Ensure Playwright `baseURL` (`playwright.config.ts`) matches the dev server port.

---

## 8. Runbook for a full QA sweep

1. **Prepare QA environment**:
   - Ensure `C:\InfinityWindow_QA` is synced with main repo version.
   - Optionally run `tools/reset_qa_env.py` in QA.

2. **Start backend & frontend in QA**.

3. **Run backend smoke suite**:
   - `python -m qa.run_smoke`.

4. **Run `make ci` in QA**:
   - `make ci` from repo root.

5. **Run Playwright UI tests**:
   - As described above.

6. **Execute selected manual tests** from `docs/TEST_PLAN.md`:
   - Especially for areas changed since the last window.

7. **Document results**:
   - Use `docs/TEST_REPORT_TEMPLATE.md` to capture a new report.
   - Update `docs/PROGRESS.md` and `docs/TODO_CHECKLIST.md` with outcomes and follow‑ups.

This runbook should be treated as the operational backbone for keeping InfinityWindow healthy across windows and environments.


