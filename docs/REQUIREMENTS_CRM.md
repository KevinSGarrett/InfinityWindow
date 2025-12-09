# CRM Requirements – Tasks, Usage, Retrieval

Use this note to keep the customer-facing requirements for tasks automation (Autonomous TODO), the Usage/telemetry dashboard, and retrieval/context shaping aligned with current behavior. Status labels should stay consistent with `docs/TODO_CHECKLIST.md` and `docs/PROGRESS.md`.

## Autonomous TODO intelligence — Status: Partial
- Scope (current): auto add/complete/dedupe with confidence scoring, audit notes, and a review queue for low-confidence changes; v1 priority/grouping heuristics apply a default priority (critical/high/normal/low style) to auto-added tasks and surface blocked/dependency hints when explicit (appended to `Task.auto_notes` and shown in Usage); manual audits are recorded when a maintainer closes a task (audit note + `manual_completed` telemetry) and surface alongside automatic actions in the Tasks/Usage UIs.
- Status notes: heuristics are intentionally conservative and not yet telemetry-tuned; true dependency graphs, richer approval flows, and broader ranking/grouping remain future work.

## Usage & telemetry dashboard — Status: Partial (Phase 1/2 shipped; Phase 3 pending)
- Scope (current): Usage tab cards + charts for task actions/model/confidence/auto-mode routes with shared filters/time window; Action source filter (All/Automatic/Manual) distinguishes manual vs automatic actions and carries through to charts, recent actions, audit notes (including manual-close notes), and exports; review-queue telemetry shows up in recent actions when suggestions are approved/dismissed.
- Status notes: Phase 1/2 are live; Phase 3 long-window persistence/analytics has not started.

## Retrieval & context shaping — Status: Not started
- Scope (planned): richer per-feature retrieval strategies and context shaping for tasks/docs/memory with configurable modes.
- Status notes: design-only; no implementation beyond existing retrieval defaults.

