# InfinityWindow Agent Guide

This guide is for **AI agents** (like this one) operating in the InfinityWindow repo.

It explains:

- What the system does at a high level.
- Where to read before making changes.
- How to apply changes safely (especially on Windows).
- How to keep documentation and QA artifacts in sync.

---

## 1. Before you edit anything

1. **Load core context:**
   - `README.md` (root) – quick overview and repo layout.
   - `docs/README.md` – docs index.
   - `docs/HYDRATION_2025-12-02.md` – high‑signal system briefing.
   - `docs/SYSTEM_MATRIX.md` – maps features ↔ files ↔ endpoints ↔ tests.
   - `docs/PROGRESS.md` – what has been implemented and which window you’re in.

2. **Understand user‑specific rules:**
   - Safe‑write paths: prefer `docs/**`, `tests/**`, `tools/**`, and project plugin directories.
   - Don’t create random scratch/demo files outside explicitly allowed zones.
   - At the end of a window, the user expects `make ci` to be run in the QA copy and summarized in `docs/PROGRESS.md`.

3. **Confirm which workspace you are in:**
   - Primary repo: `C:\InfinityWindow`.
   - QA copy: `C:\InfinityWindow_QA`.
   - Never run destructive operations (DB/chroma reset) on the wrong one.

---

## 2. Safe operations

### 2.1 Editing files

- Prefer using the provided patch/edit tools rather than hand‑crafted shell commands to modify files.
- Keep patches **small and focused**:
  - Limit each patch to a logical change (e.g., one feature or one bugfix).
  - Avoid interleaving unrelated refactors and feature work.

### 2.2 Where to write

- **Generally safe:**
  - `docs/**` – documentation (this is the main surface for descriptive work).
  - `tests/**` and `frontend/tests/**` – QA and Playwright tests.
  - `qa/**` – backend smoke test utilities.
  - `tools/**` – helper scripts (e.g., `reset_qa_env.py`) when modifications are clearly needed.

- **Be cautious:**
  - `backend/app/**` – core behavior; changes should be deliberate and tested.
  - `frontend/src/**` – UI behavior; changes should be paired with visual or Playwright checks.

### 2.3 Dangerous operations to avoid

- Deleting or recreating `backend/infinitywindow.db` or `backend/chroma_data/` in the primary repo unless explicitly instructed.
- Running shell commands that:
  - Stop system services.
  - Kill arbitrary processes.
  - Modify user‑level configuration outside this repo.

If a destructive operation truly is needed (e.g. resetting QA DB/Chroma), prefer the scripted helper (`tools/reset_qa_env.py`) on the **QA copy**.

---

## 3. Testing expectations

Whenever you make meaningful code changes:

- **Backend‑affecting changes:**

  - Run the smoke suite:

    ```powershell
    cd C:\InfinityWindow
    # ensure backend venv is active
    python -m qa.run_smoke
    ```

  - Check that:
    - Message search probe passes.
    - Tasks auto‑loop probe passes.
    - Mode routing probe passes.

- **Frontend / UI‑affecting changes:**

  - Build and run UI tests from `frontend/`:

    ```powershell
    npm run build
    npx playwright install   # first time only
    npm run dev -- --port 5174   # separate terminal
    npm run test:e2e             # Playwright tests
    ```

- **CI in QA copy:**

  - When closing a window, run:

    ```powershell
    cd C:\InfinityWindow_QA
    make ci
    ```

  - Summarize results in `docs/PROGRESS.md` under the CI log section.

---

## 4. Keeping docs in sync

When you:

- Add a feature.
- Fix a regression.
- Change behavior that a user relied on.

You should:

1. Update `docs/PROGRESS.md`:
   - Record what changed in the current window.
2. Keep plans/CRM/TODO/PROGRESS aligned:
   - If shipped behavior diverges from `Project_Plan_003_UPDATED.txt` or `Updated_Project_Plan_2_*.txt`, update the relevant plan (when the spec needs to change) and sync `docs/REQUIREMENTS_CRM.md`, `docs/TODO_CHECKLIST.md`, and `docs/PROGRESS.md`.
   - Log a doc issue in `docs/ISSUES_LOG.md` when you discover mismatches.
3. Update `docs/TODO_CHECKLIST.md`:
   - Mark items `[x]` when complete or adjust status.
4. Update `docs/SYSTEM_MATRIX.md`:
   - Add new endpoints/models/components to the relevant tables.
5. If behavior touches configuration, API, or security:
   - Update `docs/API_REFERENCE.md`, `docs/API_REFERENCE_UPDATED.md`, `docs/CONFIG_ENV.md`, and/or `docs/SECURITY_PRIVACY.md` as needed.
6. When you add or change APIs or fix defects uncovered in QA:
   - Log the issue and resolution in `docs/ISSUES_LOG.md`.
   - Keep `docs/API_REFERENCE_UPDATED.md` fully aligned with the backend so QA can rely on it for request shapes and new endpoints (e.g., task delete/overview, ingestion jobs).

Documentation and code should tell the same story; avoid leaving them out of sync.

---

## 5. How to reason about changes

- **Prefer incremental improvements**:
  - If a user asks for a large refactor, consider implementing it in stages.
  - After each stage, ensure the system is stable and tests pass.

- **Respect user feedback about UX**:
  - The right‑column layout has been iterated on multiple times; any major layout change should be:
    - Justified.
    - Small and reversible.
    - Backed by tests (`right-column.spec.ts`).

- **Align with the test plan**:
  - When in doubt about behavior, check `docs/TEST_PLAN.md`:
    - It defines what “correct” looks like for each feature.

---

## 6. Useful references

- **High‑level understanding**:
  - `docs/SYSTEM_OVERVIEW.md`
  - `docs/HYDRATION_2025-12-02.md`
  - `docs/SYSTEM_MATRIX.md`

- **Behavior & roadmap**:
  - `docs/PROGRESS.md`
  - `docs/TODO_CHECKLIST.md`

- **Operations & QA**:
  - `docs/TEST_PLAN.md`
  - `docs/TEST_REPORT_*.md`
  - `docs/OPERATIONS_RUNBOOK.md` (once filled)

- **Future Autopilot & blueprint design**:
  - `docs/AUTOPILOT_PLAN.md`
  - `docs/AUTOPILOT_LEARNING.md`
  - `docs/AUTOPILOT_LIMITATIONS.md`
  - `docs/MODEL_MATRIX.md`

Use this guide as your behavioral contract when acting in this repository. When you’re unsure, prefer to read more (code + docs) and make smaller, reversible changes. For Autopilot work specifically, always respect the additional safety constraints in `AUTOPILOT_LIMITATIONS.md` and keep docs/QA artifacts in sync as new capabilities are implemented.

