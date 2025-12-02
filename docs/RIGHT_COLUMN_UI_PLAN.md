# InfinityWindow – Right Column UI 2.0 Plan

_Companion to `Hydration_File_002.txt` and `docs/PROGRESS.md`._  
_Purpose: keep the right-column design and constraints explicit so future work doesn’t drift or regress._

## 1. Current, stable mental model

The right column should feel like a **workbench** with clear, single-purpose tabs. The long-term “grouped” idea (Work / Files / Tools / Usage / Memory) turned out to be confusing in practice, so we’re standardizing on **one main concern per tab**:

- `Tasks` – project tasks / TODOs.
- `Docs` – project documents + ingestion (text + repo).
- `Files` – project file browser + file editor + AI file edits / diff.
- `Search` – semantic search across messages and ingested docs.
- `Terminal` – terminal proposals and manual terminal usage (including history).
- `Usage` – usage/cost for the active conversation.
- `Notes` – project instructions + decision log (human notes, not vector memory).
- `Memory` – long-term memory items and the “Remember this” flow.

**Key rule**: each tab should *only* show the features associated with that concern. No more multi-feature “Work” / “Tools” super-tabs.

## 2. Guardrails learned from v1 of the UI 2.0 attempt

Avoid repeating these mistakes:

- **Overloading tabs**: putting Tasks, Docs, Instructions, and Decisions into one “Work” tab made the column look like a scrollable wall again.
- **Aggressive layout changes**: switching Files to a side-by-side split made the editor too narrow and harder to read.
- **Renaming tabs without wiring conditions**: changing `rightTab` values (e.g., `tools` → `terminal`) without updating the `rightTab === ...` checks caused entire sections to disappear.
- **Touching unrelated areas**: modifying the left column (collapse behavior, header) as part of the right-column task introduced unexpected regressions (e.g., the overlapping “+ New chat” button).

Going forward:

- Only adjust a **single tab** (or the shared tab header) at a time.
- Keep tab names stable (`"tasks" | "docs" | "files" | "search" | "terminal" | "usage" | "notes" | "memory"`).
- Avoid layout experiments that radically change existing behavior (e.g., flipping vertical → horizontal) unless we can revert quickly.

## 3. Canonical per-tab contents (as of this plan)

### 3.1 Tasks tab

**Goal**: Simple, focused project TODO list.

- Header: “Project tasks” with a count badge (number of tasks).
- Toolbar: 
  - `Refresh` button that reloads `/projects/{id}/tasks`.
  - Optional “Show more/less” if there are many tasks.
- Body:
  - Compact “Add task” row (`newTaskDescription`, Add button).
  - Scrollable list of tasks with checkbox toggle (open/done) and strike-through styling for done tasks.

No docs, no instructions, no decisions here.

### 3.2 Docs tab

**Goal**: See ingested docs and ingest new ones.

- Header: “Project documents” with count badge.
- Toolbar: `Refresh` docs list.
- Body:
  - Scrollable list of docs (name, description, doc id).
  - Two collapsible sections:
    - **Ingest text document** – name, description, text, ingest button.
    - **Ingest local repo** – root path, name prefix, ingest button.

### 3.3 Files tab

**Goal**: Browse and edit project files; preview AI file edits.

- Header: “Project files” + toolbar (Up / Refresh).
- Layout: **Vertical**, not side-by-side.
  - Files panel:
    - Location row: `Location: <subpath> (root: <fsRoot>)`.
    - Up + Refresh buttons.
    - Scrollable file list (folders + files, with selected state).
  - Editor panel (only when `fsSelectedRelPath` is set):
    - Header: “Editing: path” + unsaved indicator.
    - “Show original” checkbox; Save button.
    - Large textarea for edited content.
    - Optional “Original (read-only)” block when `Show original` is checked.
- AI file edit section (separate card below the editor):
  - Shows latest AI file-edit proposal (file, reason, instruction).
  - Buttons: Preview diff, Apply edit, Dismiss.
  - Diff preview panel (unified diff + full proposed file view).

### 3.4 Search tab

**Goal**: Semantic search over messages and docs.

- Header: “Search memory”.
- Tabs: Messages / Docs.
- Body:
  - Textarea for query + Search button.
  - Results list with type-specific metadata (conversation id + role for messages; doc id + chunk index for docs).

No terminal or memory content here.

### 3.5 Terminal tab

**Goal**: All terminal-related workflows in one place.

- Manual terminal runner:
  - Inputs: `CWD` (optional), command, “Send output to chat” checkbox.
  - Run + Clear buttons.
  - Error messages in-panel (no alerts).
- AI terminal proposals:
  - Show latest proposal (cwd, command, reason).
  - Run + Dismiss buttons.
  - Error messages inline.
- Last run output:
  - Command, CWD, exit code.
  - STDOUT and STDERR blocks.
- Manual command history:
  - Recent commands (command + cwd + timestamp).
  - “Load” button to copy back into the runner.

### 3.6 Usage tab

**Goal**: Clear summary of model usage for the current conversation.

- Header: “Usage (this conversation)”.
- Body:
  - Totals: tokens in/out, total cost.
  - Scrollable list of recent usage records (model, tokens, message id, timestamp).
  - Height limit should be generous enough that ~10 entries look natural (current cap bumped to 220px; can be tuned).

### 3.7 Notes tab

**Goal**: Human-readable project context and decisions.

- Section: **Project instructions**.
  - Editor textarea.
  - Last-updated timestamp.
  - Save + Refresh buttons.
  - Read-only “Prompt preview” block showing exactly what gets injected into the system prompt.
- Section: **Decision log**.
  - Compact form for adding decisions (title, category, details, optional link to current conversation).
  - Scrollable list of decisions (title, category chip, details, created_at, link to conversation id if present).

### 3.8 Memory tab

**Goal**: Long-term, structured memory items.

- Header: “Project memories”.
- Toolbar: “+ Remember something” (opens modal) + Refresh.
- Body:
  - List of memory items with title, content, tags, pinned flag, timestamps.
  - Buttons per item: Pin/Unpin, Delete.
  - “Remember this” buttons on each chat message pre-fill the form and link back to the source message.

## 4. Layout & scrolling strategy

- Keep the **three-column layout** with:
  - Left: projects + conversations (with folders).
  - Middle: chat.
  - Right: workbench.
- `app-main` uses a 100vh-derived height so the entire app fits the viewport.
- Each of the three columns gets its own `overflow-y: auto` region.
- In the right column, **tab headers are sticky** so the tab bar stays visible while scrolling within that column.
- Inside each tab, individual cards (`tab-section`) may have their own internal scroll for long lists (e.g., tasks, docs, decisions), but we avoid deep nesting of scroll areas.

## 5. Accessibility & keyboard navigation

- Right tab bar:
  - `role="tablist"` on the container.
  - Each button `role="tab"` and `aria-selected` based on `rightTab`.
  - Keyboard access: Alt+1..8 (or similar) to jump between tabs is acceptable as a small enhancement, but **not required** for first-pass polish.
- Skip links:
  - “Skip to chat” link already exists; we can add “Skip to right workbench” later if needed.

## 6. Status / error surfacing

- Prefer inline banners and small pills over `alert()`:
  - Filesystem, docs, tasks, etc. show errors inside their panels in a consistent style.
  - Toasts are used for short-lived status (“Memory saved”, “AI edit applied”, “Command failed”), but they should be supplemental, not the only signal.

## 7. Command UX extras (already in place or scoped)

These are **additive enhancements** and should not change the basic tab layout:

- Command palette (Ctrl+K):
  - Quick actions: switch to tab, focus chat input, collapse sidebar, etc.
  - Simple list with keyboard navigation; we do **not** rely on it for core navigation.
- Manual terminal command history:
  - Already implemented; stays in the Terminal tab.
- Toast system:
  - Already implemented; used sparingly for success/error feedback.

## 8. Phased implementation strategy (to avoid future thrash)

**Phase 0 – Baseline & docs**

- Treat `Hydration_File_002.txt` + `docs/PROGRESS.md` + this plan as the **canonical truth** for behavior.
- Confirm the eight tabs and per-tab contents are functionally correct and match the bullets above.

**Phase 1 – Per-tab visual tweaks (no structural changes)**

- For each tab:
  - Ensure a single clear header (with optional pill) and a clean card layout.
  - Adjust heights and spacing so content is readable without feeling cramped.
  - Do not move features between tabs.

**Phase 2 – Shared polish**

- Make sure tab bar is sticky and looks consistent.
- Make sure vertical scrolling is smooth per column.
- Normalize error/status styles across tabs.

**Phase 3 – Optional “nice-to-haves” (only after sign-off)**

- Command palette refinements.
- Drag-to-reorder tabs with local persistence.
- Guided tour / tips drawer.
- Optional dark/light theme toggle using existing CSS variables.

At every phase, changes should be **small and localized** (one tab or one shared component at a time) and validated against this document to avoid the kind of regressions we saw in the first UI 2.0 attempt.

## 9. Checklist vs original UI 2.0 wishlist

Status legend: ✅ done · ⚠️ partial / changed · ⏳ not done

- **Responsive layout & scroll management**
  - ✅ Main grid uses fixed-height layout (`100vh` minus header).
  - ✅ Each column (left/middle/right) has its own scroll area.

- **Sticky headers**
  - ✅ Right-column tab bar is sticky.
  - ✅ `tab-section` headers are sticky within each card.

- **Logical tab groupings**
  - ⚠️ Original “Work / Files / Tools / Usage / Memory” super-tabs were tried and rejected (too confusing).
  - ✅ Replaced with 8 simple, single-purpose tabs: `Tasks`, `Docs`, `Files`, `Search`, `Terminal`, `Usage`, `Notes`, `Memory`.

- **Compact lists & “Show more”**
  - ✅ Implemented for Tasks, Docs, and Decisions (top N + “Show more/less”).
  - ✅ Height caps loosened for Usage so the list doesn’t feel cramped.

- **Context-aware toolbars**
  - ✅ Each major section (Tasks, Docs, Files, Notes, Terminal) has a small header and toolbar area (e.g., Refresh, Show more/less).
  - ✅ Global “Refresh all” button added above the right-column tabs (reloads tasks, docs, files list, instructions, decisions, folders, memory items, and usage/messages for the active conversation).

- **Dark/light theme preparation**
  - ✅ Core colors now use CSS variables (`--surface`, `--border`, `--primary`, etc.), so theming can be added later.

- **Accessibility & keyboard navigation**
  - ✅ Right tab bar uses `role="tablist"` and `aria-selected` on each tab.
  - ✅ “Skip to chat” link exists.
  - ⏳ Arrow-key tab navigation and “Skip to memory” link are not implemented yet.

- **Status and errors**
  - ✅ Errors surfaced inline in panels (files, terminal, etc.).
  - ✅ Toast notifications used for key success/failure events.
  - ⏳ No per-tab colored status pills (e.g., last AI edit success/failure) yet.

- **Command palette / global quick search**
  - ✅ Basic command palette implemented (Ctrl+K) with quick actions (switch tabs, focus chat, collapse/expand sidebar).
  - ⚠️ Action set is minimal; can be extended in future.

- **Customizable tab order**
  - ⏳ Not implemented; tabs are static.

- **Collapsible left column**
  - ⚠️ Implemented experimentally but reverted due to UX issues (overlapping header).
  - ✅ Left column is now stable and non-collapsible by design for this pass.

- **Command history for terminal**
  - ✅ Implemented; manual command history with “Load” buttons lives in the Terminal tab.

- **Notifications / toast system**
  - ✅ Implemented and wired to key actions (e.g., memory saved, AI edit applied, manual command executed/failed).

- **Tour / onboarding hints**
  - ⏳ Not implemented yet.



