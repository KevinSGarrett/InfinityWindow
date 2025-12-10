# InfinityWindow – Developer Workflow & GitHub

Repo rules and branching discipline for the recovery baseline (`C:\InfinityWindow_Recovery`). Use this as the contract for Git/GitHub, multi-agent work, and local setup.

## Recovery repo rules
- Active dev repo: `C:\InfinityWindow_Recovery`.
- Read-only backup snapshot: `C:\InfinityWindow_Backup\019` (never edit).
- Legacy/quarantined repo: `C:\InfinityWindow` (historical reference only, do not edit or branch from it).
- Agents never modify the backup or the quarantined repo; all work happens in `C:\InfinityWindow_Recovery`.

## Branching & agent protocol
- main stays clean; feature branches only. Start from up-to-date main before work.
- No “mega hygiene” tasks: do not switch branches mid-task, merge multiple branches, or attempt repo-wide conflict resolutions autonomously.
- Branch ownership:
  - Agent #A: backend/QA + GitHub wiring for one feature at a time.
  - Agent #B: frontend/Playwright for scoped UI features.
  - Agent #C: docs/CRM/alignment (this file and other docs).
- Parallel agents are allowed only when branches avoid the same core files (e.g., `backend/app/api/main.py`, `frontend/src/App.tsx`, `docs/ISSUES_LOG.md`) or merge order is explicitly managed.

## Cursor workflow (user + agents)
- The user pastes prompts for Agent A/B/C into Cursor.
- Cursor/agent runs tests and handles git/PR for that branch. User does not run git commands unless explicitly agreed.
- Do not run prompts that mix “edit files” with “fix all git conflicts”; conflict resolution is a separate, manual step if needed.

## Typical loop per branch
1) `git fetch origin && git switch main && git pull`.
2) `git switch -c <branch>` (e.g., `docs/agent-c-recovery-workflow`).
3) Make focused changes (one feature/fix per branch).
4) Run relevant tests before push (see below).
5) `git status` / `git diff`, then `git add -p` and `git commit -m "<prefix>: <summary>"` (use `docs`/`test`/`fix`/`chore`).
6) `git push origin <branch>` and open a PR against `main`.

## Backend (FastAPI)
From repo root:
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.api.main:app --reload
```

## Frontend (React + Vite)
From repo root:
```powershell
cd frontend
npm install
npm run dev
```
Open the Vite URL (usually `http://127.0.0.1:5173/`) while the backend runs.

## Tests (run before pushing)
- Recommended quick check: `python -m pytest qa/tests_api -q --disable-warnings`.
- Stubbed CI equivalent (matches GitHub Actions):
```powershell
$env:LLM_MODE="stub"; $env:VECTORSTORE_MODE="stub"; make ci
```
- Frontend build: `npm run build --prefix frontend`.
- Playwright (when UI changes):
```powershell
npm run dev -- --host 127.0.0.1 --port 5173
npm run test:e2e
```

## Git & GitHub workflow summary
- Remote: `origin` → `https://github.com/KevinSGarrett/InfinityWindow` (primary branch `main`).
- Keep branches green: run API tests (and UI build/Playwright if the UI changed) before push/PR.
- Prefer short-lived branches; never merge directly to `main` if tests are failing.

For architecture/usage see `USER_MANUAL.md`, `SYSTEM_OVERVIEW.md`, and `SYSTEM_MATRIX.md`; for docs/QA alignment see `REQUIREMENTS_CRM.md`, `TODO_CHECKLIST.md`, and `PROGRESS.md` (Recovery 2025-12-10).
