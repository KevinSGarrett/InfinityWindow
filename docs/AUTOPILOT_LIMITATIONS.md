# InfinityWindow Autopilot – Scope, Limits & Guardrails (Design)

Status: Design only – not implemented yet. Current shipped automation is limited to task upkeep/hooks after `/chat`; Manager/Workers/ExecutionRuns are not live. For planned APIs, see `docs/API_REFERENCE_UPDATED.md` section 11 and keep this file aligned with `docs/PROGRESS.md` and `docs/TODO_CHECKLIST.md`.

This document distills the Autopilot limitations and safety contract from  
`Updated_Project_Plans/Updated_Project_Plan_2_AUTOPILOT_LIMITATIONS.txt`. It describes what Autopilot **will** and **will not** be allowed to do once the Manager/Workers/ExecutionRuns are built.

---

## 1. Scope & Mental Model

Autopilot is designed to behave like a **careful project manager plus dev team** working inside a single InfinityWindow project:

- A **Manager agent** that:
  - Reads Blueprint/Plan/Tasks/Decisions/Snapshot for one project.
  - Chooses what to work on next.
  - Starts and advances `ExecutionRun`s.
- One or more **Worker agents** that:
  - Read/write files under the project’s `local_root_path`.
  - Run safe terminal commands and tests.
  - Update docs and tasks.

It is **not** a general‑purpose automation daemon:

- It does **not** control your whole machine.
- It does **not** browse the broader internet.
- It stays within the InfinityWindow project boundaries.

---

## 2. Hard Technical Limits

### 2.1 Context & token limits

- Each LLM call has a finite context window.
- Projects can have:
  - Huge blueprints (hundreds of thousands of words).
  - Large repos (thousands of files).
  - Long conversations (months of history).
- Autopilot never loads “everything at once”:
  - Works on chunked views of docs and code.
  - Relies on search, summaries, snapshots, and PlanNodes.
  - Can **miss** details buried in rarely‑referenced places.

Design implications:

- Important constraints must be surfaced in:
  - Project instructions (Notes tab).
  - Decisions.
  - Memory items.
  - Blueprint/Plan hierarchy.

### 2.2 Embedding & ingestion limits

- Repo and blueprint ingestion are **batched** (Phase T) to respect provider limits (e.g., ~300k tokens per embeddings request).
- Very large repos/specs may require multiple ingestion passes.
- Ingestion may skip:
  - Binary files.
  - Extremely large individual files.
  - Files excluded by globs.
- Autopilot can only reason over what has been successfully ingested and indexed.

### 2.3 Single‑project scope

- Filesystem and terminal tools are restricted to a project’s `local_root_path`.
- Autopilot **cannot**:
  - Touch files outside that root.
  - Run commands outside that root.
  - Work across multiple projects in a single run.

To automate across multiple repos, you must create multiple projects and coordinate manually.

### 2.4 No background daemons (initially)

- Autopilot advances via `POST /projects/{id}/autopilot_tick`, called by the frontend when a project is open.
- When:
  - The UI is closed, or
  - The user switches projects, or
  - The server is stopped,
  - Autopilot is idle – no background jobs run.

This keeps activity anchored to a visible session.

---

## 3. Safety & Guardrails

### 3.1 Filesystem safety

- All paths are normalized and checked against `local_root_path`.
- Attempts to escape (e.g., `..`, absolute paths, other drives) are rejected.
- File edits are always:
  - Logged as `ExecutionStep` records.
  - Linked to an `ExecutionRun`.
  - Associated with pre‑ and post‑content so they can be diffed and rolled back.

### 3.2 Terminal safety

- Autopilot respects a **command allowlist**:
  - Auto‑execution is limited to clearly safe commands, such as:
    - `pytest ...`
    - `python -m pytest`
    - `npm test`
    - `npm run build`
    - `npm run lint`
    - `python -m qa.run_smoke`
- Forbidden (never auto‑run):
  - `rm`, `del`, `format`, `shutdown`, `reboot`, `git push`, `git reset`, etc.
- These commands can still be run manually by humans in the Terminal tab;
  Autopilot will not execute them on its own.

### 3.3 Approval gates

Depending on `Project.autonomy_mode`:

- `off`
  - Manager does nothing automatically.
- `suggest`
  - Manager proposes runs/steps; **all** file writes and commands require approval.
- `semi_auto`
  - Safe reads/search/tests may auto‑run.
  - Writes and unsafe commands require approval.
- `full_auto`
  - Autopilot may auto‑run file edits and safe commands within allowlist.
  - Still **never** runs forbidden commands.
  - All writes maintain rollback data so the entire run can be reverted.

Humans retain final control over critical changes.

---

## 4. Behavioral Limitations

### 4.1 Autopilot depends on a good plan

ManagerAgent is only as good as the plan:

- If the blueprint is incomplete or vague, PlanNodes and tasks will be incomplete or vague.
- If tasks lack acceptance criteria, workers may implement the wrong thing.
- If decisions are not captured, Autopilot may:
  - Repeat past debates.
  - Undo or contradict earlier choices.

Autopilot does not magically infer your true intent from one sentence.  
It amplifies whatever is encoded in:

- Blueprint / Plan hierarchy.
- Tasks and their metadata.
- Instructions / Decisions / Memory.

### 4.2 Tests are just another artifact

Autopilot treats tests as:

- Files it can read, write, and run.
- Primary signal for “are we done?” for a given run.

It cannot guarantee:

- That tests exist for a behavior.
- That tests are themselves correct.
- That passing tests mean the feature is production‑ready.

If tests are missing or weak, full‑auto behavior is dangerous.  
Humans must:

- Seed at least minimal tests.
- Review test diffs for dangerous changes.

### 4.3 Non‑determinism & drift

- LLMs are probabilistic; two runs may produce slightly different plans or code.
- Manager heuristics may change as the project evolves.
- A long series of autopilot changes can drift from the original blueprint if:
  - Requirements change but blueprint/plan aren’t updated.
  - Humans approve “quick hacks” that contradict earlier decisions.

InfinityWindow mitigates this via:

- Conversation summaries.
- Project snapshots.
- Decision log.
- PlanNode/task linkage.

But cannot fully guarantee the system never goes off‑track.  
Humans must occasionally step back, review snapshot/plan, and realign.

---

## 5. Operational Expectations (What Humans Still Do)

Even in full‑auto mode, the “CEO”/operator is responsible for:

- **Initial project setup**
  - Correct `local_root_path`.
  - Required env vars, secrets, API keys.
  - Basic tests and CI wiring.
- **Blueprint quality**
  - Uploading a good blueprint (or iterating it).
  - Approving generated PlanNodes and tasks.
- **Autonomy settings**
  - Choosing `off`/`suggest`/`semi_auto`/`full_auto` per project.
  - Adjusting settings as trust grows.
- **Reviewing diffs & commands**
  - Spot‑checking code changes.
  - Reviewing risky commands.
  - Using “Revert run” when needed.
- **Higher‑level QA**
  - Running `qa/run_smoke.py`.
  - `npm run build` + Playwright tests.
  - Following `docs/TEST_PLAN.md` for major releases.

Autopilot is a **force multiplier**, not a replacement for engineering judgment.

---

## 6. Risks & gating (rollout plan)

- Autopilot remains **off by default** until phases ship; start in `suggest`/`semi_auto` with explicit approvals.
- Respect the command allowlist and filesystem guardrails before enabling any auto-execution; extend the allowlist only with targeted tests and QA evidence.
- Keep `/projects/{id}/autopilot_tick` behind visible UI controls and surface “waiting for approval” states clearly before any writes or unsafe commands run.
- Align every rollout step with `docs/AUTOPILOT_PLAN.md`, `docs/AUTOPILOT_LEARNING.md`, and `docs/MODEL_MATRIX.md` so model choices, safety gates, and learning hooks stay consistent.

---

## 7. Non‑Goals

Autopilot is **not** intended to:

- Manage multiple disjoint projects in one brain.
- Perform arbitrary internet automation (scraping, logging into websites, etc.).
- Replace CI/deployment pipelines.
- Guarantee correctness, security, or compliance.
- Operate unattended for weeks without human review.
- Self‑modify InfinityWindow’s own core logic without explicit human intent.

If you want any of these, treat them as **separate projects** layered on top of InfinityWindow, not hidden Autopilot features.

---

## 8. Keeping Limitations Up to Date

Whenever Autopilot’s capabilities change, update:

- `docs/AUTOPILOT_LIMITATIONS.md` – this contract.
- `docs/SYSTEM_MATRIX.md` – models/endpoints/UI surfaces.
- `docs/AGENT_GUIDE.md` – safe operations for AI agents and workers.
- `docs/SECURITY_PRIVACY.md` – any new security implications.

Treat this file as the **source of truth** for what Autopilot is allowed to do.


