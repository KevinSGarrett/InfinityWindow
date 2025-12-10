# InfinityWindow – Progress Log

_Updated from `Hydration_File_002.txt`, `To_Do_List_001.txt`, and `Cursor_Chat_Log_002.md` on 2025‑12‑02._

## High‑level status

- **Core backend & chat**: complete per `To_Do_List_001` (health, projects, conversations, /chat with retrieval, usage logging).
- **Docs & local repo ingestion + search**: complete (text docs, repo ingest, /search endpoints, UI panel) plus **batched ingestion jobs + progress UI (2025‑12‑04)**. Recent fixes: Chroma metadata TypeError resolved; backend expected on `http://127.0.0.1:8000`; Job History UI occasionally slow/flake under load (allow up to 60s).
- **Tasks / TODO system**: complete (DB, API, sidebar UI, auto‑extraction from conversations).
- **Usage / cost tracking**: complete (UsageRecord logging and per‑conversation usage panel).
- **Filesystem integration**: complete (local_root_path, `/projects/{id}/fs/list`, `/projects/{id}/fs/read`, `/projects/{id}/fs/write`, editor with “Show original”).  
- **AI file edits**: complete + **diff/preview UX added** in this window.
- **Terminal integration**: complete (AI proposals, run, feedback loop) + **manual terminal UI** added in this window.
- **Project instructions + decision log**: **implemented in this window** (DB columns/models, APIs, prompt injection, Notes UI).
- **Conversation folders**: **implemented in this window** (models, APIs, search integration, basic UI).
- **Memory items (“Remember this”)**: **implemented in this window** (DB + vector store + retrieval + Memory tab + per‑message button).
- **Stability focus (2025‑12‑05)**: Chat, tasks/backlog, instructions/memory save paths under active verification; large ingestion suite runs are long, so we’re prioritizing non‑ingestion issues first. Added Chroma retry/reset for compaction errors (`/docs/text`, memory embeddings), added SQLite flush retry on memory creation, and landed extended UI smokes (Files, Terminal, Folders, Decision log, Notes reload). Recommend migrating QA to Postgres to remove SQLite lock risk entirely.
- **Right‑column UI 2.0**: partially implemented; layout is currently under active iteration based on UX feedback.
- **CI attempt (2025‑12‑05)**: `make ci` currently fails with “No rule to make target 'ci'.” – add/restore a CI target or document the correct command.

## 2025-12-10 – Usage Phase 3 + auto-mode routing v2
- Usage Phase 3:
  - Added `/projects/{project_id}/usage_summary?window=1h|24h|7d` (default 24h) for project-level totals plus per-model/group breakdowns.
  - Usage tab analytics card shows the project summary with 1h/24h/7d selector, summary cards, and per-model/group breakdown lists.
  - API coverage: `qa/tests_api/test_usage_phase3.py`.
  - Frontend coverage: `frontend/tests/ui-usage-phase3.spec.ts`.
- Auto-mode routing v2:
  - `_infer_auto_submode` heuristics now include code fences/blocks, research cues, history length, and recent route history signals.
  - Telemetry tracks per-submode counts plus textual route reasons, exposed via `/debug/telemetry`.
  - UI transparency: model override plus “Most recent auto route” pill in Usage showing `auto → <submode>` with the reason.
- Branches:
  - `feature/agent-a-auto-mode-v2`
  - `feature/agent-b-auto-mode-ui`
  - `docs/agent-c-usage-phase3-auto-mode-v2`

## 2025‑12‑08 – CI & telemetry alignment
- CI stabilized with stubbed dependencies: `LLM_MODE=stub` and `VECTORSTORE_MODE=stub` now drive `make ci` locally and in GitHub Actions (badge on README stays green).
- Usage dashboard Phase 2 confirmed complete: shared action/group/model filters + time window across charts/exports, JSON/CSV exports scoped to filters, and inline empty/error/export-fallback states.
- Task automation audit trail shipped: Task.auto_notes recorded for auto-add/complete/dedupe; telemetry recent_actions include notes/matched_text/model, covered by `qa/tests_api/test_tasks_automation_audit.py`.

## 2025‑12‑08 – QA updates (port-aligned to 8000)

- Playwright e2e suite green on backend `http://127.0.0.1:8000` after aligning API base in helpers/specs (`ui-smoke`, `ui-chat-smoke`, `ui-extended`, `tasks-suggestions`, `tasks-confidence`); stabilized with seeded data and less brittle waits.
- Confidence chip + Usage telemetry buckets verified in UI via `tasks-confidence.spec.ts`; tasks suggestions and extended flows stable with pre-seeded instructions/decisions/memory/tasks.

## 2025‑12‑08 – Final validation
- Playwright suite (including `ui-accessibility-phase3.spec.ts`) green on 8000; `npm run test:e2e` passes all 6 specs.
- API suite green (`PYTHONPATH='..' pytest tests_api`), only upstream SQLAlchemy `utcnow` deprecation warnings remain.
- Telemetry reset now clears counters on response; app code uses `datetime.now(timezone.utc)` (utcnow calls remain only in SQLAlchemy internals).

## 2025‑12‑09 – Tasks heuristics + regression
- Backend: intent guardrails (penalize vague “analysis” asks), expanded priority/blocked vocab, audit snippets include confidence/matched_text, telemetry lifts matched_text/priority/blocked into recent actions.
- Playwright targeted (tasks-confidence, tasks-suggestions, ui-smoke, ui-chat-smoke, ui-extended) green on backend 8000 after suggestions test stabilization.
- API suite: `PYTHONPATH='.;backend' pytest qa/tests_api` → 10 passed, 1 xfailed (expected), warnings only from upstream SQLAlchemy `datetime.utcnow()` internals.
- Added repo-root `Makefile` with `ci` target (backend API tests + frontend build); run `make ci` from root or QA copy.
- Playwright full suite (6/6) passing on backend 8000 (`npm run test:e2e`).
- Tasks UI sanity (post group chip): targeted tasks-confidence + tasks-suggestions specs passing.
- `make ci` now succeeds on Windows: backend API tests (PYTHONPATH set to root+backend) + frontend build.
- Added optional coverage/perf hooks: `COVERAGE_ARGS="--cov=app --cov-report=xml:../coverage-api.xml"` for pytest; `make perf` runs lightweight perf smoke (`tools/perf_smoke.py`).
- Tasks telemetry/UI update: Usage recent actions show group and matched_text; prompt includes blocked context; tasks-group chip still passes tasks-* Playwright specs.
- Drafted usage/telemetry dashboard design (`docs/USAGE_TELEMETRY_DASHBOARD.md`) for phased rollout (read-only → charts/filters → optional persistence/exports).
- Usage tab now shows summary cards (cost/calls/tokens + task auto-added/auto-completed); tasks-* Playwright specs remain green after the change.
- Added Usage filters (action/group) for recent task actions per dashboard Phase 2; targeted tasks specs still green.
- Added mini-bar visuals for model breakdown and recent task actions confidence; coverage threshold flag available via `COVERAGE_FAIL_UNDER`.
- Full Playwright suite passing after dashboard/filter changes (6/6).
- New E2E API test for chat/search/tasks (`qa/tests_e2e/test_chat_search_tasks.py`); TODO_CHECKLIST QA item marked done.

## 2025‑12‑10 – Dashboard export, model override UI, dependency hints
- Usage tab: model filter for recent task actions, JSON export (last 20 actions) for QA evidence, “Last chosen model”/“Next override” display; mini-bars retained.
- Chat UI: model override dropdown (auto/fast/deep/budget/research/code/custom) plus optional model id; overrides applied to `/chat` payload.
- Tasks automation: dependency hints captured from “depends on/after/waiting for” phrasing and appended to auto notes; dedupe tightened with first-token overlap; prompt context now includes dependency/blocked summary.
- Docs updated (TODO_CHECKLIST, tasks/AUTOMATION.md, tasks/TEST_PLAN_TASKS.md, TEST_PLAN.md, TEST_REPORT_TEMPLATE.md, USAGE_TELEMETRY_DASHBOARD.md).
- Outstanding to verify/fix: Usage tab filters/render (ISSUE-027/028/029), enforce `local_root_path` before fs/list (ISSUE-032), and tighten exception handling/raise-from warnings (ISSUE-041). Backend now emits model in task telemetry and accepts `auto_suggested` seeds.
- 2025‑12‑11 follow-ups: Usage tab now refetches telemetry/usage on tab entry and conversation selection; fs/list validated with `local_root_path` set (`/projects/{id}/fs/list` 200 with entries). Pending: UI verification for Usage filters/list (ISSUE-042) and exception handler tightening (ISSUE-041).
## 2025‑12‑08 – API coverage additions + CI attempt

- Added pytest API coverage for previously untested endpoints (folders, decisions, docs, memory, tasks, conversation messages/usage, debug telemetry) under `qa/tests_api/test_*`; uses TestClient with stub LLM plus isolated SQLite/Chroma fixtures (1536-dim stub embeddings) and a Hypothesis tag-normalization property.
- `python -m pytest ..\qa\tests_api --cov=app --cov-report=xml:../coverage-api.xml` (PYTHONPATH set to `..;.;backend`) now passes new tests but still fails `qa/tests_api/test_ingestion_e2e.py::test_basic_ingestion_happy_path` (ingestion job stayed `pending`); coverage xml still written.
- `npm run build` from `frontend` succeeds (tsc + vite).
- `make ci` from root failed in PowerShell (Python path eval/OSError); ran the backend+frontend steps above manually instead.
## Non‑ingestion coverage plan (2025‑12‑05)

- Automated Playwright smokes to run: `ui-smoke.spec.ts`, `ui-chat-smoke.spec.ts`, `ui-extended.spec.ts` (covers notes reload, decision log, folders, files, terminal, search, suggestions).
- API smokes: error-handling (bad path/missing root/invalid request), usage, docs/text ingest, memory create.
- Remaining stretch (LLM-dependent): chat → auto task extraction, chat → decision log auto-capture, chat → memory recall/search; treat as manual/observational until we have deterministic model hooks.

## Items from `To_Do_List_001.txt` completed in this chat

### 1. Manual terminal command UI (todo‑2)

- **Backend**: `/terminal/run` already existed; no schema changes were required.
- **Frontend**:
  - Added a **manual terminal runner** with fields for `cwd`, `command`, “send output to chat” toggle, and run/clear buttons.
  - On success, the result is:
    - Shown in the “Last terminal run” panel.
    - Optionally summarized and posted back into the current conversation in the required “I ran the terminal command you proposed…” format when “send to chat” is enabled.
  - Added a **manual command history** list with “Load” buttons so previous commands can be re‑run or edited quickly.

### 2. Project instructions + decision log (todo‑4/5/6)

- **DB (`backend/app/db/models.py`)**:
  - Extended `Project` with `instruction_text` and `instruction_updated_at`.
  - Added `ProjectDecision` model with fields: `project_id`, `title`, `details`, `category`, optional `source_conversation_id`, `created_at`.
- **API (`backend/app/api/main.py`)**:
  - Extended project schemas (`ProjectRead`, `ProjectUpdate`) to include instruction fields.
  - Added endpoints:
    - `GET /projects/{project_id}/instructions`
    - `PUT /projects/{project_id}/instructions`
    - `GET /projects/{project_id}/decisions`
    - `POST /projects/{project_id}/decisions`
  - Injected `project.instruction_text` into the **system prompt** for `/chat` so each project can have its own instructions.
- **Frontend (`frontend/src/App.tsx` / `.css`)**:
  - Added a **Notes tab/section** with:
    - Instructions editor (textarea, last‑updated timestamp, save + refresh).
    - Read‑only “Prompt preview” so you can see exactly what will be injected.
    - Decision log form (title, category, details, optional link to current conversation) and list view with categories and timestamps.

### 3. Conversation folders (todo‑7/8/9 – backend + search + initial UI)

- **DB models**:
  - `ConversationFolder` table with `project_id`, `name`, `color`, `sort_order`, `is_default`, `is_archived`, timestamps.
  - `Conversation.folder_id` FK to `conversation_folders.id`.
- **Backend API (`backend/app/api/main.py`, `backend/app/api/search.py`)**:
  - Folder CRUD endpoints:
    - `GET /projects/{project_id}/conversation_folders`
    - `POST /conversation_folders`
    - `PATCH /conversation_folders/{folder_id}`
    - `DELETE /conversation_folders/{folder_id}`
  - Updated conversation schemas to carry folder metadata (`folder_id`, `folder_name`, `folder_color`).
  - Default folder assignment when creating new conversations (if a project default exists).
  - `/search/messages` extended with optional `folder_id` filter and folder info in hits.
  - `/chat` now includes folder context in the system prompt (name, archived status).
- **Frontend**:
  - Left sidebar shows conversations **grouped by folders**, with a small folder toolbar for filtering, creating, and editing folders.
  - New/rename flows accept and send `folder_id` so conversations can be moved between folders.

### 4. Memory items / “Remember this” (todo‑10/11)

- **DB (`backend/app/db/models.py`)**:
  - `MemoryItem` model with fields:
    - `project_id`, `title`, `content`, `tags`, `category`.
    - Optional `source_conversation_id`, `source_message_id`.
    - Flags: `is_pinned`, `is_obsolete`, plus `created_at`, `updated_at`.
- **Vector store (`backend/app/vectorstore/chroma_store.py`)**:
  - New Chroma collection for memory items.
  - `add_memory_item_embedding` and `query_similar_memory_items` (with filters for pinned/obsolete).
- **API (`backend/app/api/main.py`)**:
  - Endpoints:
    - `GET /projects/{project_id}/memory_items`
    - `POST /memory_items`
    - `PATCH /memory_items/{memory_item_id}`
    - `DELETE /memory_items/{memory_item_id}`
  - `/chat` augmented to retrieve **similar memory items** and inject them into the retrieval system message (especially pinned ones).
- **Frontend**:
  - New **Memory tab** on the right showing:
    - List of memory items (title, content, tags, pinned flag, timestamps).
    - Pin/unpin and delete actions.
  - “**Remember this**” button on each chat message pre‑fills a memory form (title/content and source message link).
  - Memory creation/edit flows call the new backend endpoints and surface errors inline.

### 5. Diff/preview UX for AI file edits (todo‑12)

- **Backend (`backend/app/api/main.py`)**:
  - Extended `FileAIEditPayload` with `include_diff` (default `True`).
  - `ai_edit_project_file` now returns a **unified diff** (`diff` field) between the original and edited content (via `difflib.unified_diff`), in addition to `original_content` and `edited_content`.
- **Frontend (`frontend/src/App.tsx` / `.css`)**:
  - AI file‑edit panel now has:
  - A **“Preview edit”** button that calls `/projects/{id}/fs/ai_edit` with `apply_changes: false, include_diff: true`.
    - A diff preview area (`diff-view`) and an optional full proposed file view in a collapsible block.
    - Status and error messages surfaced inline, plus toast notifications for success/failure.
  - “Apply AI edit” still performs the actual write, but now you can see the diff first.

## Features partially implemented / in active iteration

### Right‑column UI 2.0

- Goal: Move from a single tall stack of panels to a more **organized, tabbed workbench** while staying faithful to v2 plans.
- Current state after this window:
  - Right column is split into **eight single‑purpose tabs** – Tasks, Docs, Files, Search, Terminal, Usage, Notes, Memory – with per‑column scrolling and a sticky tab bar (see `RIGHT_COLUMN_UI_PLAN.md`).
  - Within each tab, content is refactored into **card‑like sections** (`tab-section`) with headers/toolbars and compact list modes.
  - Manual terminal command history, command palette (Ctrl+K), and toasts are wired up.
- Open issues (as discussed in this chat):
  - Some tabs can still feel dense when many sections are visible together.
  - Files tab layout and height caps occasionally feel cramped; further spacing and panel tuning may be needed.
  - Left column collapse behavior and header layout are being adjusted to avoid visual overlap with the “+ New chat” button.

These UI concerns are **known and actively being addressed**; the next pass will focus on:

- Polishing the existing eight‑tab layout rather than introducing new super‑tabs.
- Making the Files editor comfortable in its vertical layout and, if needed, adding a future toggle for alternate layouts.
- Loosening height constraints on panels like “Recent assistant calls” so content doesn’t feel crushed.

## Next phases (v3 / v4 / v5…)

Based on `Hydration_File_002.txt`, `To_Do_List_001.txt`, and current code, here’s how remaining ideas map into future phases. These are **not required for v2**; they are explicitly “later” work.

### v3 – Product polish & UX depth

- **More advanced diff UX**:
  - Inline/patch‑level apply, optional per‑hunk acceptance, and possibly side‑by‑side views on top of the existing unified diff.
- **Right‑column UI 2.0 polish, round 2**:
  - Theming (dark/light), icons, improved typography, and finer spacing tweaks per tab.
- **Tabs ergonomics**:
  - Drag‑to‑reorder right‑column tabs and store preferences per browser (localStorage).
  - More complete keyboard model for tabs (arrow‑key navigation, possibly “Skip to Memory” link).
- **Onboarding / guidance**:
  - Guided tour or tips drawer explaining each tab and the main workflows.
- **Analytics & tagging basics**:
  - Topic auto‑tagging for messages and/or conversations.
  - Slightly richer usage/analytics views beyond the current per‑conversation panel.
- **Auto mode model routing**:
  - Implement task-aware heuristics (or lightweight classifier) so `mode="auto"` selects codex/deep/nano tiers based on request type.
  - Update UI/config so users can inspect or override the chosen model when needed.
- **Tasks intelligence upgrades**:
  - Extend the autonomous TODO maintainer so it not only adds tasks but also reconciles completions, updates ordering/priority, and avoids duplicates; target ≥90% precision/recall.
  - Add telemetry around task creation/completion accuracy (auto vs manual) so we can measure and tune reliability.
  - Provide safeguards for low-confidence cases (e.g., ask for confirmation or fall back to manual entry instead of silently adding noise).
  - Introduce confidence scores + a review queue so “maybe” additions/completions require a single click approval.
  - Layer priority & grouping heuristics (Critical / Blocked / Ready) so automation keeps urgent work surfaced.
  - Track dependencies and detect overlapping tasks (“implement API” vs “wire /api endpoint”) before creating new items.
  - Surface a telemetry dashboard (auto-added / auto-completed / dismissed suggestions, accuracy samples) in the Usage tab.
  - Append audit snippets (“Closed automatically on <date> after user said …”) whenever the maintainer marks something done.
  - Feed richer context into the extraction prompt (project goals, sprint focus, known blockers) so the AI emphasizes the right work.
  - Future stretch goals: natural-language task commands, sprint/calendar sync, and cross-project duplicate detection.

### v4 – Integrations & platform expansion

- **Slack integration**:
  - Bot/app that maps Slack channels/threads to InfinityWindow projects & conversations.
  - Slash commands (e.g., `/assistant remember`, `/assistant tasks`) built on top of existing APIs.
- **LibreChat / OpenAI‑compatible endpoint**:
  - `/openai/v1/chat/completions`‑style endpoint that proxies to InfinityWindow’s `/chat`, so third‑party UIs can use it directly.
- **Multi‑provider / multimodal support**:
  - Add Anthropic and/or other providers alongside OpenAI.
  - Optional image/audio endpoints where it makes sense for long‑running projects.
- **Remote GitHub integration**:
  - Attach remote repos by URL, clone + index them, and reuse existing search/doc machinery for remote code.

### v5 – Massive‑scale docs & advanced retrieval

- **Huge hierarchical doc ingestion**:
  - Support ~600k‑word docs with explicit section/subsection/chunk hierarchy.
  - Two‑stage retrieval that first selects sections, then chunks, as described in the original mega‑plan.
- **Advanced code/document search UX**:
  - Deeper filters, cross‑project search, and richer result views for large doc/codebases.

### v6+ – Operational hardening & extras

- **Operational/infra work**:
  - Full logging/monitoring infra, security review, backups, multi‑user considerations.
- **Project export/import & long‑term analytics**:
  - Export/import of projects (tasks, docs, memories, decisions).
  - Higher‑level analytics/exports beyond per‑conversation usage.
- **Task intelligence stretch goals**:
  - Natural-language task commands (“@assistant mark …”) routed through the automation loop.
  - Sprint/calendar sync so high-priority items surface in external planners.
  - Cross-project duplicate detection when multiple initiatives describe the same work.

### Autopilot & Blueprint & Learning [design-only roadmap]

**The Autopilot items below are an agreed design direction only; no Autopilot code has landed yet.**  
For the concrete implementation steps per phase, see `AUTOPILOT_IMPLEMENTATION_CHECKLIST.md`.

In parallel with the v3–v6 themes above, Autopilot introduces a multi‑phase architecture for long‑running, blueprint‑driven projects (see `AUTOPILOT_PLAN.md`):

- **Phase 1 – Blueprint & Plan graph**
  - Models: `Blueprint`, `PlanNode`, `PlanNodeTaskLink`, `TaskDependency`, `BlueprintIngestionJob`.
  - Endpoints: create/list blueprints; generate PlanNode trees; generate tasks for PlanNodes.
  - UI: Blueprint selector and Plan tree in the Tasks tab; “Generate tasks for this node” actions.
- **Phase 2 – Project Brain & context engine**
  - Models: `ConversationSummary`, `ProjectSnapshot`.
  - Modules: `conversation_summaries.py`, `snapshot.py`, `context_builder.py`, `alignment.py`.
  - Behavior: deterministic context bundles for chat/workers; alignment checks for risky edits/commands.
- **Phase 3 – Execution runs & workers**
  - Models: `ExecutionRun`, `ExecutionStep`.
  - Modules: `runs.py`, `workers.py`.
  - Behavior: tool‑calling code/test/doc workers, step logging, diff/rollback, Runs panel in UI.
- **Phase 4 – ManagerAgent & Autopilot heartbeat**
  - Project fields: `autonomy_mode`, `active_phase_node_id`, `autopilot_paused`, `max_parallel_runs`.
  - Modules: `manager.py`, `intent_classifier.py`.
  - Endpoints: `/projects/{id}/autopilot_tick`, `/projects/{id}/manager/plan`, `/projects/{id}/refine_plan`.
- **Phase T – Scalable ingestion & token/cost control**
  - Models: `IngestionJob`, `FileIngestionState`, `BlueprintSectionSummary`.
  - Helpers: `embed_texts_batched`, `get_embedding_model`, ingestion job APIs.
  - Env knobs: `OPENAI_EMBEDDING_MODEL`, `MAX_EMBED_TOKENS_PER_BATCH`, `MAX_EMBED_ITEMS_PER_BATCH`, `MAX_CONTEXT_TOKENS_PER_CALL`, `AUTOPILOT_MAX_TOKENS_PER_RUN`.

These are still **design‑level** items; no Autopilot models/endpoints/UI are live yet. As phases are implemented, this section should be updated with concrete “implemented in window X” bullets and cross‑links into `SYSTEM_MATRIX.md`, `API_REFERENCE.md`, and the Autopilot docs.

These phases are intentionally high‑level. When we decide to start on one, we should:

- Update this file with concrete sub‑tasks for that phase.
- Cross‑check with `Hydration_File_002.txt` and `docs/RIGHT_COLUMN_UI_PLAN.md` so scope stays consistent.

## CI run log (2025-12-02)

- Command: `make ci`
- Result: **Failed** – `make` is not installed on this Windows host (`'make' is not recognized as an internal or external command`). No checks were executed.
- **QA rerun** (`C:\InfinityWindow_QA`): `make ci` now succeeds (pytest still reports “no tests” but is ignored; `npm run build`/Vite bundle completes without TypeScript errors).

## CI / QA spot check (2025-12-03)

- Commands:
  - `robocopy` sync (backend/frontend/docs/qa/tools) from `C:\InfinityWindow` → `C:\InfinityWindow_QA`.
  - `python tools/reset_qa_env.py --confirm`.
  - Backend: `uvicorn app.api.main:app --host 127.0.0.1 --port 8000`.
  - Frontend: `npm run dev -- --host 127.0.0.1 --port 5174`.
  - Playwright: `npx playwright test tests/tasks-suggestions.spec.ts`.
- Result: **PASS** – Tasks tab renders priority chips/blocked reasons and the suggestion drawer approve/dismiss flow works end-to-end after the QA sync + duplicate-handler cleanup.

## Notes

- Whenever DB schema changes were made (e.g., adding instructions, decisions, folders, memory_items), we relied on the existing pattern: **delete** `backend/infinitywindow.db` and restart the backend to let SQLAlchemy recreate tables. A proper migration system (Alembic) remains a future improvement.
- Likewise, when resetting the DB, we **cleared `backend/chroma_data`** to keep vector store contents in sync.
- Issue IDs referenced in dated test reports are now tracked centrally in `docs/ISSUES_LOG.md` so fixes stay auditable.

## QA fixes implemented on 2025-12-02

- **Message search reliability**: `add_message_embedding` now omits `folder_id` when it is `None`, preventing Chroma from rejecting inserts and restoring `/search/messages` results immediately after chatting.
- **Chat mode routing**:
  - `mode="research"` now gracefully falls back to an authorized model if the configured research model is unavailable.
  - `mode="auto"` uses lightweight prompt heuristics (code fences, research keywords, message length) to pick between the code, research, deep, or fast tiers instead of always defaulting to a single model; it still surfaces the chosen model via the usage log.
- **Auto-mode planning bias**: Short-yet-strategic prompts (roadmaps, multi-quarter planning, schema/telemetry rollouts) are forced toward the deep tier unless they are truly breeze-length (<120 chars), preventing “Ping?”-class heuristics from stealing heavier prompts.
- **Autonomous tasks loop**:
  - The maintainer marks tasks `done` when users report completions, avoids duplicates with similarity + token-overlap checks, and keeps the open list ordered by most recently updated items.
  - `GET /projects/{id}/tasks` now returns open tasks first, sorted by `updated_at`, so the UI reflects the autop-run reordering without needing client-side hacks.
  - Completion parsing ignores clauses that contain “still pending / blocked / not done / in progress” hints so open follow-ups do not get closed accidentally when users mention unfinished work alongside completed items.
- **Guarded QA reset helper**: Added `tools/reset_qa_env.py`, which refuses to touch `backend/infinitywindow.db` or `backend/chroma_data` while port 8000 is in use, then backs up (or purges) both stores so each QA run can start from a clean slate without manual stop/delete gymnastics.
- **QA rerun verification**: After running the reset helper, re-executed the Phase B/C tests:
  - `C-MsgSearch-01` now passes (SNOWCRASH token immediately retrievable).
  - `B-Mode-01/02` confirm research fallback + auto-mode heuristics route to fast/code/deep tiers as expected.
  - `B-Tasks-02` confirms auto-maintainer closes finished work and inserts follow-ups automatically.
- **UI regression coverage**: Added Playwright smoke tests (`right-column.spec.ts`, `files-tab.spec.ts`, `notes-memory.spec.ts`) plus a reusable config so the Files, Notes, and Memory tabs get exercised alongside the existing tab-switch regression.
- **Telemetry hooks**: Backend exposes `/debug/telemetry`, reporting auto-mode routing stats and autonomous TODO maintenance counters (auto-added/completed/deduped). QA can now verify routing behavior without digging through logs and optionally reset the counters between runs.
- **Search & Usage UX**: Search tab gained conversation/folder/document filters, grouped results, and “open in chat/docs” actions, while the Usage tab now offers a conversation selector, aggregate metrics, per-model breakdown, enriched recent-call list, and the shared routing/tasks telemetry drawer.
- **Notes & Decisions**: Notes tab now includes pinned notes, an instructions diff preview, richer decision cards (status/tag filters, inline edits, follow-up task/memory hooks, clipboard), and an automation pass that detects “Decision…” statements in chat and captures them as drafts. Projects must recreate the SQLite DB (or run a migration) to pick up the new columns (`pinned_note_text`, decision status/tags/follow-up metadata).

## QA fixes implemented on 2025-12-03

- **Tasks tab regression**: Removed duplicate `handleApproveTaskSuggestion`/`handleDismissTaskSuggestion` definitions in `frontend/src/App.tsx` that caused Vite overlays and blocked Playwright.
- **QA sync workflow**: Documented the `robocopy` + `tools/reset_qa_env.py --confirm` flow so QA can be refreshed safely before each run.
- **Playwright coverage**: `tests/tasks-suggestions.spec.ts` is now part of the standard QA spot-check list, ensuring autonomous task UI stays healthy.

## Enhancements implemented on 2025-12-04

- **Large repo ingestion batching**:
  - Added `embed_texts_batched` with env-configurable caps (`MAX_EMBED_TOKENS_PER_BATCH`, `MAX_EMBED_ITEMS_PER_BATCH`) so docs/repo ingestion stays under OpenAI request limits.
  - Created `IngestionJob` + `FileIngestionState` models to track job progress and skip unchanged files via SHA-256 digests.
  - Added `/projects/{id}/ingestion_jobs` (POST + GET) and wired the Docs tab to poll status with live progress + error reporting.
  - Added cancel endpoint + job history list + UI button so long ingests can be stopped/audited, plus extra telemetry (files/bytes/duration).
  - Added `qa/ingestion_probe.py` so the smoke suite exercises both the happy path and a forced failure.
- **QA evidence (2025-12-04)**:
  - Expanded `docs/TEST_PLAN.md` / `TEST_REPORT_TEMPLATE.md` with a dedicated B-Docs matrix (progress bytes, cancel, history, telemetry, failure path).
  - Fixed `discover_repo_files` so all matching files are collected (bug previously limited ingestion to one file per directory).
  - Ran the scripted harness (`temp_ingest_plan.py`) in `C:\InfinityWindow_QA` to execute B-Docs-01 → B-Docs-07 end-to-end; captured results in `docs/TEST_REPORT_2025-12-04.md` and screenshots/logs for each scenario.

## CI / QA spot check (2025-12-04)

- Commands:
  - `backend\.venv\Scripts\python.exe -m qa.run_smoke`
  - `npm run build`
  - `make ci` in `C:\InfinityWindow_QA` (attempted)
- Results:
  - `qa.run_smoke` **passed** (covers message search, autonomous tasks, repo ingestion happy-path + forced failure, and mode routing).
  - `npm run build` **passed** (TypeScript + Vite production bundle).
  - `make ci` still fails in `C:\InfinityWindow_QA` (“No rule to make target 'ci'.”); that repo needs its Makefile updated before this command can succeed.

## QA fixes implemented on 2025-12-06

- **Tasks & automation**
  - Added scoped task create (`POST /projects/{id}/tasks`), task delete (`DELETE /tasks/{task_id}`), and tasks overview (`GET /projects/{id}/tasks/overview` combining tasks and suggestions).
  - Auto-update runs after `/chat` with retry (config `AUTO_UPDATE_TASKS_AFTER_CHAT`); manual `POST /projects/{id}/auto_update_tasks` kept for retries.
  - Status/priority validation added; stale suggestions cleaned; test artifacts removed via delete endpoint.
- **Search & memory**
  - Memory search now stores and returns `title`; duplicate handler removed to prevent 500/422 errors.
- **Filesystem & terminal**
  - `/fs/read` accepts `file_path` or `subpath`; `/fs/ai_edit` accepts `instruction` or `instructions`.
  - Scoped terminal run no longer requires `project_id` in body; path param is injected server-side.
- **Docs & pricing**
  - `API_REFERENCE.md` and `API_REFERENCE_UPDATED.md` synced with live endpoints/aliases; pricing table now includes `gpt-5-nano`, `gpt-5-pro`, and `gpt-5.1-codex`, fixing zero-cost usage totals.

## Follow-on work – large repo / blueprint ingestion

- Repo ingestion now batches embeddings and surfaces progress; blueprint-specific ingestion (Phase T) still needs:
  - Blueprint-sized batching/resume support (multi-GB specs, multi-phase checkpoints).
  - Streaming progress + resume for blueprint ingestion jobs (similar to repo flow but with section summaries).
  - Blueprint-specific telemetry entries (Batch N/M, section anchors, token budgets) surfaced in UI + `/ingestion_jobs`.

## 2025-12-11 – Usage telemetry UI verification

- Usage telemetry now renders on tab entry and when project/usage conversation changes; errors surface inline.
- Recent task actions list is scoped to the selected project; action/model filters reduce the list (seeded UI run: baseline 3 → auto_added 1, auto_completed 1, model filter 1).
- Model filter falls back to task action models when no usage breakdown exists.
- Docs: `API_REFERENCE_UPDATED.md` notes `local_root_path` must be an existing path on project create; fs/list validation remains enforced.

## 2025-12-11 – Docs/Tests sync + next focus
- Docs in `/docs` and `/docs/tasks` reviewed for current state; alignment logs maintained in `docs/alignment/`.
- Test plans/templates (`docs/TEST_PLAN.md`, `docs/TEST_REPORT_TEMPLATE.md`, `docs/tasks/TEST_PLAN_TASKS.md`) refreshed for current features; upcoming coverage to extend when new work lands.
- Next high-impact items to start:
  1) Refine task-aware auto-mode routing + polish model override UI (doc touchpoints: CONFIG_ENV, USER_MANUAL, USAGE_TELEMETRY_DASHBOARD).
  2) Usage/telemetry dashboard v2 (charts/exports/time filters) with a small Playwright check for charts/export.
  3) Task automation polish: dependency tracking + audit snippets for auto-closes (update tasks/AUTOMATION.md, tasks/TEST_PLAN_TASKS.md with new cases).

## 2025-12-12 – Usage telemetry v2 (partial) and routing reason
- Auto-mode routing now records the routed submode + reason; surfaced in Usage summary.
- Usage tab adds time filter (all/last5/last10), action/model counts, and JSON/CSV export for filtered recent actions.
- USAGE_TELEMETRY_DASHBOARD updated to reflect partial Phase 2; remaining charts/time windows tracked for next iteration.
- Open lint item: UI ARIA/inline-style warnings (ISSUE-045) to address for a clean lint run.

## 2025‑12‑13 – Usage telemetry Phase 2 complete
- Usage dashboard now renders lightweight charts for action types, models, confidence buckets, and auto-mode routes; all charts, lists, and exports share the same action/group/model filters and time window.
- Exports explicitly mirror the filtered recent actions; Usage tab handles empty/error states without collapsing the panel.
- Added API coverage for `/debug/telemetry` and `/conversations/{id}/usage` (`qa/tests_api/test_usage_telemetry_dashboard.py`) plus Playwright coverage for charts/filters/exports (`frontend/tests/usage-dashboard.spec.ts`); docs refreshed for Phase 2 status.
- Phase 2 polish: Usage fetch failures now surface inline, and JSON/CSV exports show a preview even if clipboard copy fails; empty states remain visible so charts/tests keep running even with sparse usage data.

## 2025-12-14 – Task automation audit trail
- Task maintainer now writes short audit snippets for auto-added, auto-completed, and deduped tasks (stored in `Task.auto_notes` and shown in Tasks/Usage UI).
- Task telemetry recent_actions include `task_auto_notes`, matched text, and model info for these automation events to keep audit trails and exports in sync.
- Added API coverage for audit notes and telemetry consistency (`qa/tests_api/test_tasks_automation_audit.py`) and reset task telemetry between tests for deterministic counts.

## 2025-12-15 – Frontend ARIA polish
- Closed ISSUE-045 by adding ARIA tab roles/aria-controls to the right-column tabs (with focus outlines) and clearing inline-style/lint noise.
- Usage dashboard filters are explicitly labeled (“Usage time range”, “Usage records window”) with slightly looser padding for filters/cards; manual updated for accessibility cues.


## 2025-12-08 – Noisy history hardening
- Added API QA for noisy/long conversations: mixed completion vs pending signals, chatter-only no-op, and near-duplicate “login screen” dedupe telemetry.
- Stubbed auto-update now requires actionable hints before adding tasks, ignores pure chatter, and uses the freshest user mention when auto-closing; dedupe covers “login screen/page” variants.
- Core auto_update completion path checks recent “pending/not done/blocked” clauses before closing tasks so new contradictory lines keep tasks open.



