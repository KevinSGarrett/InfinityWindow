# Requirements CRM (Canonical Map)

Purpose: single place to track the current requirements/status for the major automation and safety areas. Other docs should point here when describing requirement coverage.

## Status snapshot

| Area | Status | Notes / canonical links |
| --- | --- | --- |
| Retrieval & context | Shipped for messages/docs/memory; advanced context builder is **design-only** | `docs/SYSTEM_OVERVIEW.md` (3.7 search, ingestion); planned context builder in `docs/AUTOPILOT_PLAN.md` & `docs/AUTOPILOT_LEARNING.md`. |
| Filesystem & terminal safety | Shipped: path guarding under `local_root_path`, terminal allowlist for safe commands | `docs/SYSTEM_OVERVIEW.md` (3.4, 3.5), `docs/AUTOPILOT_LIMITATIONS.md` (design guardrails). |
| Usage dashboard | Shipped (Phase 2 charts/filters/exports); long-window analytics still future | `docs/PROGRESS.md` (2025-12-13 entries), `docs/TODO_CHECKLIST.md` (2 usage dashboard), `docs/USAGE_TELEMETRY_DASHBOARD.md`. |
| Autonomous TODO upkeep | Shipped (auto add/complete/dedupe with audit notes); heuristics continue to evolve | `docs/TODO_CHECKLIST.md` (2), `docs/PROGRESS.md` (tasks automation entries), `docs/USER_MANUAL.md` (§6.2–§6.3). |
| Autopilot (manager, runs, workers) | **Not implemented — design-only** | `docs/AUTOPILOT_PLAN.md`, `docs/AUTOPILOT_IMPLEMENTATION_CHECKLIST.md`, `docs/AUTOPILOT_LIMITATIONS.md`, `docs/MODEL_MATRIX.md` (role models). |
| Model matrix (routing) | Chat modes live; role aliases are design-only | `docs/MODEL_MATRIX.md`, `docs/CONFIG_ENV.md`, `docs/SYSTEM_OVERVIEW.md` (4). |

Use this page as the canonical requirements map; keep it synchronized with `docs/PROGRESS.md` and `docs/TODO_CHECKLIST.md` when statuses change.
