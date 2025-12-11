# Alignment Overview (Recovery)

## Recovery summary
- 2025-12-10: merge/DB/test drift in the legacy repo led to a recovery cut.
- Restored `C:\InfinityWindow_Backup\019` into `C:\InfinityWindow_Recovery`, rebuilt SQLite/Chroma, and rewired GitHub via `recovery-main-2025-12-10`.
- Repo roles: `C:\InfinityWindow_Recovery` active; `C:\InfinityWindow_Backup\019` read-only; `C:\InfinityWindow` quarantined.
- Baseline scope: core workbench (projects/conversations/tasks/docs/memory/decisions/files/terminal, basic usage logging) is implemented; archive/export, advanced analytics, and Autopilot/Blueprint remain future/roadmap only.

## Workflow guardrails
- Cursor agents work only under `C:\InfinityWindow_Recovery` and within the prompt’s file list.
- Keep prompts small and file-scoped; one feature per branch; no “resolve all conflicts” or “clean up all branches” asks.
- `main` stays clean; recovery branches stage fixes; human owner performs GitHub merges.

## References
- Workflow rules: `docs/DEVELOPMENT_WORKFLOW.md` and `docs/CURSOR_AGENT_PROMPTS.md`.
- Requirements status: `docs/REQUIREMENTS_CRM.md`.
- Current tasks and log: `docs/TODO_CHECKLIST.md` and `docs/PROGRESS.md`.
- Roadmap notes: advanced analytics, archive/export, and Autopilot/Blueprint appear only as future items in `USER_MANUAL.md` and `SYSTEM_OVERVIEW.md`.

