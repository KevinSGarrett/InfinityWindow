# InfinityWindow – Progress Log

_Updated from `Hydration_File_002.txt`, `To_Do_List_001.txt`, and `Cursor_Chat_Log_002.md` on 2025‑12‑02._

## High‑level status

- **Core backend & chat**: complete per `To_Do_List_001` (health, projects, conversations, /chat with retrieval, usage logging).
- **Docs & local repo ingestion + search**: complete (text docs, repo ingest, /search endpoints, UI panel).
- **Tasks / TODO system**: complete (DB, API, sidebar UI, auto‑extraction from conversations).
- **Usage / cost tracking**: complete (UsageRecord logging and per‑conversation usage panel).
- **Filesystem integration**: complete (local_root_path, /fs/list, /fs/read, /fs/write, editor with “Show original”).  
- **AI file edits**: complete + **diff/preview UX added** in this window.
- **Terminal integration**: complete (AI proposals, run, feedback loop) + **manual terminal UI** added in this window.
- **Project instructions + decision log**: **implemented in this window** (DB columns/models, APIs, prompt injection, Notes UI).
- **Conversation folders**: **implemented in this window** (models, APIs, search integration, basic UI).
- **Memory items (“Remember this”)**: **implemented in this window** (DB + vector store + retrieval + Memory tab + per‑message button).
- **Right‑column UI 2.0**: partially implemented; layout is currently under active iteration based on UX feedback.

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
    - A **“Preview edit”** button that calls `/fs/ai_edit` with `apply_changes: false, include_diff: true`.
    - A diff preview area (`diff-view`) and an optional full proposed file view in a collapsible block.
    - Status and error messages surfaced inline, plus toast notifications for success/failure.
  - “Apply AI edit” still performs the actual write, but now you can see the diff first.

## Features partially implemented / in active iteration

### Right‑column UI 2.0

- Goal: Move from a single tall stack of panels to a more **organized, tabbed workbench** while staying faithful to v2 plans.
- Current state after this window:
  - Right column is split into logical tabs (Work, Files, Tools, Usage, Memory) with **per‑column scrolling** and a sticky tab bar.
  - Within tabs, content has been refactored into **card‑like sections** (`tab-section`) with headers/toolbars and compact list modes.
  - Manual terminal command history, command palette (Ctrl+K), and toasts are wired up.
- Open issues (as discussed in this chat):
  - Work tab still feels dense when all sections are visible together.
  - Files tab side‑by‑side layout may be too cramped; we may need to revert to a vertical editor layout or add a toggle.
  - Tools tab stacks Search + Terminal + History; this needs additional spacing and/or sub‑tabs for clarity.
  - Left column collapse behavior and header layout are being adjusted to avoid visual overlap with the “+ New chat” button.

These UI concerns are **known and actively being addressed**; the next pass will focus on:

- Restoring/expanding the number of right‑column tabs (Tasks, Docs, Files, Search, Terminal, Usage, Notes, Memory) to reduce stacking.
- Making the Files editor full‑width again (vertical layout) or user‑toggable between split and stacked modes.
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

These phases are intentionally high‑level. When we decide to start on one, we should:

- Update this file with concrete sub‑tasks for that phase.
- Cross‑check with `Hydration_File_002.txt` and `docs/RIGHT_COLUMN_UI_PLAN.md` so scope stays consistent.

## CI run log (2025-12-02)

- Command: `make ci`
- Result: **Failed** – `make` is not installed on this Windows host (`'make' is not recognized as an internal or external command`). No checks were executed.
- **QA rerun** (`C:\InfinityWindow_QA`): `make ci` now succeeds (pytest still reports “no tests” but is ignored; `npm run build`/Vite bundle completes without TypeScript errors).

## Notes

- Whenever DB schema changes were made (e.g., adding instructions, decisions, folders, memory_items), we relied on the existing pattern: **delete** `backend/infinitywindow.db` and restart the backend to let SQLAlchemy recreate tables. A proper migration system (Alembic) remains a future improvement.
- Likewise, when resetting the DB, we **cleared `backend/chroma_data`** to keep vector store contents in sync.

## QA fixes implemented on 2025-12-02

- **Message search reliability**: `add_message_embedding` now omits `folder_id` when it is `None`, preventing Chroma from rejecting inserts and restoring `/search/messages` results immediately after chatting.
- **Chat mode routing**:
  - `mode="research"` now gracefully falls back to an authorized model if the configured research model is unavailable.
  - `mode="auto"` uses lightweight prompt heuristics (code fences, research keywords, message length) to pick between the code, research, deep, or fast tiers instead of always defaulting to a single model; it still surfaces the chosen model via the usage log.
- **Autonomous tasks loop**:
  - The maintainer marks tasks `done` when users report completions, avoids duplicates with similarity + token-overlap checks, and keeps the open list ordered by most recently updated items.
  - `GET /projects/{id}/tasks` now returns open tasks first, sorted by `updated_at`, so the UI reflects the autop-run reordering without needing client-side hacks.
- **Guarded QA reset helper**: Added `tools/reset_qa_env.py`, which refuses to touch `backend/infinitywindow.db` or `backend/chroma_data` while port 8000 is in use, then backs up (or purges) both stores so each QA run can start from a clean slate without manual stop/delete gymnastics.
- **QA rerun verification**: After running the reset helper, re-executed the Phase B/C tests:
  - `C-MsgSearch-01` now passes (SNOWCRASH token immediately retrievable).
  - `B-Mode-01/02` confirm research fallback + auto-mode heuristics route to fast/code/deep tiers as expected.
  - `B-Tasks-02` confirms auto-maintainer closes finished work and inserts follow-ups automatically.


