# InfinityWindow Requirements & CRM Status (Recovery Baseline)

Canonical repos and scope:
- Active development repo: `C:\InfinityWindow_Recovery` (only writable workspace).
- Read-only backup snapshot: `C:\InfinityWindow_Backup\019`.
- Legacy/quarantined repo: `C:\InfinityWindow` (historical reference only; do not edit).

Status legend: **Shipped** (implemented in this repo), **Partial** (works but needs polish/validation), **Future** (design-only / not present here).

## Current requirement clusters
- Core workspace (projects, conversations, chat, search): **Shipped**. FastAPI backend + React UI support projects, conversations, chat modes, search over messages/docs/memory.
- Tasks & automation: **Partial**. Tasks CRUD, auto-add/auto-complete/dedupe and telemetry are present. Priority/dependency intelligence, richer approvals, and long-horizon tuning remain future.
- Docs & ingestion/search: **Shipped**. Text and repo ingestion with `IngestionJob` progress, hash skip, cancel/history; search across docs/messages/memory. Blueprint/plan ingestion is **Future**.
- Filesystem & terminal safety: **Shipped**. Scoped fs list/read/write and AI edits under project root; terminal runs scoped with `check=True`; `local_root_path` validation enforced.
- Notes, decisions, memory: **Shipped**. Project instructions/pinned note, decision log with follow-ups, memory items + retrieval and “Remember this” button.
- Usage & telemetry: **Partial**. Usage records per conversation plus task automation telemetry and lightweight charts/filters/exports. Long-window persistence/analytics still **Future**.
- UI workbench (right-column tabs): **Shipped**. Eight-tab layout (Tasks, Docs, Files, Search, Terminal, Usage, Notes, Memory) with refresh-all and keyboard shortcuts.
- QA & safety tooling: **Shipped**. Smoke probes (`qa/run_smoke.py`), ingestion probes, Playwright specs, guarded QA reset script. Continue to validate after recovery.
- Git/GitHub workflow hygiene: **Shipped** (doc’d). main stays clean; feature branches only; agents A/B/C own separate scopes; no branch merging/conflict “mega hygiene.”
- Autopilot / Blueprint / ExecutionRuns: **Future (design-only)**. Kept in docs as roadmap; not implemented in this codebase.
- Export/import/archive flows: **Future (design-only)**. No archive/export/import UI or API in this repo; treat as backlog.

## Recovery notes
- All status above reflects the recovered code in `C:\InfinityWindow_Recovery` dated 2025-12-10.
- Any requirement not visible in this repo (e.g., Autopilot dashboards, Blueprint ingestion, project export/import) is future work and must not be treated as shipped.
- See `docs/TODO_CHECKLIST.md` for prioritized follow-ups and `docs/PROGRESS.md` for dated log entries (including the “Recovery 2025-12-10” note).
