# Tasks / Automation / Autopilot Checklist

Sources: `docs/TODO_CHECKLIST.md` and `docs/PROGRESS.md` (current window). This file pulls every task-related item into one list. Status legend matches the main checklist: `[x]` done, `[~]` in progress/partial, `[ ]` not started (or design-only).

## Current window & near-term
- [x] Autopilot reliability: auto_update_tasks runs after `/chat` with retry/timeout guards. (TODO_CHECKLIST §6)
- [x] Autopilot reliability: mitigate 503s for auto_update_tasks. (TODO_CHECKLIST §6)
- [x] Autopilot reliability: handle missing task backlog files gracefully. (TODO_CHECKLIST §6)
- [~] Autopilot reliability: improve task intent extraction to reduce extra “analysis” tasks and handle vague prompts; tighten dedupe/completion on noisy conversations; add telemetry-backed confidence scoring and audit snippets. (TODO_CHECKLIST §6)
- [x] Autonomous task loop upgraded (auto-complete, dedupe, ordering). (TODO_CHECKLIST §1 / PROGRESS Notes)
- [~] Task-aware auto-mode routing (heuristic + telemetry done; refine heuristics and add UI override). (TODO_CHECKLIST §2)
- [~] Suggested-change queue / Approve–Dismiss flow for low-confidence add/complete (initial version shipped; refine). (TODO_CHECKLIST §2)
- [x] Confidence scores + telemetry UI for auto add/complete (Usage tab + task chip). (TODO_CHECKLIST §2)
- [ ] Priority & grouping heuristics (Critical / Blocked / Ready) beyond recency. (TODO_CHECKLIST §2)
- [ ] Dependency tracking and smarter dedupe. (TODO_CHECKLIST §2)
- [ ] Full usage/telemetry dashboard UI (graphs, filters, long-term analytics). (TODO_CHECKLIST §2)
- [ ] Audit trail snippets when automation closes a task (“Closed automatically on …”). (TODO_CHECKLIST §2)
- [x] Telemetry polish: include matched_text (where safe), ensure priority/blocked/confidence consistently appear in recent actions.
- [x] Intent extraction refinement: cut “analysis” noise, handle vague/multi-intent prompts with clearer context and goals.
- [x] Confidence surfaced in tasks UI (chip) and covered by Playwright assertion.
- [x] Usage tab shows confidence buckets and per-action confidence/metadata.
- [x] Seed helper `/debug/seed_task_action` available for QA/UI confidence checks.
- [ ] Context-aware extraction prompts (goals, sprint focus, blockers). (TODO_CHECKLIST §2)
- [ ] Additional QA around noisy projects and long histories. (TODO_CHECKLIST §2)
- [ ] End-to-end chat flow for search and tasks (QA/E2E). (TODO_CHECKLIST §5)
- [x] Expand automated test coverage beyond smoke (backend + frontend) — Playwright + API suites green on 8000. (TODO_CHECKLIST §1)
- [ ] Port CI config back to primary repo; add coverage reporting and basic perf checks. (TODO_CHECKLIST §5)

## Future / product polish (tasks-focused items from PROGRESS)
- [ ] Tasks intelligence upgrades (v3 roadmap): extend maintainer for higher precision/recall, telemetry on accuracy, safeguards for low-confidence, review queue, priority/grouping heuristics, dependency detection, telemetry dashboard, audit snippets, richer context, natural-language task commands, sprint/calendar sync, cross-project dedupe. (PROGRESS v3 Tasks intelligence)
- [ ] Auto mode model routing UI/override; deeper heuristics using telemetry. (PROGRESS v3)
- [ ] Deeper analytics and dashboards for usage and automation. (TODO_CHECKLIST §6 Longer-term)

## Autopilot (design-only, not implemented)
- [ ] Phase 1 – Blueprint & Plan graph (models + endpoints + Plan tree in Tasks tab). (TODO_CHECKLIST §7 / PROGRESS)
- [ ] Phase 2 – Project Brain & context builder (ConversationSummary, ProjectSnapshot; route chat/workers through it). (TODO_CHECKLIST §7 / PROGRESS)
- [ ] Phase 3 – Execution runs & workers (runs API, rollback, Runs panel/tab). (TODO_CHECKLIST §7 / PROGRESS)
- [ ] Phase 4 – ManagerAgent & heartbeat (`autonomy_mode`, `autopilot_tick`, manager plan/refine). (TODO_CHECKLIST §7 / PROGRESS)
- [ ] Phase T – Token/cost controls for Autopilot (MAX_CONTEXT_TOKENS_PER_CALL, AUTOPILOT_MAX_TOKENS_PER_RUN; blueprint ingestion progress/telemetry). (TODO_CHECKLIST §7 / PROGRESS)

## Completed (for traceability)
- [x] Scoped task create (`POST /projects/{id}/tasks`), delete, overview; auto-update hook after chat; enum validation; stale suggestion cleanup; test artifact removal. (PROGRESS 2025-12-06)
- [x] API regression tests for chat→tasks auto-add/complete; noisy conversation coverage. (TODO_CHECKLIST §5, PROGRESS)
- [x] Usage tab telemetry shows task action details; `/debug/telemetry` task counters/stats. (PROGRESS 2025-12-06)

