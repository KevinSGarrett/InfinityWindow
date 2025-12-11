# Requirements & CRM (Recovery Baseline)

Baseline repos:
- Active development: `C:\InfinityWindow_Recovery` (only writable workspace for Cursor agents).
- Read-only backup: `C:\InfinityWindow_Backup\019`.
- Legacy/quarantined: `C:\InfinityWindow` (do not use).

## Implemented / partial (recovery baseline)
- Core workbench: projects, conversations (with pinned note and instructions), tasks, docs, memory, decisions, files, terminal, and semantic search across messages/docs/memory.
- Tasks & automation: auto add/complete/dedupe after chat, approve/dismiss suggestions, and telemetry counters/recent actions; further heuristics/ordering refinements are future.
- Docs and ingestion: text docs plus repo ingestion jobs (create/poll/cancel) with progress.
- Files & terminal: scoped fs list/read/write; AI file edit; guarded terminal run (global and project) with persisted manual run history (new `TerminalHistory` model, 200-entry retention, simple GET feed). Advanced history analytics remain future.
- Usage & telemetry: short-window usage and task automation telemetry; **advanced/long-window dashboards and exports are not implemented**.
- QA/dev workflow: stubbed LLM/vector store by default; small branches off `recovery-main-2025-12-10` (or current recovery branch); human merges to GitHub main.

## Future / design-only (previously proposed or rolled back)
- Project archive/restore and export/import bundles.
- Advanced usage analytics and long-window dashboards/exports.
- Autopilot/Blueprint/manager-worker agent flows.
- Any design-only items in `Project_Plan_003` or `Updated_Project_Plans/*` that are not visible in this recovery codebase.
- Any archive/export/advanced analytics references in `USER_MANUAL.md` or `SYSTEM_OVERVIEW.md` are roadmap notes only; treat them as future until implemented here.

## Pointers
- Work items and status: see `docs/TODO_CHECKLIST.md` and `docs/PROGRESS.md`.
- Workflow guardrails and agent scopes: see `docs/DEVELOPMENT_WORKFLOW.md` and `docs/CURSOR_AGENT_PROMPTS.md`.

