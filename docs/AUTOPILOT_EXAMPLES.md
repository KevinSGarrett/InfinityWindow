# InfinityWindow Autopilot – Usage Scenarios (Design Examples)

Status: Design only – not implemented yet. Current automation in production is limited to task upkeep/hooks after `/chat`; Autopilot phases (Manager/Workers/Runs/Blueprint execution) are not shipped. For live endpoints and behaviors, see `docs/API_REFERENCE_UPDATED.md` (sections 1–9) and the planned APIs in section 11; keep status in sync with `docs/PROGRESS.md` and `docs/TODO_CHECKLIST.md`.

This document captures concrete, end‑to‑end usage examples for the future Autopilot system, based on  
`Updated_Project_Plans/Updated_Project_Plan_2_AUTOPILOT_EXAMPLES.txt`. The workflows here are illustrative only and are not wired to the current UI/backend yet. When implementing these flows, use `AUTOPILOT_IMPLEMENTATION_CHECKLIST.md` to track progress.

---

## 1. Bootstrapping a Project from a Huge Blueprint

**Goal:** Turn a ~500k‑word project spec into a living plan, then let Autopilot start building the MVP in “suggest” / “semi_auto” mode.

### Preconditions

- A new InfinityWindow project exists with:
  - `local_root_path` pointing at the target repo (empty or skeleton).
  - Backend and frontend running.
  - Core docs like `API_REFERENCE` and `DEV_GUIDE` available.
- The large blueprint spec is available as a text/Markdown file.
- Autopilot Phases 1–4 are implemented (Blueprint, PlanNodes, Runs, Manager/Workers).

### Flow (Once Implemented)

1. **Upload and ingest the blueprint**
   - Docs tab → “Ingest text doc”.
   - Name: “Master Blueprint v1”.
   - Paste or upload the full spec.

2. **Create Blueprint and generate Plan**
   - Tasks tab → Blueprint/Plan section.
   - “Create blueprint from doc” → select “Master Blueprint v1”.
   - Click “Generate plan” to create PlanNodes (phases → epics → features → stories).

3. **Decompose features into tasks**
   - Expand “Phase 1 – MVP” → pick an epic (e.g. “Auth & Onboarding”).
   - For each feature node (e.g. “User registration”):
     - Click “Generate tasks”.
     - Review/edit task titles, acceptance criteria, risk/priority.

4. **Set up Autopilot**
   - In project header or Notes tab:
     - Set autonomy: `suggest` (first runs).
     - Set active phase: “Phase 1 – MVP”.
     - Update project instructions with:
       - Tech stack.
       - Non‑negotiable constraints.
       - QA expectations.

5. **Tell the Manager to start**
   - In chat:
     - “Use the Master Blueprint v1 to build the MVP. Start with the auth phase.”
   - Intent classifier tags this as `START_BUILD`.
   - Manager:
     - Confirms active phase.
     - Picks top unblocked task(s) under “Auth & Onboarding”.
     - Creates planned `ExecutionRun`s.

6. **Review proposed runs**
   - Runs tab:
     - See Run #1: “Implement user registration API” (run_type=implement_feature).
     - Inspect its planned steps (plan, read files, write implementation, add tests, run tests).
     - Approve the run in suggest mode to allow workers to begin.

7. **Iterate & increase autonomy**
   - Let Autopilot complete one or two small features.
   - Once confident:
     - Switch autonomy to `semi_auto`, allowing safe steps (reads/tests) to run automatically.

Result: the blueprint becomes a concrete plan + tasks; Autopilot starts executing features while keeping you in the loop.

---

## 2. Implementing a Single Feature in Semi‑Auto Mode

**Goal:** Autopilot implements a specific feature end‑to‑end while you approve file edits and commands.

### Setup

- Blueprint and PlanNodes exist.
- Tasks have been generated for feature “User registration”.
- Autonomy is set to `semi_auto`.

### Flow

1. **Pick the feature**
   - In Plan tree, select PlanNode “User registration”.
   - Confirm tasks:
     - “Design DB schema for users”.
     - “Implement /api/register”.
     - “Write tests for registration”.

2. **Ask Manager to focus**
   - In chat:
     - “Start work on the ‘User registration API’ feature and get it to passing tests in semi_auto mode.”
   - Manager:
     - Validates tasks for that PlanNode.
     - Creates runs for schema design and endpoint implementation, respecting dependencies.

3. **Watch runs**

   - Runs panel:
     - Run #3: “Design user schema”.
     - Run #4: “Implement registration endpoint”.

4. **Approve edits**
   - When a run hits a `write_file` step:
     - Review diffs for relevant files (e.g., models/user.py, app/api/auth.py).
     - Check alignment badges against Plan/Decisions.
     - Click “Approve step”.

5. **Tests**
   - Test worker runs tests (e.g., `pytest` subset).
   - On failure:
     - Autopilot loops: read failures → propose code/test edits → re‑run tests.
     - You approve code edits as needed.

6. **Completion**
   - When tests are green:
     - Run status → `completed`.
     - Linked tasks are marked `done`.
     - Manager updates snapshot: “User registration API implemented and tested”.

---

## 3. “CEO Mode” – Non‑Developer Steering

**Goal:** A non‑technical user guides a multi‑week project primarily through chat; Autopilot does implementation inside guardrails.

### Pattern

1. **High‑level instructions**
   - CEO sends broad directives:
     - “This week, focus on payment flows.”
     - “Deprioritize marketing site work for now.”
     - “Once auth and billing are done, we’ll think about reporting.”

2. **Manager interpretation**
   - Interprets these as:
     - Updates to active phase.
     - Re‑prioritization of PlanNodes and tasks.
   - Chooses tasks/runs that reflect these priorities.

3. **Human interaction points**
   - CEO:
     - Approves or rejects diffs conceptually (“Yes, that’s how I want payment retries to work.”).
     - Asks Manager:
       - “Explain what changed in the last 3 runs in simple terms.”
       - “Summarize what we got done this week.”

4. **Snapshots for sanity**
   - Project Snapshot doc is the CEO’s status report:
     - Goals, completed work, risks, and next steps.
   - CEO can ask:
     - “If we need to ship an MVP in 2 weeks, what should we drop?”
     - Manager suggests PlanNodes to de‑scope and tasks to defer.

The CEO does not need to know which worker is doing what; Autopilot exposes status and decisions in human‑friendly terms.

---

## 4. Handling a Failing Run Safely

**Goal:** Show how Autopilot fails safely and how you recover when a run goes wrong.

### Scenario

- Autopilot is refactoring a component.
- A run introduces failing tests that the worker cannot fix automatically.

### Flow

1. **Failure visible in Runs panel**
   - Run #9 status → `failed`.
   - Last step has:
     - `status="failed"`.
     - `error_message` with traceback or test failures.
   - Runs panel highlights the run in red.

2. **Autopilot behavior**
   - Manager:
     - Stops advancing this run.
     - Does not start new dependent tasks.
     - Posts a summary to chat:
       - E.g., “Refactor run #9 failed while updating payment handler X. Tests Y and Z are failing with [reason].”

3. **Human options**
   - Inspect diffs and failing steps.
   - Ask:
     - “Explain the failure in non‑technical terms.”
     - “Suggest how to fix this without changing behavior.”
   - Decide:
     - **Fix & continue**:
       - Approve minimal fix patch.
       - Click “Retry step” or “Continue run”.
     - **Roll back**:
       - Click “Revert run”.
       - All files touched by run #9 revert to their pre‑run state.
       - Manager logs a Decision: “Refactor X aborted; design needs revisiting.”

Autopilot is allowed to fail but must fail in an **inspectable and reversible** way, not silently corrupt the project.

---

## 5. Updating the Blueprint Mid‑Project

**Goal:** Adjust the plan when requirements change, without losing prior work.

### Flow

1. **Ingest new blueprint version**
   - In Docs:
     - Ingest “Master Blueprint v2”.
   - In Tasks / Blueprint section:
     - Create a new Blueprint linked to v2.
     - Run “Generate plan” for v2.

2. **Compare v1 and v2**
   - Use “Compare to parent” or a dedicated UI:
     - Mark changed PlanNodes.
     - Attach `change_note`s.

3. **Tell Manager to reconcile**
   - In chat:
     - “We have a new blueprint version. Update the plan and tasks so we match v2, but keep already‑implemented features unless they explicitly changed.”
   - Manager:
     - Uses `BlueprintDiff` to classify nodes as unchanged/modified/added/removed.
     - Creates new tasks where needed.
     - Marks obsolete tasks appropriately.

4. **Autopilot resumes**
   - Active phase may remain “Phase 1 – MVP”.
   - Manager picks new tasks based on updated PlanNodes.

---

## 6. Using Autopilot Just for Testing & QA

**Goal:** Use Autopilot as a smart test runner and fixer, while continuing to code manually.

### Flow

1. **Set Autonomy to `semi_auto`**
   - Instructions:
     - Emphasize: “Autopilot should not implement new features by itself.”
     - Focus on running tests and fixing small bugs.

2. **Manual coding**
   - You edit code in Files tab or local editor, commit as usual.

3. **Ask Autopilot to handle tests**
   - In chat:
     - “Run tests for backend and help me fix any failures.”
   - Manager:
     - Starts a `run_tests_only` run.

4. **Test worker behavior**
   - Runs `pytest` or project‑appropriate commands.
   - Summarizes failures.
   - Proposes targeted fixes.

5. **Human review**
   - You:
     - Review and approve/reject code patches.
     - Re‑run tests as needed.

Outcome: InfinityWindow acts as a **smart QA assistant** even if you don’t trust it with full feature implementation yet.

---

## 7. How These Examples Fit into the System

These scenarios sit on top of:

- Projects with conversations, tasks, docs, memory, files, terminal, usage.
- Autopilot plan and learning layer (`docs/AUTOPILOT_PLAN.md`, `docs/AUTOPILOT_LEARNING.md`).
- Model configuration (`docs/MODEL_MATRIX.md`, `docs/CONFIG_ENV.md`).
- Operations & QA flows (`docs/OPERATIONS_RUNBOOK.md`, `qa/run_smoke.py`, `docs/TEST_PLAN.md`).

As Autopilot is implemented, the UI and API should be shaped so that a human can easily follow these patterns without needing to know every internal detail.


