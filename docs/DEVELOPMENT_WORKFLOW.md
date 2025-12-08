# InfinityWindow – Developer Workflow & GitHub

How to run the stack locally, execute the main tests, and keep Git/GitHub tidy. For full usage steps see `USER_MANUAL.md`; for architecture see `SYSTEM_OVERVIEW.md` and `SYSTEM_MATRIX.md`.

## Prerequisites
- Windows 10/11; PowerShell or cmd.
- Python 3.11+ with `python` on PATH (use a virtual env per project).
- Node.js (current LTS) with `npm`.
- Git; optional: Make (for QA copy), Playwright (for UI tests).

## Backend (FastAPI)
- From repo root:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

- Add `backend/.env` with `OPENAI_API_KEY=...` (and any `OPENAI_MODEL_*` overrides if needed).
- Run the app (defaults to `http://127.0.0.1:8000`):

```powershell
uvicorn app.api.main:app --reload
```

## Frontend (React + Vite)
- From repo root:

```powershell
cd frontend
npm install
npm run dev
```

- Open the URL printed by Vite (usually `http://127.0.0.1:5173/`) while the backend is running.

## Tests (run before pushing)
- API suite (with backend venv active, from repo root):

```powershell
$env:PYTHONPATH=".;backend"
python -m pytest qa/tests_api/test_tasks_automation_audit.py
# or full suite
python -m pytest qa/tests_api
```

- Frontend checks:

```powershell
cd frontend
npm run build              # typecheck + build
# Playwright (optional; keep dev server up in another terminal)
npm run dev -- --host 127.0.0.1 --port 5173
npm run test:e2e
```

## Git & GitHub workflow
- Remote: `origin` → `https://github.com/KevinSGarrett/InfinityWindow` (primary branch `main`).
- Keep `main` green: run the API tests (and UI build/Playwright if you changed the UI) before pushing.
- Branching:
  - Prefer short-lived branches like `feature/<topic>` or `bugfix/<topic>` merged into `main` after tests.
  - If committing directly to `main`, keep changes small and tested.
- Typical loop:
  - `git status` / `git diff` (review).
  - `git add -p` (or specific files).
  - `git commit -m "feat: <summary>"` (Conventional Commit prefixes encouraged: `feat`, `fix`, `docs`, `test`, `refactor`).
  - `git push origin <branch>` (or `git push origin main` when ready).

Quick pointers: use `DEV_GUIDE.md` for code structure and conventions, `OPERATIONS_RUNBOOK.md` for QA/ops routines, and `TEST_PLAN.md` for detailed test cases.

