# Usage & Telemetry Dashboard – Design Notes

Status: Phase 1 shipped; Phase 2 shipped (filters, time filter, JSON/CSV export, charts for model/action/confidence/mode, inline error/export fallback states); Phase 3 (persistence/long windows) pending.

## Goals
- Provide a single dashboard (UI + API) to inspect usage and task-automation telemetry over time.
- Keep it lightweight, scoped to the existing `/debug/telemetry` and `/conversations/{id}/usage` data, plus recent task actions.
- Avoid introducing new persistence until needed; start with in-memory plus per-run snapshots.

## Metrics / Facets
- **Usage**: tokens in/out, cost, calls per model, per-conversation, per-project.
- **Task automation**: auto-added, auto-completed, auto-deduped, auto-suggested counts; confidence stats/buckets; recent actions (status/priority/group/blocked/matched_text).
- **Resets**: honor `reset=true` to clear counters and show post-reset values.

## UI Plan (incremental)
1) **Phase 1 (read-only)**:
   - “Dashboard” section in Usage tab:
     - Cards: Totals (tokens/cost/calls), Task counters (auto-*), Confidence buckets, Recent actions (present).
     - Routing reason for auto mode (when available).
   - Filters:
     - Conversation selector (existing).
2) **Phase 2 (charts + filters)**:
   - Implemented:
     - Filters: action, group, model ✅; time filter (all/last5/last10) ✅.
     - Exports: JSON/CSV for **the currently filtered/time-windowed recent actions** ✅.
     - Charts (lightweight bars) for calls per model, task action counts, confidence buckets, and auto-mode route usage ✅.
     - Empty/error states keep the Usage tab stable and surfaced inline (usage fetch errors + export copy failures) ✅.
   - Still open for future windows:
     - Time windows beyond the recent-action window (e.g., last hour/day) if APIs grow.
3) **Phase 3 (persistence/exports)**:
   - Optional: export last N minutes/hours as JSON/CSV (beyond recent actions).
   - Optional: persist telemetry snapshots per reset for comparison.

## API / Data
- Reuse `/debug/telemetry` for task automation counters/stats/actions.
- Reuse `/conversations/{id}/usage` for per-conversation usage totals.
- No new endpoints required for Phase 1; Phase 2 might add:
  - `/debug/telemetry/actions?limit=100&action=auto_added&group=critical`.
  - `/conversations/{id}/usage/aggregate?window=1h` (optional).

### Task action sources (telemetry)
- `auto_conversation`: automation from chat-driven auto-update (and manual retries).
- `manual_update`: manual task edits/closures via `PATCH /tasks/{task_id}`.
- `task_suggestion`: approve/dismiss flows for suggested add/complete actions.
- `qa_seed`: QA-only seed helper `/debug/seed_task_action`.

## Task Grouping Surface
- Use `task_group` (critical/blocked/ready) in recent actions and any future charts.
- Consider a small legend in Usage showing counts by group.

## Acceptance Criteria (minimum)
- Dashboard section renders without errors when telemetry is empty.
- Recent actions show action, confidence, status/priority/group/blocked, matched_text when present.
- Confidence buckets and task counters reflect `/debug/telemetry` reset state.
- Usage totals show non-zero when chat activity exists; no blocking impact if usage is zero.

## Follow-ups
- Decide whether to add persistence (e.g., write recent actions to disk or DB).
- Decide on charting library (lightweight, no heavy deps) or pure CSS bars.
- Keep data fetch inexpensive; cache telemetry for a short window to avoid backend load.


