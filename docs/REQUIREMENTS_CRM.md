# CRM Requirements - Agent C

## Usage & telemetry dashboard
- Status: Implemented
- Description:
  - Phase 1/2: cards, charts, filters, shared time window, and JSON/CSV exports in the Usage tab.
  - Project-level usage summary (`GET /projects/{project_id}/usage_summary?window=1h|24h|7d`, default 24h) returns totals plus per-model and per-group breakdowns.
  - Usage tab analytics card surfaces the project summary with the 1h/24h/7d selector, summary cards, and model/group breakdown lists.
  - Longer 30d/90d persistence/analytics are future enhancements, not part of the current requirement scope.

## Task-aware auto-mode routing
- Status: Partial
- Description:
  - Auto-mode routing v2 uses `_infer_auto_submode` heuristics with new signals (code fences/blocks, research cues, history length, and recent route counts).
  - Telemetry records per-submode counts and textual reasons; `/debug/telemetry` exposes the latest route + reason.
  - Transparency UI: model override control plus “Most recent auto route” pill in the Usage tab showing `auto → <submode>` and reason.
- Remaining:
  - Data-driven tuning using live telemetry and any Autopilot-level routing integration are future work.

