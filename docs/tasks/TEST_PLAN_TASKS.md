# Tasks Testing Plan (Target: ≥98/100 coverage score)

Scope: every task-related surface—backend code/API, chat extraction/automation, UI (Tasks/Usage), telemetry, suggestions, filesystem/terminal adjacencies, and Autopilot design hooks where applicable. Use this plan in addition to `docs/TEST_PLAN.md`; this is task-focused and exhaustive. Refreshed 2025-12-12; add cases as new work lands (auto-mode routing reason, telemetry dashboard v2 exports/time filter, task dependency tracking, audit snippets).

## A. Environment & Data Setup
- Fresh DB/Chroma or known seed; ensure `local_root_path` set.
- Backend running on `http://127.0.0.1:8000`; frontend dev server (`5173/5174`) as needed.
- Enable AUTO_UPDATE_TASKS_AFTER_CHAT (default true) for automation paths.
- Create two projects: `Tasks-Happy`, `Tasks-Noisy`; ensure at least one conversation each.
- Seed at least one doc, memory item, decision, and pinned note per project (for retrieval/prompt context).
- Seed a suggestion (add + complete) and a confidence-bearing auto action for UI/telemetry checks.

## B. API Surfaces (CRUD & Validation)
- Create/list/update project-level tasks (`POST /projects/{id}/tasks`, `GET /projects/{id}/tasks`, `PATCH /tasks/{id}`, `DELETE /tasks/{id}`).
- Tasks overview (`GET /projects/{id}/tasks/overview`) returns tasks + suggestions (filters: status, limit).
- Validation: status/priority enums reject bad values (422); blocked_reason and auto_notes accepted.
- Delete cleans artifacts; ordering returns open first, sorted by `updated_at`.
- Limits/pagination: overview honors `suggestion_limit`; rejects over-max; empty lists render correctly.
- Cross-project isolation: identical payloads scoped to each project do not leak tasks/suggestions/telemetry.

## C. Chat → Tasks Automation
- Auto-add: chat creates tasks for clear asks (login page + logout bug).
- Auto-complete: follow-up chat marks one task done, leaves others open.
- Noisy conversation: adds tasks amid chatter; later message completes one; blocked_reason inferred when stated (“blocked on API keys”).
- Post-/chat hook respects AUTO_UPDATE_TASKS_AFTER_CHAT; manual `POST /projects/{id}/auto_update_tasks` works when hook is disabled.
- Idempotence: rerunning auto_update does not duplicate tasks.
- Multilingual/ambiguous: non-English adds/completes; vague asks fall back to suggestions; contradictions don’t close tasks.
- Long-history resilience: relevant ask >10 messages back still handled (or fails gracefully).
- Intent guardrail: “analysis/brainstorm/look into…” without action verbs should prefer suggestions (low confidence) rather than direct adds.
- Prompt context includes goals/instructions/pinned + top open tasks and blocked-items context.
- Dependency hints: “depends on / after / waiting for …” adds `dependency_hint` to auto_notes and recent action details; no crash on missing objects.
- Model override path: chat with override still triggers auto-update; telemetry/Usage show chosen model and next override.

## D. Suggestions & Confidence
- Low-confidence paths emit suggestions via overview and `/projects/{id}/task_suggestions` (pending queue).
- Approve/dismiss flows: `POST /task_suggestions/{id}/approve|dismiss` update tasks and suggestion status.
- Confidence fields present in telemetry (min/max/avg, buckets) and in suggestion payloads (when applicable).
- UI: drawer shows pending items; approve/dismiss updates counts; empty-state renders; confidence (if present) surfaces on tasks or recent actions.
- Regression: suggestions cleaned when target task is done; no stale items.

## E. Priority, Blocked, Ordering Heuristics
- Priority inference: critical/high/low keywords set priority; default normal.
- Blocked_reason detection from natural phrases (blocked on / waiting on / depends on / once we …); blocked tasks remain open.
- Ordering: open first, then recency; priorities do not break ordering stability.
- UI chips: priority and blocked chips render; layout intact.
- (Upcoming) Grouping heuristics: Critical / Blocked / Ready grouping visible in API + UI once implemented.
 - Verify expanded keyword sets (critical/high/low) map to expected priorities; blocked patterns include “blocked on/waiting on/once we…”.
- Tasks expose `group` (critical/blocked/ready) derived from priority/blocked_reason; verify presence in API responses.
- Dedupe tightening: repeated asks with shared first tokens and high overlap are skipped; telemetry `auto_deduped` increments; no duplicate rows.
- Dependency hints surfaced in UI notes and telemetry details.

## F. Telemetry & Usage
- `/debug/telemetry` returns task counters (auto-added/completed/deduped) and confidence stats/buckets.
- Usage tab (UI) shows recent task actions with status/priority/blocked/auto_notes and confidence.
- Telemetry reset (`GET /debug/telemetry?reset=true`) clears counters.
- Usage costs: `/conversations/{id}/usage` returns non-zero cost; aligns with Usage tab when chat exists.
- Recent actions include matched_text when present; priority/blocked fields appear in telemetry entries.
- Action/group/model filters work together; time filter (all/last5/last10) applies to counts/exports; JSON/CSV export of filtered recent task actions matches telemetry; “Last chosen model” card + routing reason match latest usage record; “Next override” reflects pending override.

## G. UI – Tasks Tab
- Render list, add task inline, delete, refresh.
- Status toggles (open/done) reflect API state; blocked and priority chips render.
- Suggestion drawer: pending items appear; approve/dismiss updates list and tasks.
- “Refresh all” updates tasks/suggestions alongside other panels.
- Confidence chip renders when automation metadata exists; decimal shown.
- Multi-project isolation: switching projects updates tasks/suggestions without leakage.
- Keyboard/AX: add task via keyboard, navigate list, approve/dismiss suggestions with keyboard; aria labels present for add button, chips, and drawer controls.
- Empty states: no tasks, no suggestions, no telemetry data render friendly guidance (no crash).

## H. UI – Usage Tab (task facets)
- Recent task actions visible with status/priority/blocked reason/auto_notes; confidence (telemetry buckets).
- Per-conversation filtering does not drop task telemetry; reset clears.
- Bucket labels render (<0.4, 0.4–0.7, ≥0.7); no JSX parsing errors.
- Usage shows non-zero totals when chat activity exists.
- Model filter reduces the list; JSON export reflects filters; last chosen model/next override cards render.
- Verify Usage tab renders recent actions after telemetry is present (ISSUE-027/028/029/042): enter Usage tab, select conversation, click “Use current chat”, ensure list populates, and action/group/model filters reduce entries.
- Telemetry/Usage refresh on tab entry/Use current chat: confirm list populates without manual reload now that telemetry fetch is automatic.

## I. Filesystem/Terminal Adjacent (task flows)
- FS read/write/ai_edit accept `file_path` or `subpath`, `instruction` or `instructions`; no 422s.
- Terminal scoped run works without `project_id` in body on `/projects/{id}/terminal/run`.
- AI edit missing target file is skipped gracefully (no hard failure).

## J. Search & Context Interactions
- Message search works while tasks exist (no regression from tasks features).
- Memory/docs search OK; tasks automation does not break memory/doc retrieval.
- Chat retrieval includes doc titles so automation can reference ingested docs explicitly.

## K. Security / Safety
- `_safe_join` blocks `..` (including embedded); FS endpoints reject traversal.
- Terminal endpoint remains guarded by scoped project_id injection.
- Validation rejects empty project names; pinned_note_text round-trips on update.
- Tasks cannot be created with empty/whitespace description; 422 enforced.

## L. Performance / Resilience
- Auto-update retry path handles transient failures; no unhandled exceptions.
- Overview endpoint performs within reasonable latency (<1s on seed data).
- Telemetry endpoints remain responsive with many task actions.
- Playwright/API runs complete without port errors (use 8000).

## M. Regression & E2E Test Hooks
- API: `qa/tests_api/test_chat_tasks_autopilot.py`, `test_chat_tasks_noisy.py`, `test_api_chat_routing.py` (stubbed), `test_api_projects.py` (pinned_note_text), `test_security.py` (safe_join), `test_ingestion_e2e.py` (compat).
- E2E: `qa/tests_e2e/test_chat_search_tasks.py` (chat → tasks auto-add + message search).
- Smoke: `python -m qa.run_smoke` covers auto-loop probe.
- UI (green on backend 8000): `frontend/tests/ui-smoke.spec.ts`, `ui-chat-smoke.spec.ts`, `ui-extended.spec.ts`, `tasks-suggestions.spec.ts`, `tasks-confidence.spec.ts` (confidence chip + Usage buckets).
- Stability aids: seed data in UI specs (instructions/decisions/memory/task/suggestions), refresh-all before confidence chip assert, lenient instruction meta fallback, optional dismiss in suggestions.

## N. Scoring Rubric (target ≥98/100)
- Critical blockers (API errors, missing tasks, completion fails): -5 each.
- Major gaps (suggestions/telemetry missing, UI actions fail): -3 each.
- Minor issues (chip/label mismatch, cosmetic UI glitches): -1 each.
- Passing all scripted cases (API + UI + smoke) yields full 100; allow max 2 minor deductions to stay ≥98.
- Require: all core API tests passing, all Playwright specs green on 8000 with seeds, non-zero usage cost spot-check, confidence chip visible, suggestions flow completes, instructions/notes persist.
- Apply rubric in `docs/TEST_REPORT_TEMPLATE.md` summary; log deductions explicitly.

## O. Execution Order (suggested)
1) API CRUD/validation (B). 2) Chat automation (C). 3) Suggestions/confidence (D). 4) Priority/blocked/order (E). 5) Telemetry/Usage (F, H). 6) Tasks UI (G). 7) Adjacent FS/Terminal (I). 8) Search/context sanity (J). 9) Security checks (K). 10) Performance/resilience spot checks (L). 11) Regression packs (M). 12) Score with rubric (N).

## P. Evidence to Capture
- API responses for chat automation, overview, suggestions, telemetry (pre/post), and tasks list before/after completions.
- UI screenshots: Tasks tab (list + suggestions), Usage tab (task actions), any chips/labels added.
- Test logs: pytest outputs for `qa/tests_api`, smoke results, Playwright report snippets.

## Q. Edge & Negative Cases
- Task create/update with empty/whitespace description rejected; overly long descriptions handled gracefully.
- Invalid IDs: 404 for non-existent task/project; 400 when project has no conversations for auto_update_tasks.
- Suggestion approve/dismiss with wrong ID returns 404; suggestion already approved returns no-op or 409 per contract.
- Auto-update when AUTO_UPDATE_TASKS_AFTER_CHAT is disabled: hook no-ops, manual endpoint still works.
- Duplicate detection: repeated identical asks do not create dupes; semantic near-dup skip verified.
- Completion safety: mentions of “not done / still pending / blocked” do not close tasks.
- Blocked tasks: status remains open even if completion phrasing appears alongside “blocked”.
- Pagination/limits: overview and suggestions honor `suggestion_limit`; rejects over-max.
- Invalid status/priority inputs return 422 with clear error body.

## R. Multi-Project & Isolation
- Two projects with similar tasks: auto-update and suggestions stay scoped (no cross-project leakage).
- Conversations/folders from one project do not influence task extraction in another.
- Telemetry per conversation/project remains isolated; Usage tab shows correct project/conversation context.

## S. Concurrency & Scale
- Concurrent task creates via `/projects/{id}/tasks` do not deadlock or duplicate; ordering remains stable.
- Concurrent auto_update_tasks calls: no duplicate insertions; suggestions not double-created.
- Large task lists (1000+) still return ordered correctly; overview perf acceptable (<2s).
- Telemetry under load (many task actions) remains responsive; reset works.

## T. UI/UX Polish & Accessibility
- Tasks tab keyboard: add task, navigate list, approve/dismiss suggestion via keyboard.
- Screen reader labels for add-task input, suggestion buttons, status toggles, priority/blocked chips.
- Empty states: no tasks, no suggestions, no telemetry data render friendly guidance.
- Error toasts/banners appear for failed create/update/delete and disappear on retry.

## U. Config Toggles & Fallbacks
- AUTO_UPDATE_TASKS_AFTER_CHAT=false: verify no automatic updates; manual endpoint still functional.
- Model overrides (mode=auto/fast/deep/budget/research/code) do not break task extraction when stubs/fallbacks are used.
- Telemetry reset: counters zeroed, no residual state in Usage tab after refresh.

## V. Data Integrity & Auditing
- `pinned_note_text` round-trips via project update and instructions endpoints.
- Tasks include auto_notes when set; PATCH preserves other fields.
- Deleted tasks removed from overview and suggestions; no orphaned suggestions after delete.
- Audit snippets stored and surfaced; verify timestamp, source message/ref, confidence, and priority/blocked context.

## W. Autopilot & Design Hooks (tracking)
- Phase placeholders (blueprints, runs, manager) remain inert: task flows unchanged with design-only code present.
- Config/env for future Autopilot tokens (MAX_CONTEXT_TOKENS_PER_CALL, AUTOPILOT_MAX_TOKENS_PER_RUN) default safely (no crashes).

## X. Performance / Resilience Deep Cuts
- Auto-update retry on transient DB/embedding errors recovers without duplicating tasks.
- Overview and suggestions endpoints handle intermittent DB contention (busy timeout respected).
- Long chat histories: extraction still runs (or fails gracefully) without timing out the API.

## Y. Chat-Specific Exhaustive Cases
- Languages & phrasing: English + at least one non-English (e.g., Spanish) request adds tasks; completion phrasing in non-English marks done; mixed-language chatter does not break extraction.
- Multi-task asks: single message with 3–5 tasks; all created, no truncation; priorities inferred where applicable.
- Ambiguity: vague requests generate suggestions (low confidence) rather than direct adds; queue visible in overview.
- Contradictory signals: message says “done” and “still pending” together; task is not closed (safety).
- Overlapping descriptions: “Implement login” vs “Add login page” deduped; semantic near-dup check prevents double add.
- Dependency phrasing: “depends on”, “after we”, “waiting for” produces tasks with dependency hint in auto_notes and recent action details; no crash on missing object.
- Stricter dedupe: near-duplicate tasks sharing first ~5 tokens are skipped; telemetry `auto_deduped` increments; no duplicate row in `/tasks`.
- Blocked + done in one message: “Payment retry flow is blocked until keys arrive; login task is done” → payment remains open/blocked; login marked done.
- Follow-up corrections: user says previous completion was wrong; task reopens (if supported) or remains open after manual toggle; no phantom auto-complete.
- Long history: extraction works when relevant ask is >10 messages back; uses max_messages window; no crash when history exceeds window.
- Mode variations: mode=auto/fast/deep/budget/research/code do not regress task extraction (stubbed or real); auto-mode subrouting still calls extraction.
- Attachments/links: mentions of docs/memory titles in chat do not break extraction; tasks may reference doc titles; no crashes on unknown links.
- Tool errors: simulated embedding/model failure during chat does not crash `/chat`; auto-update retry path logs warning and leaves tasks unchanged.
- Hook disabled mid-run: toggle AUTO_UPDATE_TASKS_AFTER_CHAT off, send chat, verify no auto-update; re-enable, next chat triggers auto-update.
- Multiple conversations per project: auto-update chooses latest conversation; manual endpoint works when pointing to recent conversation set.
- Cross-talk: interleaved assistant/system messages do not get treated as user TODOs.

## Z. UI Verification for Chat Outcomes
- After chat auto-add, Tasks tab reflects new items without manual refresh (or after Refresh All).
- After chat auto-complete, status chip shows done; suggestion queue drains if applicable.
- Usage tab shows recent task actions corresponding to the chat interactions (add/complete, confidence if available).
- Suggestion drawer updates when low-confidence paths were taken during chat.

- Tasks tab renders a confidence chip for auto-added/completed items showing last action and confidence value.
- Playwright: after seeding an auto-added task, assert `.task-confidence-chip` exists and contains a decimal.
- No regression to priority/blocked chips layout; chips wrap gracefully on narrow widths.
- Usage tab renders confidence buckets and recent actions with timestamps/notes; Playwright can assert a recent task action shows a formatted confidence.
- Test helper: `frontend/tests/tasks-confidence.spec.ts` seeds a project/task via `/debug/seed_task_action`, verifies the confidence chip, and (when usage data exists) checks telemetry buckets (skips usage check when no usage records).
- Confirm usage totals are non-zero by calling `/conversations/{id}/usage` after a chat; align UI Usage tab with API values (spot-check dollars and confidence buckets).
- Stability aids (current suite): refresh-all before chip assert; allow instruction meta to be absent if values persist; seed data for ui-extended (instructions/decisions/memory/task) to keep UI paths deterministic.
- Model override UI near chat input renders (default/auto/fast/deep/budget/research/code/custom); override applied to `/chat` payload; “Last chosen model” and “Next override” appear in Usage cards.
- Usage tab JSON export (last 20 recent task actions) available; contents match `/debug/telemetry` recent_actions slice; model filter reduces the list accordingly.
- Dependency hints appear in auto_notes for tasks created from dependency phrasing; blocked/dependency context visible in prompt preamble (manual spot-check or log).
- Accessibility: Tasks tab controls and Usage export/filter controls reachable via keyboard; tooltips/labels present where applicable.

## AB. Extended Telemetry/Usage Testing
- `/debug/telemetry` includes confidence buckets and recent actions; verify reset clears buckets/actions.
- Usage tab:
  - Switching conversations updates Usage panel and retains telemetry drawer.
  - “Use current chat” focuses selected conversation and refreshes usage/telemetry without errors.
  - Refresh vs Refresh & reset buttons behave correctly; reset zeroes counters in UI.
  - Recent actions render confidence with two decimals and show matched_text/timestamp when present.
  - Model filter and action/group filters jointly reduce recent actions; JSON export honors filters (up to 20 entries).
  - Telemetry list populates on tab entry/Use current chat (no empty-state regressions); if empty with data in `/debug/telemetry`, mark failure (ISSUE-027/028/029).
- API: confidence_buckets present even when empty; confidence_stats omitted when no actions.
- API validation: tasks expose `auto_confidence`, `auto_last_action`, `auto_last_action_at`; ensure present after auto-add/complete paths.

## AC. End-to-End Coverage (Tasks, target ≥98/100)
- Playwright on backend 8000 (with seeds/stability aids): `ui-smoke`, `ui-chat-smoke`, `ui-extended`, `tasks-suggestions`, `tasks-confidence` all passing.
- API pack (`qa/tests_api`) with PYTHONPATH set; chat→tasks auto-add/complete and noisy flows green.
- Usage cost/telemetry: `/conversations/{id}/usage` non-zero after chat; Usage tab shows confidence buckets/actions aligned with API.
- Suggestions flow completes (approve/dismiss), no stale items; confidence chip visible for auto actions.
- Instructions/pinned note persist (UI + API); tasks/usage tabs isolate per project.
- Scoring gate: any critical task-related failure drops below 98; require API + UI green, non-zero usage, confidence chip visible, suggestions flow successful, instructions persist.
- Telemetry dashboard (future): refer to `docs/USAGE_TELEMETRY_DASHBOARD.md` for phased rollout; once implemented, add dashboard checks here.
- Evidence required for pass: API responses (tasks list, overview, telemetry pre/post, usage), UI screenshots (Tasks list + suggestions + confidence chip; Usage recent actions with filters/export and model cards), and Playwright/API logs attached to report.
