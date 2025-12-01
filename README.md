# InfinityWindow – A Local AI Workbench for Long‑Running Projects

InfinityWindow is my attempt to build the kind of AI workspace I *wished* existed:

- It remembers **everything** important about a project – not just the last few messages.
- It can see **your real files and repos**, not just paste‑ins.
- It organizes conversations, tasks, decisions, and documents so you can work on the same project for **weeks or months** without losing the plot.   

Think of it as a “personal AI operating system” for deep work – built to solve the exact pain of:

> *“My chat window forgot half the project, I have 500k words of plans, a large codebase, and I’m completely lost.”*   

---

## 1. What InfinityWindow Is (Non‑Technical Overview)

Most AI tools work like this:

- You open a chat.
- You paste in some context.
- The model gives a response.
- After a while, the chat “forgets”, context runs out, and you’re back to copy‑pasting.

InfinityWindow is designed to be the opposite of that experience:

1. **Projects, not just chats**

   - You work in named **projects** (“RastUp orchestrator”, “New product spec”, etc.).
   - Each project has:
     - A set of conversations.
     - Attached documents and Git repos.
     - Project instructions (“charter”).
     - A decision log (“we chose X over Y because…”).
     - A task list / TODOs.   

2. **“Never forgets” important context**

   - All conversations are saved.
   - Large docs (hundreds of thousands of words) and code are indexed.
   - When you ask a question, InfinityWindow automatically pulls in the most relevant snippets from:
     - Past messages.
     - Project docs.
     - Attached repositories.
     - Pinned memories (“remember this”).   

3. **A focused, local web UI**

   - Custom “ChatGPT‑style” web interface:
     - Project selector.
     - Conversation list.
     - Main chat pane.
     - Right‑hand panel with tabs for **Docs, Search, Tasks, Usage, Files, Terminal, Memory**.   
   - Built to feel like a serious workbench, not just another chatbot.

4. **Grounded in your actual files**

   - InfinityWindow knows the **local root folder** for each project.   
   - You can:
     - Browse the directory tree.
     - Open files.
     - (Safely) apply AI‑proposed edits with a diff & “Apply changes” confirmation step.

5. **Built for multi‑week projects**

   - Conversation folders, auto‑generated titles, and project notes help you find things again later.
   - A per‑project task list that the AI can help maintain for you.
   - A cost/usage panel so you can see which models you’re using and what they cost over time.   

---

## 2. Why This Project Is Interesting to Employers

### 2.1 Real problem, not a toy demo

This project started from an actual pain point:

- I had **~500k words** of project plans plus a growing codebase.
- A long‑running chat session went off‑track and started forgetting core details.
- Untangling what was done, what was missing, and how to continue realistically required better tooling than a normal chat window.   

InfinityWindow is the system I designed to prevent that scenario from ever happening again.

### 2.2 “Never‑forget” AI: practical RAG, not hype

Under the hood, InfinityWindow implements a serious Retrieval‑Augmented Generation (RAG) setup:

- Large docs are **chunked hierarchically** (document → section → subsection → chunk).
- Both documents and conversations are embedded into a vector store.
- For each new message, the backend performs **multi‑step retrieval** to assemble a compact, relevant context for the model.   

This is the difference between “I pasted a PDF” and “my assistant actually *remembers* the whole PDF and can reference it precisely.”

### 2.3 Designed as a platform, not a one‑off script

InfinityWindow is structured as a real product:

- A backend API (FastAPI) with clearly defined endpoints.
- A local database for projects, messages, tasks, documents, etc.
- A vector database (e.g., Chroma) for semantic search across messages, docs, and code.
- A modular front‑end layout that can evolve over time (new tabs, new tools, new visualizations).   

An employer can see:

- System design.
- Separation of concerns.
- A clear roadmap and phased delivery plan.

### 2.4 Multi‑model, multi‑provider mindset

The system is designed to support:

- Multiple chat models (e.g., different OpenAI models, and optionally Anthropic).
- Different usage modes: `auto / fast / deep / budget / research / code`.   

Even if the initial implementation focuses on OpenAI, the architecture is built to add more providers and modalities without rewriting everything.

---

## 3. Key Features (High‑Level)

Here’s what InfinityWindow aims to provide once the current roadmap is complete.

### 3.1 Project‑centric workspace

- **Projects as first‑class citizens**:
  - Each project has its own instructions, conversations, docs, repos, tasks, decisions.
- **Per‑project instructions (“charter”)**:
  - A long‑form description of goals, constraints, and context that is always injected into the system prompt.
- **Decision log**:
  - A growing list of “We decided X instead of Y because Z” so the AI doesn’t re‑open old debates.   

### 3.2 Conversation organization

- Auto‑generated conversation titles (with manual override).
- Conversation folders (e.g., “Architecture”, “Frontend”, “Ops”).
- Each conversation belongs to a project and can be grouped, searched, and revisited. :contentReference[oaicite:12]{index=12}  

### 3.3 Document and repo ingestion

- Ingest documents up to **600k+ words**, using structured chunking for efficient retrieval.
- Attach Git repos to projects and index code files for semantic search:
  - “Explain the architecture of X.”
  - “Find where `UserSession` is instantiated.”
  - “What changed between commit A and B in this area?”   

### 3.4 Tasks / TODO system (AI‑assisted)

- A per‑project tasks table, surfaced as a **Tasks** tab in the UI.
- You can create and complete tasks manually.
- The AI can scan recent conversation history and:
  - Extract new tasks.
  - Mark tasks as done when they are discussed as completed.
- Optional: automatic updates after every conversation turn.   

The goal is that your task list stays synchronized with the reality of the project, without you having to manually maintain a giant checklist.

### 3.5 Cost & usage tracking

- The backend records:
  - Which model was used.
  - Input/output tokens.
  - Approximate cost per call.
- The UI shows:
  - Totals for each conversation.
  - Stats for the last reply (model, tokens, cost).   

This makes the system transparent and helps manage cost when working on large projects.

### 3.6 Local file and terminal integration

- **Files tab:**
  - Browse the project’s local directory tree.
  - View file contents in the UI.
  - Stage 1 safe edits: AI suggests a change → you see a diff → you approve → backend writes the file.   

- **Terminal tab:**
  - Run commands in the project directory from inside the app (e.g. `git status`, `pytest`).
  - Later: AI‑proposed commands that you explicitly approve before they run.   

The long‑term vision is an AI that can see your actual repo and tools, not just what you paste.

### 3.7 Memory upgrades – “Remember this”

- A dedicated **memory_items** table:
  - Keyed “memories” like canonical API lists, core requirements, edge cases.
- “Remember this” action in the chat:
  - Select text or a message → save as long‑term memory for the project.
- These items are stored, indexed, and pulled into context for future chats.   

---

## 4. Under the Hood (High‑Level Technical View)

For more technical readers, here’s the simplified architecture.

> **Note:** This is intentionally written in “resume‑friendly” language, but maps directly to the actual plan and code structure.

### 4.1 Backend

- **Framework**: FastAPI.
- **Core endpoints**:
  - `/chat` – project‑aware chat endpoint that:
    - Looks up the project.
    - Performs memory retrieval.
    - Routes to the correct model.
  - `/docs/*` – upload and manage documents.
  - `/github/*` – attach and index local repos.
  - `/projects/*` – CRUD for projects, instructions, decision logs.
  - `/tasks/*` – CRUD for tasks and AI‑assisted extraction.
  - `/terminal/*` – run commands (with guardrails).
  - `/files/*` – browse and edit files under the project root.   

- **Storage**:
  - Relational DB (SQLite/Postgres) for:
    - Projects, conversations, messages.
    - Documents, sections, chunks.
    - Tasks, memory items, usage records.
  - Vector DB (Chroma/Qdrant/etc.) for embeddings:
    - Conversation chunks.
    - Document chunks.
    - Code chunks.
    - Pinned memories.   

### 4.2 Model routing

- Model registry describing:
  - Available models, context sizes, and cost tiers.
- Router chooses:
  - Which model to use based on task type (`chat`, `summarization`, `code`, etc.), context size, and budget.   

### 4.3 Retrieval pipeline

For each user message:

1. Fetch recent conversation history.
2. Query vector store for relevant:
   - Past messages.
   - Document chunks.
   - Code.
   - Memory items.
3. Combine with:
   - Project instructions.
   - Decision log.
4. Build final prompt and call the chosen model.   

---

## 5. Status & Roadmap

InfinityWindow is intentionally being built in phases.

### 5.1 Current status

Based on the latest project plan, the following pieces are already in place or mostly implemented:

- Backend foundations (FastAPI, DB, vector store).
- Core chat with multi‑mode support.
- Document & repo ingestion wired into retrieval.
- Custom InfinityWindow UI with:
  - Projects dropdown.
  - Conversations list.
  - Chat pane with modes.
  - Right‑hand panel with docs/search/ingestion tools.   

### 5.2 Upcoming work (InfinityWindow v2 roadmap)

From the updated plan, the next major milestones are:   

- **Project & conversation organization**
  - Auto‑titles and folders.
  - Project instructions editor.
  - Decision log UI.

- **Tasks / TODO sidebar**
  - Manual tasks tab.
  - On‑demand AI “Update tasks from conversation” button.
  - Optional automatic updates after each message.

- **Usage / cost tracking panel**
  - Backend usage logging.
  - Compact “Last reply” and “Conversation totals” box.

- **Local project directory integration**
  - `local_root_path` per project.
  - File browser.
  - Safe, diff‑based file edits.

- **Terminal integration**
  - Terminal tab with output.
  - AI‑proposed commands with explicit user approval.

- **Memory upgrades & UI 2.0**
  - “Remember this” flow.
  - Memory tab.
  - Refined layout and visual polish.

---

## 6. How to Read This Repo as an Employer

If you’re reviewing this repo as a hiring manager or engineer, the most interesting parts to look at are:

- **Architecture & docs**
  - `docs/` – project plans and design documents.
- **Backend**
  - `backend/src/api/` – API surface.
  - `backend/src/orchestrator/` – chat routing, retrieval, model selection.
  - `backend/src/memory/` – DB + vector store integrations.
- **Features**
  - `backend/src/features/` – tasks, memory, analytics, exports.   

Even if some pieces are still work‑in‑progress, the repo and plan show:

- How I think about **system design**.
- How I break down a large, ambitious idea into phases.
- How I design AI‑powered systems that are **safe, traceable, and maintainable**, not just flashy demos.

---

## 7. Quick Start (Conceptual)

> Exact commands may change as the project evolves; this is the high‑level flow, not a locked‑in setup script.

1. Clone the repo and create a virtual environment.
2. Start the backend (FastAPI).
3. Start the InfinityWindow UI.
4. Create a project and set its local root path.
5. Attach documents and/or repositories.
6. Start chatting – and let InfinityWindow handle the memory, organization, and retrieval for you.

---

If you’d like, I can also:

- Add a shorter “Executive Summary” section at the top for non‑technical hiring managers.
- Add a small “Demo scenarios” section (“Show me all tasks we discussed about authentication”, “Explain the architecture in this repo”, etc.) to make the capabilities concrete.
::contentReference[oaicite:26]{index=26}
