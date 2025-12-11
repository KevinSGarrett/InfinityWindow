# InfinityWindow Requirements & CRM Status (Recovery Baseline)

Canonical repos and scope:
- Active development repo: `C:\InfinityWindow_Recovery` (only writable workspace).
- Read-only backup snapshot: `C:\InfinityWindow_Backup\019`.
- Legacy/quarantined repo: `C:\InfinityWindow` (historical reference only; do not edit).

Status legend: **Shipped** (implemented in this repo), **Partial** (works but needs polish/validation), **Future** (design-only / not present here).

## Current requirement clusters
- Core workspace (projects, conversations, chat, search): **Shipped**. FastAPI backend + React UI support projects, conversations, chat modes, search over messages/docs/memory.
- Tasks & automation: **Partial**. Tasks CRUD, auto-add/auto-complete/dedupe, and context-aware prompt assembly (`PROJECT_CONTEXT` built from instructions + pinned note/sprint focus + project goal + high-priority tasks) with telemetry are present; Usage tab surfaces a hint when context is available. Priority/dependency intelligence and long-horizon tuning remain future.
- Retrieval/context shaping: **Partial**. Env-driven `RetrievalProfile` (messages/docs/memory/tasks K) preserves prior defaults, feeds chat/search/task upkeep, and is exposed via `/debug/retrieval_config` plus a read-only summary in the Usage tab. Telemetry-driven tuning, long-window analytics, and multi-strategy profiles are future.
- Docs & ingestion/search: **Shipped**. Text and repo ingestion with `IngestionJob` progress, hash skip, cancel/history; search across docs/messages/memory. Blueprint/plan ingestion is **Future**.
- Filesystem & terminal safety: **Shipped**. Scoped fs list/read/write and AI edits under project root; terminal runs scoped with `check=True` and a pattern-based injection guard; `local_root_path` validation enforced. Persisted terminal history remains future.
- Notes, decisions, memory: **Shipped**. Project instructions/pinned note, decision log with follow-ups, memory items + retrieval and “Remember this” button.
- Usage & telemetry: **Partial**. Usage records per conversation plus task automation telemetry (including context injection + surfaced high-priority counts) and lightweight charts/filters/exports. Long-window persistence/analytics still **Future**.
- UI workbench (right-column tabs): **Shipped**. Eight-tab layout (Tasks, Docs, Files, Search, Terminal, Usage, Notes, Memory) with refresh-all and keyboard shortcuts.
- QA & safety tooling: **Shipped**. Smoke probes (`qa/run_smoke.py`), ingestion probes, Playwright specs, guarded QA reset script. Continue to validate after recovery.
- Git/GitHub workflow hygiene: **Shipped** (doc’d). main stays clean; feature branches only; agents A/B/C own separate scopes; no branch merging/conflict “mega hygiene.”
- Autopilot / Blueprint / ExecutionRuns: **Future (design-only)**. Kept in docs as roadmap; not implemented in this codebase.
- Export/import/archive flows: **Future (design-only)**. No archive/export/import UI or API in this repo; treat as backlog.

## Recovery notes
- All status above reflects the recovered code in `C:\InfinityWindow_Recovery` dated 2025-12-10.
- Any requirement not visible in this repo (e.g., Autopilot dashboards, Blueprint ingestion, project export/import) is future work and must not be treated as shipped.
- See `docs/TODO_CHECKLIST.md` for prioritized follow-ups and `docs/PROGRESS.md` for dated log entries (including the “Recovery 2025-12-10” note).
# CRM Requirements – Recovery Baseline (C:\InfinityWindow_Recovery)

Source of truth:
- Design: `Project_Plan_003` and files in `Updated_Project_Plans/` (design-only).
- Implementation: recovered code at `C:\InfinityWindow_Recovery` (FastAPI + React).
- Status values match the actual code and tests in this recovery copy.

## Clusters

### Projects & Conversations — Status: Implemented (core)
- Create/list/update projects; `local_root_path` is **required** and must exist.
- Per-project instructions + pinned note; conversations auto-create when missing.
- Conversation folders CRUD + default folder support.
- No archive/delete/restore flows; no `include_archived`; export/import not started.

### Chat & Retrieval — Status: Partial
- `/chat` reuses or creates conversations, stores messages, and calls the stubbed LLM.
- Retrieval embeds user text and surfaces similar messages, docs, and memory items into the system prompt. Retrieval counts (messages/docs/memory/tasks) are governed by an env-driven `RetrievalProfile` that clamps overrides and defaults to the prior 5/5/5/5 behavior.
- Diagnostics: `/debug/retrieval_config` exposes the active profile + source; UI surfaces a read-only retrieval summary in the Usage tab. Quality tuning/persistence remains future.

### Documents & Ingestion — Status: Implemented (core)
- Text doc ingest (`/docs/text`, `/projects/{id}/docs/text`), metadata CRUD, and delete.
- Repo ingestion jobs (`/projects/{id}/ingestion_jobs` + poll/cancel) with Chroma embeddings.
- Semantic search over messages/docs/memory via `/search/*`.

### Tasks / TODO Automation — Status: Partial
- Auto add/complete/dedupe runs after `/chat` and via `/projects/{id}/auto_update_tasks`; automation prompts now include a `PROJECT_CONTEXT` block (instructions, pinned note/sprint focus, project goal/description, high-priority tasks with blocked/not-blocked flags) and telemetry captures context injection + surfaced high-priority counts.
- Task suggestions + approve/dismiss endpoints; audit fields (`auto_confidence`, `auto_last_action`, `auto_notes`) and a Usage-tab hint appears when instructions + pinned note are present.
- Telemetry counters + recent actions via `/debug/telemetry`; task overview endpoint combines tasks + suggestions; QA: `qa/tests_api/test_tasks_automation_prompt_context.py`, `qa/tests_api/test_tasks_automation_audit.py`, Playwright `frontend/tests/tasks-confidence.spec.ts`.

### Memory & Decisions — Status: Implemented
- Memory item CRUD + search; pinned items injected into chat context.
- Decision log CRUD; auto-capture hook after chat.

### Files & AI Edit — Status: Implemented
- Safe filesystem list/read/write scoped to `local_root_path` with traversal/UNC blocking.
- AI file edit endpoint accepts `instruction|instructions`, optional diff/apply flags.

### Terminal — Status: Partial
- `/terminal/run` and scoped `/projects/{id}/terminal/run` execute commands under the project root with a basic injection guard blocking obviously destructive patterns.
- History endpoint returns an empty list; persisted terminal history is future work.

### Usage & Telemetry — Status: Partial
- `/conversations/{id}/usage` returns per-conversation usage records (tokens/model/cost) plus task automation telemetry, including context-aware prompt injection and surfaced high-priority task counts.
- `/debug/telemetry` returns LLM + task + ingestion counters and recent actions; the Usage tab surfaces a subtle hint when context-aware TODO extraction is active (instructions + pinned note present).
- No dashboard persistence, charts, or long-window analytics.

### Autopilot / Blueprint / Export-Import — Status: Not started (design-only)
- Autopilot managers/workers, blueprint/plan graphs, project archive/export/import are not present in this baseline.

## Evidence
- Backend APIs: `backend/app/api/main.py`, `backend/app/api/docs.py`, `backend/app/api/search.py`.
- Tests: `qa/tests_api/test_api_projects.py`, `test_chat_tasks_autopilot.py`, `test_chat_tasks_noisy.py`, `test_tasks_automation_audit.py`, `test_tasks_automation_prompt_context.py`, `test_usage_telemetry_dashboard.py`, `test_ingestion_e2e.py`.
- Frontend: minimal SPA in `frontend/src/App.tsx`; Playwright specs cover basic tabs, telemetry/task surfaces, and context-aware TODO hints (`frontend/tests/tasks-confidence.spec.ts`).
# InfinityWindow – Requirements & CRM

## Source of truth
- Design specs of record: `Project_Plan_003_UPDATED.txt` and `Updated_Project_Plan_2_*.txt` (QA copies). Keep this file aligned with those plans.
- Delivery flow: **Plans → CRM (this doc) → TODO_CHECKLIST / PROGRESS → implementation & tests.**
- Last sync: 2025-12-10 (project archive lifecycle update).

## Requirement clusters

### Project lifecycle & housekeeping — Status: Implemented (core archive)
- Scope: project create/read/update plus **archive via DELETE `/projects/{id}`** (soft delete). Archived projects remain readable, are hidden from `GET /projects` by default, and can be listed with `include_archived=true`. Write operations on archived projects (new chats/ingests/tasks) may be rejected; archived data stays available for audit/usage.
- Backend: FastAPI DELETE now marks projects archived instead of 405; GET `/projects` supports `include_archived`; GET `/projects/{id}` returns archived rows for audit.
- Frontend: Project list exposes an **Archive project** action that calls DELETE `/projects/{id}` and refreshes the list to hide archived entries by default.
- QA/Evidence: API regression for delete/list on archived projects; Playwright project-list archive flow; PROGRESS entry “2025-12-10 – Project lifecycle & archive v1”; docs updated in `USER_MANUAL.md`, `API_REFERENCE.md`, `API_REFERENCE_UPDATED.md`, `SYSTEM_OVERVIEW.md`.
- Future extensions: `[ ]` Permanent purge for archived projects; `[ ]` Bulk archive/unarchive or batch include/exclude controls.

### Enhanced retrieval & context shaping v1 — Status: Partial
- Scope: env-driven `RetrievalProfile` (messages_k/docs_k/memory_k/tasks_k) with caps and defaults matching the prior hard-coded 5s; shared by chat (`app/api/main.py`), search (`app/api/search.py`), and task upkeep.
- Diagnostics: `GET /debug/retrieval_config` returns the active profile + source; UI shows a read-only summary alongside Usage telemetry.
- Evidence: `qa/tests_api/test_retrieval_config.py` (defaults, env overrides, chat/search callsites), `frontend/tests/usage-dashboard.spec.ts` (Usage telemetry/summary rendering). Future: telemetry-driven tuning with real-world data and long-window/strategy profiles.

### Usage dashboard (Phase 3) — Status: Implemented
- Scope: usage records per conversation, charts/filters/exports, telemetry drawer. Phase 3 persistence/long-window analytics remain future work.
- Evidence: `USAGE_TELEMETRY_DASHBOARD.md`, `TODO_CHECKLIST.md`, `PROGRESS.md` (2025-12-13), Playwright dashboard specs, API usage tests.

### Task-aware auto-mode routing v2 — Status: Partial
- Scope: auto-mode heuristics, telemetry, UI override; data-driven refinement still pending.
- Evidence: `USER_MANUAL.md` (§5.3), `PROGRESS.md` (2025-12-10 routing reasons), routing tests/probes.

### Autonomous TODO intelligence — Status: Partial
- Scope: auto add/complete/dedupe with confidence/audit; dependency graphing and richer approval flows pending.
- Evidence: `TODO_CHECKLIST.md`, `PROGRESS.md` (2025-12-14 audit trail), tasks automation tests.

### Autopilot / Blueprint / Learning — Status: Not started (design-only)
- Scope: blueprint ingestion, plan graph, Manager/worker agents, learning layer.
- Evidence: `AUTOPILOT_PLAN.md`, `AUTOPILOT_LEARNING.md`, `Updated_Project_Plan_2_*` design notes.

