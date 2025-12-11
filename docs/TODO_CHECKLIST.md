# TODO Checklist (Recovery Baseline)

Legend: `[x]` done, `[ ]` not started.

## Completed – Recovery & baseline re-establish
- [x] Recovery 2025-12-10: Restored backup (`C:\InfinityWindow_Backup\019`) into `C:\InfinityWindow_Recovery`, rebuilt SQLite/Chroma, wired GitHub via `recovery-main-2025-12-10`, and set guardrails (one feature per branch, no repo-wide conflict prompts, human merges to main).
- [x] BE-RECOVERY-001: Restore backend from backup and rebuild SQLite/Chroma from models.
- [x] BE-RECOVERY-002: Wire `C:\InfinityWindow_Recovery` to GitHub via `recovery-main-2025-12-10`; scrub legacy paths.
- [x] FE-RECOVERY-001: Frontend defaults/env updated for recovery; Playwright selectors stabilized.
- [x] DOC-RECOVERY-001: Documented repo roles, workflow guardrails, CRM/TODO/PROGRESS alignment, and agent prompt templates.

## Current focus
- [ ] Keep recovery branches small, tested, and human-merged; protect `main`.
- [ ] Re-check docs (CRM, TODO, PROGRESS) after each change to keep the recovery baseline accurate.

## Future (design-only / not in baseline)
- [ ] Project archive/restore and export/import bundles.
- [ ] Autopilot/Blueprint/manager-worker agents.
- [ ] Advanced/long-window usage analytics dashboards and exports.
- [ ] Terminal injection guard and persisted terminal history.
- [ ] Retrieval/prompting improvements for long-window context.

