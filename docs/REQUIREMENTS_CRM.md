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

### Retrieval Phase 1 — Status: Partial
- Scope: message/doc/memory retrieval in `/chat`, debug retrieval context endpoints, and telemetry. `GET /conversations/{id}/debug/retrieval_context` returns **404 for missing conversations by design**.
- Evidence: `API_REFERENCE_UPDATED.md`, `SYSTEM_OVERVIEW.md`, retrieval Phase 1 noted as Partial in TODO/PROGRESS.

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

