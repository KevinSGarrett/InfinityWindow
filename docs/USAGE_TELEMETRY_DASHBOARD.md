# Usage & Telemetry Dashboard – Design Notes

Status: Phase 1 shipped; Phase 2 shipped (filters, time filter, JSON/CSV export, charts for model/action/confidence/mode, inline error/export fallback states); Phase 3 shipped (project summary + 1h/24h/7d windows); long-window persistence (30d/90d) remains future.

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
- Phase 3 adds `GET /projects/{project_id}/usage_summary?window=1h|24h|7d` (default `24h`) returning project-level totals plus per-model and per-group breakdowns; totals and breakdowns fuel the analytics card.
- Reuse `/debug/telemetry` for task automation counters/stats/actions.
- Reuse `/conversations/{id}/usage` for per-conversation usage totals.
- No new endpoints required for Phase 1; Phase 2 might add:
  - `/debug/telemetry/actions?limit=100&action=auto_added&group=critical`.
  - `/conversations/{id}/usage/aggregate?window=1h` (optional).

## Analytics card (Usage tab)
- Shows the project-level usage summary for the selected window (1h/24h/7d selector, default 24h).
- Summary cards: tokens in/out, estimated cost, total calls.
- Lists: per-model breakdown and per-group breakdown tied to the selected window.
- Error handling: inline banner when the summary fetch fails; charts/exports continue to render when available so the tab stays usable.

## Task Grouping Surface
- Use `task_group` (critical/blocked/ready) in recent actions and any future charts.
- Consider a small legend in Usage showing counts by group.

## Acceptance Criteria (minimum)
- Dashboard section renders without errors when telemetry is empty.
- Recent actions show action, confidence, status/priority/group/blocked, matched_text when present.
- Confidence buckets and task counters reflect `/debug/telemetry` reset state.
- Usage totals show non-zero when chat activity exists; no blocking impact if usage is zero.

## Follow-ups
- Decide whether to add persistence (e.g., write recent actions to disk or DB) and long-window (30d/90d) analytics/exports.
- Decide on charting library (lightweight, no heavy deps) or pure CSS bars.
- Keep data fetch inexpensive; cache telemetry for a short window to avoid backend load.


