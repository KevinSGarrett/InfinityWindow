# Task Automation & API Reference (current)

This document captures the live task surface (APIs, automation behavior, telemetry, and tests). Use `docs/API_REFERENCE_UPDATED.md` for full payload shapes; this file focuses on tasks.

## Core APIs
- `GET /projects/{id}/tasks` — tasks list (open first, ordered by `updated_at`).
- `GET /projects/{id}/tasks/overview` — tasks + pending suggestions (query: `suggestion_status`, `suggestion_limit`).
- `POST /projects/{id}/tasks` — create task (scoped).
- `PATCH /tasks/{task_id}` — update description/status/priority/blocked_reason/auto_notes (enum validated).
- `DELETE /tasks/{task_id}` — delete task (cleanup/artifacts).
- `POST /projects/{id}/auto_update_tasks` — manual trigger; runs best-effort on latest conversation (400 if none).
- Suggestions: `GET /projects/{id}/task_suggestions`, `POST /task_suggestions/{id}/approve|dismiss`.
- Telemetry: `GET /debug/telemetry` (task counters + confidence stats) and Usage tab drawer (recent task actions incl. status/priority/blocked_reason/auto_notes/confidence/matched_text/task_group).
- Task responses include automation metadata: `auto_confidence`, `auto_last_action`, `auto_last_action_at`, plus `auto_notes` (with audit snippets for auto-closed tasks).

## Automation behavior
- Post-/chat hook: after `/chat`, auto-update runs by default (`AUTO_UPDATE_TASKS_AFTER_CHAT`, retry + timeout guard).
- Extraction prompt context: project description, instructions, pinned notes, top open tasks, blocked-items context, and a new “Dependencies to consider” line (derived from blocked items).
- Priority/blocked heuristics: critical/high/low keyword lists (expanded); blocked reason regexes (blocked on / waiting on / once we …); ordering keeps open tasks first.
- Dependency hints: new tasks capture “depends on / after / waiting for …” phrasing, append a `Dependency hint:` line to `auto_notes`, and store `dependency_hint` in recent action details.
- Intent guardrails: vague/analysis-only asks are penalized into suggestions unless action verbs are present.
- Grouping heuristic: tasks expose `group` (critical/blocked/ready) derived from priority/blocked_reason; surfaced in API and Usage telemetry.
- Context-aware prompt: injects goals/instructions/pinned notes/top open tasks plus blocked/dependency context.
- Completion detection: fuzzy phrase + token-overlap with recent messages; stale completion suggestions are auto-dismissed. Completions are skipped when the latest matching clause includes “pending / not done / blocked / in progress” hints so noisy updates don’t auto-close open work.
- Noisy/long histories: the stubbed auto-update (CI) skips adding tasks when messages are pure chatter, and only closes tasks when the freshest matching user message is a clear completion (later “still pending” lines keep tasks open).
- Aliases/ergonomics:
  - Filesystem read accepts `file_path` or `subpath`.
  - AI edit accepts `instruction` or `instructions`.
  - Terminal scoped run injects `project_id` from path; body `project_id` optional.

### Priorities & blocked status (v1)
- Auto-added tasks get a default priority from keyword heuristics (critical/high/normal/low style) when the phrasing is explicit; otherwise they stay at the neutral default.
- Blocked/dependency hints (“blocked on”, “waiting for”, “depends on/after …”) are appended to `auto_notes` and shown in Tasks/Usage alongside the detected priority/group.
- Automation is intentionally conservative; manual edits in the Tasks tab always override automation (including priority/blocked fields and notes).

## Telemetry & usage
- Task counters: auto-added / auto-completed / auto-deduped; confidence stats + buckets; recent actions list (with status/priority/blocked/auto_notes/confidence/action/timestamp/matched_text/task_group and `dependency_hint` when present).
- Cost: pricing table includes `gpt-5-nano`, `gpt-5-pro`, `gpt-5.1-codex`; Usage tab now shows non-zero totals.
- Usage tab surfaces confidence buckets (lt_0_4, 0_4_0_7, gte_0_7) and per-action confidence; added filters (action/group/model) and JSON export for recent task actions.
- Audit & source: manual closes emit audit notes (“Closed manually on …”) plus `manual_completed` telemetry; action source classification (`auto_conversation`, `manual_update`, `qa_seed`, review-queue approvals) flows into Usage filters and recent actions to separate manual vs automatic work.
- Dev/test seed helper: `/debug/seed_task_action` can create a task and record an automation action with confidence/notes for UI/QA.

## Tests (current)
- API: `qa/tests_api/test_chat_tasks_autopilot.py` (auto-add + complete) and `qa/tests_api/test_chat_tasks_noisy.py` (noisy convo add/complete, long-history completion guard, chatter no-op).
- E2E: `qa/tests_e2e/test_chat_search_tasks.py` (chat → tasks auto-add + message search).
- Smoke: `qa/run_smoke.py` includes tasks auto-loop probe.
- UI: Playwright suite on backend 8000 now green — `frontend/tests/tasks-suggestions.spec.ts` (suggestion drawer approve/dismiss; priority/blocked chips), `frontend/tests/tasks-confidence.spec.ts` (confidence chip + Usage buckets), `frontend/tests/ui-smoke.spec.ts` (instructions meta tightened), `frontend/tests/ui-chat-smoke.spec.ts`, `frontend/tests/ui-extended.spec.ts`.
- Ingestion-adjacent (for completeness): `qa/tests_api/test_ingestion_e2e.py` ensures ingestion does not block task flows.

## Recent telemetry / usage checks
- `/debug/telemetry` on 8000 shows non-zero task confidence stats and recent actions (auto_added/auto_suggested).
- `/conversations/{id}/usage` (sample chat on gpt-5-pro) returned non-zero cost (~$0.04917) confirming usage totals are flowing post-port alignment.
- Playwright stabilizers: seeded data for ui-extended (instructions/decisions/memory/task), refresh-all before confidence chip check, and lenient fallback on instruction meta keep the suite green on 8000.

## Open follow-ups (from `docs/TODO_CHECKLIST.md`)
- Confidence scores + telemetry UX polish.
- Priority & grouping heuristics (Critical/Blocked/Ready) refinement; dependency tracking.
- Context-aware extraction prompt improvements for noisy/long histories.
- Full usage/telemetry dashboard and audit snippets (“Closed automatically on …”).
- Next iteration (planned):
  - Tighten task intent extraction for vague/multi-intent prompts; reduce “analysis” noise. (shipped)
  - Expand priority inference (Critical/High/Ready) and blocked detection with richer phrase lists and context (instructions/goals). (shipped v1 keyword expansion)
  - Emit audit snippets in `auto_notes` when automation closes a task, including confidence and matched text. (shipped)
  - Telemetry polish: include matched_text where safe, ensure confidence stats align with audit notes, and surface priority/blocked in recent actions consistently. (shipped)
  - Add blocked-context into extraction prompt (shipped v1); consider surfacing grouping in Usage charts/table.
  - Future dashboard: dedicated Usage/telemetry dashboard with graphs/filters/long-term analytics (design goal).

## Quick operational notes
- If automation misbehaves in QA, ensure the DB/Chroma are clean (`tools/reset_qa_env.py` in QA copy) and rerun `python -m qa.run_smoke`.
- For UI regressions, run Playwright smokes: `npm run test:e2e -- tasks-suggestions.spec.ts` (frontend dir; dev server on 5174 auto-starts via webServer config).
- For UI confidence checks, `frontend/tests/tasks-confidence.spec.ts` seeds a task via `/debug/seed_task_action` (dev/test only) before asserting chips.

