# InfinityWindow – Complete Setup & Usage Manual

_This manual explains, in exhaustive detail, how to **set up**, **run**, and **use** the InfinityWindow system from the GitHub repo. It is written so that a new user can go from zero to fully functional, and then learn how to use every feature._

---

## 1. Prerequisites & Environment

### 1.1 Supported OS & Shell

- **Operating system**: Windows 10/11 (the project is developed and tested on Windows).
- **Shells**:
  - PowerShell (recommended).
  - `cmd.exe` also works for some commands; examples here use **PowerShell** unless noted.

### 1.2 Required Software

Install the following:

- **Python 3.11+** (3.12 confirmed to work).
  - Ensure `python` is on your PATH.
- **Node.js + npm** (recent LTS).
  - Ensure `node` and `npm` are on your PATH.
- **Git** (for getting the repo, optional for some workflows).
- **OpenAI API key** (or compatible key for the configured provider).

Optional but recommended:

- **GNU Make** (via Chocolatey) for `make ci` in a QA/staging copy.
- **Playwright** for UI regression tests.

### 1.3 Directory Layout Convention

By default, the repo is assumed to live at:

- `C:\InfinityWindow`

Key directories:

- `backend\` – FastAPI app, DB, vector store, LLM client.
- `frontend\` – React + TypeScript SPA.
- `docs\` – project docs (plans, progress, QA reports, manuals like this).
- `scratch\` – test files (e.g., `scratch/test-notes.txt`).

These assumptions are encoded in the docs; you can use a different root, but adjust paths accordingly.

---

## 2. Getting the Code & Initial Setup

### 2.1 Clone or Download the Repository

If using Git:

```powershell
cd C:\
git clone https://github.com/your-account/InfinityWindow.git
cd C:\InfinityWindow
```

If you download a ZIP:

- Extract it to `C:\InfinityWindow`.

### 2.2 Backend Setup (FastAPI)

1. **Create and activate a virtual environment** (recommended):

```powershell
cd C:\InfinityWindow\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. **Install backend dependencies**:

```powershell
pip install -r requirements.txt
```

3. **Configure environment variables**:

Create a `.env` file in `backend\` (if one is not already present):

```text
OPENAI_API_KEY=sk-...

# Optional – override model routing
OPENAI_MODEL_AUTO=gpt-5.1
OPENAI_MODEL_FAST=gpt-5-nano
OPENAI_MODEL_DEEP=gpt-5-pro
OPENAI_MODEL_BUDGET=gpt-4.1-nano
OPENAI_MODEL_RESEARCH=o3-deep-research
OPENAI_MODEL_CODE=gpt-5.1-codex
```
These values are just an example of overriding the defaults; if you omit these env vars, the built‑in mode→model defaults are the ones documented in `SYSTEM_OVERVIEW.md` and `CONFIG_ENV.md`.

> Note: If `o3-deep-research` is not available to your account, set `OPENAI_MODEL_RESEARCH` to another supported model to avoid 500 errors on `mode="research"`.

4. **Initialize (or reset) the database and vector store**:

- **First run**: no manual action needed; FastAPI will create `backend/infinitywindow.db` automatically.
- **If schema has changed** and you see `sqlite3.OperationalError: no such column ...`:
  - Stop the backend.
  - Delete:

    ```powershell
    Remove-Item C:\InfinityWindow\backend\infinitywindow.db -Force
    Remove-Item C:\InfinityWindow\backend\chroma_data -Recurse -Force
    ```

  - Restart the backend; the DB will be recreated with the new schema.

5. **Run the backend server**:

From `C:\InfinityWindow\backend` with venv active:

```powershell
uvicorn app.api.main:app --reload
```

Backend will listen on `http://127.0.0.1:8000` (use a different port only if 8000 is occupied; adjust UI/API calls accordingly).

You can verify with:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Expected JSON:

```json
{"status":"ok","service":"InfinityWindow","version":"0.3.0"}
```

### 2.3 Frontend Setup (React + Vite)

1. **Install frontend dependencies**:

```powershell
cd C:\InfinityWindow\frontend
npm install
```

2. **Run dev server**:

```powershell
npm run dev
```

You’ll see output similar to:

```text
  VITE vX.Y.Z  ready in N ms
  ➜  Local:   http://127.0.0.1:5173/
```

3. **Open the app in your browser**:

- Visit `http://127.0.0.1:5173`.
- The UI should load without console errors and show:
  - InfinityWindow header with version pill.
  - Three columns: Projects/Conversations (left), Chat (middle), Workbench tabs (right).

---

## 3. Running a QA/Staging Copy (Optional)

For robust testing, you can maintain a **QA copy** of the repo, e.g. `C:\InfinityWindow_QA`, separate from your main working copy.

### 3.1 Create QA Copy

Using `robocopy` from an elevated PowerShell:

```powershell
robocopy C:\InfinityWindow C:\InfinityWindow_QA /MIR /XD .git .venv node_modules
```

Then:

- Recreate `.venv` in `C:\InfinityWindow_QA\backend`.
- Run `uvicorn` from QA backend.
- Run `npm install` + `npm run dev` from QA frontend.

### 3.2 CI via Makefile (in QA)

In `C:\InfinityWindow_QA\Makefile`:

```make
ci:
	@echo "Running backend tests..."
	-cd backend && pytest
	@echo "Running frontend build..."
	cd frontend && npm run build
```

Then:

```powershell
cd C:\InfinityWindow_QA
make ci
```

- `pytest` may exit with “no tests ran” – ignored by the leading `-`.
- `npm run build` will run the Vite production build and catch TypeScript errors.

---

## 4. Core Usage: Projects & Conversations

### 4.1 Projects

When you first open the app:

- If no projects exist, the backend may create a “Default Project”.
- Otherwise, the **Project selector** (top‑left) will show existing projects.

You can manage projects via API or UI (if exposed), but in most flows:

- You keep a single main project pointing to `C:\InfinityWindow` as its `local_root_path`.

To create a project via API:

```powershell
$body = @{
  name = "Demo Project"
  description = "Main InfinityWindow playground"
  local_root_path = "C:\InfinityWindow"
} | ConvertTo-Json

Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8000/projects `
  -ContentType 'application/json' `
  -Body $body
```

### 4.2 Conversations

In the left column:

- **Conversations list** shows:
  - Titles (or “Chat conversation #id” if untitled).
  - Optional folder labels/color.
- **+ New chat**:
  - Starts a new conversation under the selected project.

You can:

- Click a conversation to view its messages.
- Use “Rename” to give it a title.
- Move it into a folder (see §7.3).

---

## 5. Chat Basics & Modes

### 5.1 Sending Messages

In the middle column:

- Type into the chat input box.
- Press **Enter** to send (Shift+Enter for a newline).
- The UI shows:
  - User messages (you).
  - Assistant messages (InfinityWindow).
  - “Thinking…” placeholder while waiting.

After sending:

- The backend:
  - Stores the message.
  - Runs retrieval (past messages, docs, memory).
  - Calls the LLM.
  - Stores and displays the reply.
  - Logs usage & updates tasks automatically.

### 5.2 Chat Modes

You can choose from:

- `auto` – general‑purpose default.
- `fast` – optimized for speed/low cost.
- `deep` – more thorough reasoning (higher cost).
- `budget` – very cheap but less powerful.
- `research` – intended for deep research tasks (requires an appropriate model).
- `code` – for code‑heavy tasks.

Internally:

- Each mode maps to a concrete model ID via environment variables or defaults (see `docs/CONFIG_ENV.md` and `backend/app/llm/openai_client.py`).
- Built‑in defaults (if you do not override `OPENAI_MODEL_*`) are:
  - `auto` → `gpt-4.1`
  - `fast` → `gpt-4.1-mini`
  - `deep` → `gpt-5.1`
  - `budget` → `gpt-4.1-nano`
  - `research` → `o3-deep-research`
  - `code` → `gpt-5.1-codex`
- You can override these with:
  - `OPENAI_MODEL_AUTO`, `OPENAI_MODEL_FAST`, `OPENAI_MODEL_DEEP`,
  - `OPENAI_MODEL_BUDGET`, `OPENAI_MODEL_RESEARCH`, `OPENAI_MODEL_CODE`
  in your backend `.env`.

Auto‑mode behavior:

- When `mode="auto"` and no explicit `model` is provided:
  - The backend inspects the latest user prompt.
  - It routes to a logical sub‑mode:
    - Code‑heavy → `code`
    - Long, research‑flavored → `research`
    - Very short/simple → `fast`
    - Everything else → `deep`
  - The chosen sub‑mode is translated to a concrete model ID as above.
- If the primary model fails (e.g., `o3-deep-research` is unavailable), the backend:
  - Tries `OPENAI_MODEL_AUTO` (or its default).
  - Then tries `OPENAI_MODEL_FAST` as a last resort.

Practical guidance:

- Use **code** for complex refactors and code generation.
- Use **fast** for quick, low‑stakes questions.
- Use **deep** for thorough analysis.
- Use **budget** when cost is critical.
- Use **research** for long‑context research prompts, but ensure `OPENAI_MODEL_RESEARCH` points to a model your account can access.
- Use **auto** as a default when you want InfinityWindow to pick between code/research/fast/deep automatically.

### 5.3 Model Override & Routing Telemetry

To the right of the chat input, below the Mode dropdown, there is a **Model override** field:

- If you leave it **blank**:
  - The backend chooses a model based on the selected mode and the auto‑routing heuristics described above.
- If you type a **model ID** (e.g., `gpt-5.1`, `gpt-4.1-mini`, `gpt-4.1-nano`):
  - That exact model string is sent to the backend as the `model` parameter.
  - The backend uses your override directly and **skips** auto‑mode routing.

Common example model IDs you can use here:

- `gpt-5.1`
- `gpt-5-mini`
- `gpt-5-nano`
- `gpt-4.1`
- `gpt-4.1-mini`
- `gpt-4.1-nano`
- `o3-deep-research` (if enabled for your account)
- `gpt-5.1-codex` (code‑optimized model)

To inspect how auto‑mode and tasks automation are behaving:

- Open the **Usage** tab (right column).
- The dashboard cards are followed by lightweight charts for task action types, calls per model, confidence buckets, and auto-mode routes; these charts share the same action/group/model filters and time window as the recent actions list.
- Use the filters (action/group/model) and the time filter (all/last5/last10) to scope both the charts and the recent actions list; “Copy JSON/CSV” exports exactly that filtered set and shows a preview inline.
- At the bottom, in **Routing & tasks telemetry**:
  - Click **Refresh** to fetch `/debug/telemetry` from the backend.
  - Optionally click **Refresh & reset** to zero the counters after reading them.
  - You’ll see:
    - Auto‑mode route counts per logical sub‑mode.
    - Model fallback attempts/successes.
    - Counts of tasks auto‑added, auto‑completed, and auto‑deduped.

---

## 6. Tasks / TODOs (Project Tasks)

### 6.1 Manual Tasks

In the **Tasks** tab (right column):

- **Add a task**:
  - Type a description (e.g., “Refactor openai_client model routing”).
  - Click “Add”.
  - The task appears in the list with a checkbox.
- **Mark as done**:
  - Click the checkbox; the status toggles to `done`.
  - Visually, done tasks may show strikethrough or similar styling.

API equivalents:

- `GET /projects/{id}/tasks`
- `POST /tasks`
- `PATCH /tasks/{task_id}`

### 6.2 Automatic Task Extraction

Behavior:

- After each `/chat` call, the backend runs `auto_update_tasks_from_conversation`:
  - Takes recent messages (up to 16) from the conversation.
  - Builds a plain‑text view like:
    - `user: ...`
    - `assistant: ...`
  - Scans for:
    - **Completion phrases** (“X is done”, “Y is fixed”, “we finished Z”…).
    - **TODO‑like statements** that describe new work.
- For each existing open task:
  - Normalizes the text (lowercases, strips punctuation).
  - Compares it against recent completion lines using:
    - Substring checks.
    - Fuzzy similarity (`difflib.SequenceMatcher`).
    - Token overlap.
  - Marks tasks `done` when there is a strong match and increments `auto_completed`.
- Completion detection prefers the freshest user statements and skips clauses that include “pending / not done / blocked / in progress” so noisy updates do not close the wrong tasks.
- For each new TODO‑like line:
  - Normalizes the description.
  - Compares against existing open tasks.
  - Skips it if it looks like a duplicate:
    - Same or very similar wording.
    - High token overlap.
  - Otherwise, creates a new `open` task and increments `auto_added`.
- When listing tasks:
  - The backend sorts so that:
    - All `open` tasks come first.
    - Within each status, most recently updated tasks appear first.
- Pure chatter without actionable verbs or task hints is ignored; no tasks are created and telemetry stays empty for that chat.

What you’ll see:

- As you discuss future work (“We need to X, Y, Z”), new tasks appear in the Tasks tab automatically.
- As you report progress (“We finished X”, “Y is done”, “we merged the change for Z”), corresponding tasks flip to `done` automatically, when the wording is similar enough.
- If you mention that something is still pending/not done/blocked, the maintainer leaves it open; only the latest clear completion will close a task.
- When automation adds, closes, or dedupes a task, a short audit note appears under the task (e.g., “Closed automatically on 2025-12-08 14:20 UTC after: 'login page task is done'”).

### 6.3 Current Behavior & Best Practices

- The auto‑maintainer is **conservative**:
  - It prefers to **not** mark something done rather than mark the wrong task.
  - It only auto‑completes when the completion line clearly matches an existing open task.
  - It skips adding tasks that look like near‑duplicates.
- Manual edits always win:
  - You can still add/edit/complete tasks directly in the UI.
  - Auto‑maintenance respects those changes.

Best practices:

- Be explicit when reporting completions:
  - “Mark the task ‘Refactor openai_client model routing’ as done.”
  - Or re‑use the same phrasing when you say something is finished.
- Periodically skim the Tasks tab:
  - Merge or delete any tasks that feel redundant.
  - Confirm that high‑priority items are near the top; you can always reorder or rephrase tasks for clarity.

### 6.4 Review queue (low-confidence suggestions)
- When items appear: the maintainer queues low-confidence adds/completions, dependency-blocked items (“waiting on/after/depends on …”), or potential duplicates instead of auto-applying them.
- What you see: each queued suggestion shows a confidence chip, priority/group/blocked chips, dependency badges/hints, matched text, and a reason (confidence/dependency/duplicate/noise).
- Actions: **Approve** applies the suggested add/complete and removes the entry; **Dismiss** requires a short reason and logs `auto_dismissed` telemetry. Stale suggestions disappear automatically when the underlying task state changes.
- Telemetry: approvals/dismissals appear in the Usage tab recent actions/exports as auto_applied/queued/dismissed, with confidence and dependency hints preserved.
- Archived projects: tasks/automation are read-only. Review queue actions are disabled and surface an archived/read-only message; automation does not auto-apply changes while archived.

---

## 7. Documents, Search & Memory

### 7.1 Ingesting Text Documents

In the **Docs** tab:

- **Ingest text doc**:
  - Provide:
    - Name (e.g., “Telemetry Spec v1”).
    - Optional description.
    - Content (paste text into textarea).
  - Click “Ingest text doc”.

Backend:

- `POST /docs/text`:
  - Stores the document.
  - Chunks and embeds the content into Chroma.

After ingestion:

- The doc appears in the Docs list.
- It can be retrieved via `POST /search/docs`.

### 7.2 Ingesting a Local Repo

Still in the **Docs** tab:

1. Expand **Ingest local repo**.
2. Fill in:
   - **Root path** – usually the same directory you pointed the project at (`C:\InfinityWindow` in most setups).
   - **Name prefix** – optional label prepended to every ingested file (e.g., `InfinityWindow/` so search results mention the repo path).
3. Click **Ingest repo**.
4. A status card appears directly under the button:
   - Status: `pending`, `running`, `completed`, `failed`, or `cancelled`.
   - Live counters: processed/total files, processed/total bytes, and duration.
   - A **Cancel job** link is available while status = `running`.
   - Errors (bad path, permission issues, OpenAI error) surface inline.
5. Below the form, the **Recent ingestion jobs** table lists the last ~20 jobs with status, files/bytes, duration, finish time, and any error messages. Use the “Refresh” link to reload it on demand.

Backend flow:

- `POST /projects/{project_id}/ingestion_jobs` creates a job (`kind="repo"`) and immediately starts hashing + ingesting files.
- `GET /projects/{project_id}/ingestion_jobs/{job_id}` reports status, counts, and error (if any). The UI polls this every ~2 seconds until the job finishes.
- `embed_texts_batched` enforces `MAX_EMBED_TOKENS_PER_BATCH` (default `50000`) and `MAX_EMBED_ITEMS_PER_BATCH` (default `256`) so embeddings requests never exceed provider limits.
- `FileIngestionState` stores a SHA-256 per project/path, so re-running the ingest only processes files whose content actually changed.
- `ingestion_jobs` keeps timestamps, processed counts, bytes, and cancellation flags so jobs can be audited or stopped mid-run.

When the job completes, the Docs list refreshes automatically and you can immediately search the newly ingested files. This enables questions such as:

- “Where is `auto_update_tasks_from_conversation` implemented?”
- “How does `/terminal/run` work?”

### 7.3 Searching Messages & Docs

In the **Search** tab:

- Modes:
  - **Messages** – search past messages.
  - **Docs** – search ingested docs.

Usage:

- Enter a query (e.g., `DOC_RESET_TOKEN`).
- Press Enter to search.
- Results show:
  - For messages: snippets, conversation IDs, and distance.
  - For docs: document IDs, chunk text, and distance.

Filters & workflow:

- **Conversation filter** – limit message search to a specific conversation.
- **Folder filter** – restrict message search to a conversation folder (e.g., “Backend”).
- **Document filter** – narrow doc search to a single ingested document.
- Each filter can be cleared/reset without reloading the page.

Result actions:

- Each conversation group includes an **Open conversation** button:
  - Sets the active conversation in the middle column.
  - Refreshes messages + usage for that conversation.
- Each document group includes a **View in Docs tab** button:
  - Switches to the Docs tab.
  - Highlights the selected document in the list.

Both message and doc search are covered by the automated QA probes and test plan (`docs/TEST_PLAN.md`); if you see empty results unexpectedly, check the backend logs and QA docs for guidance.

### 7.4 Memory Items

In the **Memory** tab:

- You can:
  - Create memory items (title, content, tags, category).
  - Pin/unpin items.
  - Delete or update items.

“Remember this”:

- Each chat message exposes a button that pre‑fills a Memory form:
  - Title and content drawn from that message.
  - Links back to the original conversation/message.

Usage in chat:

- Pinned memory items are preferentially retrieved and injected into the system prompt, making the assistant behave as if it “remembers” critical facts.

Practical tips:

- Use memory for:
  - Non‑obvious project rules.
  - Long‑term constraints (e.g., “Always use `BLACK` for formatting”).
  - Onboarding notes for new collaborators.

---

## 8. Filesystem & AI File Editing

### 8.1 Browsing & Editing Files

In the **Files** tab:

- The header shows:
  - Project root (from `local_root_path`).
  - Current subdirectory.
- The file list:
  - Folders (`📁`) and files (`📄`).
  - Click a folder to enter it.
  - Click a file to open it.

Editor:

- Textarea shows editable content.
- “Show original” toggles a read‑only view.
- “Save file” writes changes to disk via `/fs/write`.

Safety:

- The backend will reject:
  - Absolute paths.
  - Relative paths with `..`.
  - Attempts to escape the project root.

### 8.2 AI File Edits (Manual & Automatic)

Manual AI edit (via UI):

- In the **AI File Edit** panel:
  - Choose a file path.
  - Describe the change (e.g., “Add logging to error handling”).
  - Click “Preview edit” to see the diff.
  - Click “Apply AI edit” when satisfied.

Automatic edits (via chat):

- Ask the assistant to refactor a file.
- The backend system prompt allows it to emit `<<AI_FILE_EDIT>>` blocks.
- The backend:
  - Applies file edits.
  - Returns the cleaned response (without raw edit blocks).

Best practices:

- Use **Preview** before applying.
- Commit changes in Git after reviewing diffs.

---

## 9. Terminal Integration

### 9.1 AI-Proposed Commands

When the assistant proposes a command:

- The last line of the reply may be a `terminal_command_proposal` JSON object.
- In the **Terminal** tab:
  - You’ll see:
    - Suggested cwd.
    - Command.
    - Reason.
  - You can:
    - Click “Run command” to execute via `/terminal/run`.
    - Click “Dismiss” to ignore.

After running:

- The result is:
  - Displayed in “Last terminal run”.
  - Summarized into a message sent back into the conversation, so the assistant can reason about the output.

### 9.2 Manual Terminal Commands

In the **Terminal** tab:

- Manual command runner:
  - Enter `cwd` (e.g., `backend`, `frontend`, or empty for project root).
  - Enter a command (e.g., `pytest -q` or `npm run build`).
  - Click “Run”.
- History:
  - Keeps past commands + cwds.
  - You can load and re‑run from history.

Safety tips:

- The backend enforces `cwd` under `local_root_path`.
- You, not the assistant, are responsible for destructive commands.
- Prefer safe diagnostics and tests as recommended by the system prompt.

---

## 10. Project Instructions, Decisions, Folders & Memory (Notes Tab)

### 10.1 Project Instructions

In the **Notes** tab:

- **Instructions editor**:
  - Paste or type project‑specific rules, style guides, or behaviors.
  - The backend stores `instruction_text` on the project and injects it into the system prompt for `/chat`.
  - The preview block shows exactly what will be injected.
- **Pinned note**:
  - Short reminder shown at the top of the Notes tab (e.g., “Focus on auth bugs this week”).
  - Great for surfacing time-sensitive priorities without editing the full instructions.
- **Unsaved change banner + diff**:
  - As soon as you modify either the instructions or the pinned note, you’ll see an “Unsaved changes” warning.
  - Expand “View last saved instructions” to compare your draft to the last committed version before overwriting it.

Use cases:

- “Always answer in markdown.”
- “Prefer PowerShell examples over Bash.”
- “This project uses `poetry` instead of `pip`.”

### 10.2 Decision Log

Also in **Notes**:

- **Decision entry form**:
  - Title (e.g., “Adopt Playwright for UI tests”).
  - Category (e.g., “Testing”, “Architecture”).
  - Details.
  - Optional: link to the current conversation.
  - Status selector (`recorded`, `draft`).
  - Tags (comma separated).
- **Decision filters**:
  - Filter the list by status, category, tag, or free-text search.
  - Toggle between the first few items vs. “Show more”.
- **Decision cards** show:
  - Status badges (including `Draft`/`Auto` for system-detected entries).
  - Category chip and tags.
  - Timestamps for creation/last update.
  - Source conversation link (click to jump into the chat).
  - Follow-up task link (if one has been created).
- **Actions per card**:
  - Change status inline (dropdown).
  - Edit tags (inline prompt).
  - Create/clear follow-up tasks (automatically linked back to the decision).
  - Save to memory (creates a memory item with the decision content).
  - Copy text to clipboard.

Benefits:

- You build a **living history** of important choices.
- You can immediately turn a decision into follow-up tasks or memory items without retyping.
- Filters + search make it easy to find “all security decisions” or the last time you approved a migration.
- Later, you (or the assistant) can:
  - Reference past decisions.
  - Avoid revisiting the same debates.

### 10.3 Conversation Folders

In the left sidebar:

- Manage folders:
  - Create “Backend”, “Frontend”, “Docs”, etc.
  - Set colors.
- Move conversations into folders; they will:
  - Be visually grouped.
  - Be filterable in message search via `folder_id`.

### 10.4 Decision Automation & Drafts

- InfinityWindow watches the most recent assistant messages for patterns like “Decision: …” or “We decided to …”.
- When detected, it creates an **auto-detected draft decision**:
  - Marked with `Draft` and `Auto` badges.
  - Linked to the source conversation.
  - Surfaces a banner (“New draft decisions detected”) in the Notes tab.
- Review these drafts quickly:
  - **Mark recorded** to confirm.
  - **Dismiss draft** if it’s noise.
- You can still use all the usual actions (follow-up task, memory, copy) on drafts.

---

## 11. Usage Panel (Per-Conversation Cost & Tokens)

In the **Usage** tab:

- **Conversation selector**:
  - Pick any conversation (not just the one currently open in chat).
  - “Use current chat” jumps back to the active conversation’s usage in one click.
- **Summary metrics**:
  - Total tokens in/out and estimated cost (USD).
  - Total assistant calls recorded for the selected conversation.
- **Model breakdown**:
  - Shows how many calls each model handled.
  - Displays aggregate tokens-in/tokens-out per model so you can spot expensive routes.
- **Recent assistant calls**:
  - Last 10 usage records (model, tokens, timestamp, message ID).
- **Routing & tasks telemetry** (shared with §5.3):
  - Shows auto-mode routing counts, fallback attempts/successes, and autonomous task stats.
  - “Refresh & reset” lets you zero the counters after capturing a snapshot.
- **Task automation charts & exports**:
  - Action/group/model filters and the time filter apply to charts, the recent actions list, and JSON/CSV exports.
  - Filters are keyboard/screen-reader friendly (action/group/model/time plus “Usage time range” and “Usage records window” selectors).
  - Charts cover task action types, calls per model, confidence buckets, and auto-mode routes.
  - If clipboard copy fails, the export preview still appears inline; usage/telemetry fetch errors are shown inline without collapsing the tab.

Backend:

- Every `generate_reply_from_history` call records a `UsageRecord`.
- `/conversations/{id}/usage` aggregates and returns a summary.

Use this panel to:

- Track how “expensive” a conversation is.
- Spot outlier calls (e.g., deep analysis with many tokens) and which model handled them.
- Combine with the telemetry drawer to understand how auto-mode routing is behaving and whether autonomous tasks are firing as expected.

---

## 12. Keyboard Shortcuts & Command Palette

### 12.1 Right-Column Tab Shortcuts

- Alt+1: Tasks
- Alt+2: Files
- Alt+3: Docs
- Alt+4: Search
- Alt+5: Terminal
- Alt+6: Usage
- Alt+7: Notes
- Alt+8: Memory
- Tabs expose ARIA tab roles with visible focus rings; screen readers announce the active tab while Alt+1–8 jumps directly.

### 12.2 Command Palette

- Launch with a shortcut (e.g., Ctrl+K).
- Use it to:
  - Switch tabs quickly.
  - Jump to specific features.

---

## 13. Testing & QA

### 13.1 Manual QA

Refer to:

- `docs/TEST_PLAN.md`
  - Describes end‑to‑end test phases A–I.
- `docs/TEST_REPORT_TEMPLATE.md`
  - Template for recording test runs.
- `docs/TEST_REPORT_2025-12-02.md`
  - Example completed report from a full QA run.

You can follow the test plan to:

- Confirm environment & health.
- Validate CRUD for projects, chats, tasks, docs.
- Exercise filesystem, AI edits, terminal, instructions, decisions, folders, memory.
- Run UI regressions via Playwright.

### 13.2 Automated UI Tests (Playwright)

In the QA frontend (`C:\InfinityWindow_QA\frontend`):

1. Ensure dev server is running:

```powershell
npm run dev -- --host 127.0.0.1 --port 5174
```

2. Run Playwright tests:

```powershell
npx playwright test
```

- `tests/right-column.spec.ts` verifies that:
  - Each right‑column tab can be clicked.
  - The active state updates correctly.

---

## 14. Known Issues & Limitations

> Status as of 2025‑12‑03. For the latest state, see `docs/PROGRESS.md` and the dated `docs/TEST_REPORT_*.md` files.

Earlier internal QA runs (e.g., `TEST_REPORT_2025-12-02.md`) identified several regressions that have since been fixed in the 2025‑12‑02/03 windows:

- **Message search** – `/search/messages` previously returned no hits after chatting; this was fixed as part of the “Message search reliability” work logged in `PROGRESS.md` and `TEST_REPORT_2025-12-02.md`.
- **Research mode** – `mode="research"` previously failed when `OPENAI_MODEL_RESEARCH` pointed at an unavailable model; the routing now falls back gracefully as described in the chat‑modes section and `PROGRESS.md`.
- **Auto mode routing** – `mode="auto"` previously used a single fixed model; it now routes between code/research/fast/deep tiers using heuristics, covered by `B-Mode-02` in `TEST_PLAN.md`.
- **Autonomous TODO maintenance** – the task maintainer previously only added tasks; it now also marks tasks done when completions are detected, dedupes similar items, and orders open tasks by `updated_at`, as reflected in `PROGRESS.md` and `B-Tasks-02`.

As of this manual, there are no additional global “known issues” beyond what is tracked per window in `docs/PROGRESS.md` and the dated `docs/TEST_REPORT_*.md` files. Consult those documents for the most up‑to‑date list of open bugs or limitations.

---

## 15. Future: Blueprints & Autopilot (Design Preview)

> The features in this section are **planned** and described in more detail in `AUTOPILOT_PLAN.md`, `AUTOPILOT_LEARNING.md`, and related docs.  
> They are **not available in the current InfinityWindow build**.  
> Everything in this section describes planned capabilities only; the InfinityWindow build you are running today does not include Autopilot, ExecutionRuns, or Blueprint/Plan features.

### 15.1 Blueprints & Plan tree

In future versions, InfinityWindow will be able to:

- Ingest a very large spec (e.g., 500k‑word blueprint) as a first‑class `Blueprint`.
- Derive a hierarchical **Plan tree** of `PlanNode`s (phases → epics → features → stories → task specs).
- Generate structured tasks for each feature/story node and keep them linked to the plan.
- Drive the Tasks tab from this Plan tree so you can see “where each task lives” in the blueprint.

These behaviors are purely design today; see `AUTOPILOT_PLAN.md` for details.

### 15.2 Autopilot, Execution Runs & “CEO Mode”

Autopilot will add:

- **ExecutionRuns / ExecutionSteps** to log multi‑step work (file reads/writes, tests, docs edits) with diff/rollback.
- A **ManagerAgent** that:
  - Picks the next tasks to work on.
  - Starts and advances runs via `/projects/{id}/autopilot_tick`.
  - Respects a project’s autonomy mode (`off` / `suggest` / `semi_auto` / `full_auto`).
- **Worker agents** (code/test/docs) that use Files/Terminal/Search tools under strict guardrails.

User‑facing flows will include:

- A **Runs** panel/tab that shows what Autopilot is doing, step by step.
- Autopilot controls in the header (mode selector, Pause/Resume, status pill).
- “CEO mode” workflows where a non‑technical user steers the project with high‑level chat instructions while Autopilot executes runs inside those limits.

Again, these are future capabilities; refer to `AUTOPILOT_EXAMPLES.md` for concrete scenarios and treat them as design sketches until the corresponding code and UI land.

---

## 16. Mental Model & Usage Tips


1. **Think in projects**:
   - Create one project per repo or major initiative.
   - Let InfinityWindow be the “brain” for that project: tasks, memory, docs, commands.

2. **Let the system observe your work**:
   - Talk through your plans and steps in chat.
   - The system will:
     - Propose tasks.
     - Suggest terminal commands.
     - Offer file edits.

3. **Use the right tabs**:
   - Tasks → what’s left to do.
   - Docs → what we know.
   - Files → what we can change.
   - Search → what we’ve talked about or ingested.
   - Terminal → what we can run.
   - Usage → what it costs.
   - Notes/Memory → what we don’t want to forget.

4. **Treat AI as a co-pilot, not an oracle**:
   - Review diffs.
   - Sanity‑check terminal commands.
   - Read decision log entries and memory items.

5. **Iterate & refine**:
   - Update project instructions as your style evolves.
   - Use memory items to capture stable facts.
   - Keep tasks clean enough that you trust them.

If you follow this pattern, InfinityWindow can handle a wide range of **difficult, multi‑week projects** by keeping your context, files, tasks, and commands unified in a single, AI‑augmented workspace.


