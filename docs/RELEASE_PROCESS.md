# InfinityWindow Release Process

This document describes a **lightweight release process** for InfinityWindow.  
“Release” here usually means completing a work “window” and pushing a stable state to `main`.

---

## 1. Versioning model

- InfinityWindow is currently versioned informally by **date and window** (e.g., “2025‑12‑02 window”).
- Over time, you can introduce semantic versions (e.g., `v0.3.0`) and tag them in Git.
- Regardless of scheme, each release should be reflected in:
  - `docs/PROGRESS.md` (what changed in this window).
  - `docs/CHANGELOG.md` (high‑level summary).

---

## 2. Pre-release checklist

Before calling a window “done” or cutting a release:

- **Code state**
  - [ ] `git status` is clean (no unintended changes).
  - [ ] New or modified files are committed with clear messages.

- **Backend / frontend health**
  - [ ] Backend starts cleanly with `uvicorn app.api.main:app --reload`.
  - [ ] Frontend builds successfully (`npm run build`).
  - [ ] Smoke tests pass (`python -m qa.run_smoke`).
  - [ ] Playwright UI tests pass (`npm run test:e2e`) for key flows.

- **QA / CI**
  - [ ] In the QA copy (`C:\InfinityWindow_QA`), `make ci` has been run recently and the result recorded in `docs/PROGRESS.md`.
  - [ ] Any failing tests or issues are either fixed or explicitly captured as open items in `PROGRESS.md` / `TODO_CHECKLIST.md`.

- **Docs**
  - [ ] `docs/SYSTEM_OVERVIEW.md` matches current behavior.
  - [ ] `docs/SYSTEM_MATRIX.md` is updated for new/changed features.
  - [ ] `docs/PROGRESS.md` and `docs/TODO_CHECKLIST.md` reflect what was done and what remains.
  - [ ] `docs/CHANGELOG.md` has an entry summarizing the window.
  - [ ] Any new patterns or constraints are captured in `DEV_GUIDE.md` / `AGENT_GUIDE.md`.

---

## 3. Release steps

1. **Run tests locally**
   - Backend smoke suite:
     ```powershell
     python -m qa.run_smoke
     ```
   - Frontend build:
     ```powershell
     cd frontend
     npm run build
     ```
   - Optional: Playwright E2E tests:
     ```powershell
     npm run dev -- --port 5174   # in one terminal
     npm run test:e2e             # in another
     ```

2. **Run CI in QA copy**
   - From `C:\InfinityWindow_QA`:
     ```powershell
     make ci
     ```
   - Record outcome in `docs/PROGRESS.md` (CI run log).

3. **Finalize documentation**
   - Update:
     - `docs/PROGRESS.md`
     - `docs/TODO_CHECKLIST.md`
     - `docs/CHANGELOG.md`
     - `docs/DECISIONS_LOG.md` (if any global decisions were made)
   - Ensure `docs/SYSTEM_OVERVIEW.md` is still accurate.

4. **Commit and push**
   - In `C:\InfinityWindow`:
     ```powershell
     git status
     git add ...
     git commit -m "Describe the window or release clearly"
     git push
     ```
   - Optionally tag the release:
     ```powershell
     git tag -a v0.3.0 -m "Release description"
     git push origin v0.3.0
     ```

---

## 4. Post-release

- Create or update:
  - Next‑window TODOs in `docs/TODO_CHECKLIST.md`.
  - Any planned items in `docs/PROGRESS.md` under future phases (v3/v4+).
- If needed, reset the QA environment using `tools/reset_qa_env.py` to prepare for the next round of testing.

This process is intentionally lightweight; you can expand it over time with more formal CI/CD steps or external automation, but these basics should keep InfinityWindow’s `main` branch stable and well‑documented.***

