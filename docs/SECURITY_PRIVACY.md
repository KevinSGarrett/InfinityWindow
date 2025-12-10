# InfinityWindow Security & Privacy Notes

This document summarizes how InfinityWindow handles data, where it is stored, and the main security/privacy considerations as of 2025‑12‑02.

> This is not a formal security audit. It is a working document to guide safer usage and future hardening.

---

## 1. Data handled by InfinityWindow

### 1.1 Local data

Stored primarily in:

- **SQLite database** (`backend/infinitywindow.db` by default)
  - Projects and their metadata.
  - Conversations and messages.
  - Tasks, docs, memory items, decisions.
  - Usage/auxiliary records.

- **Chroma vector store** (`backend/chroma_data/`)
  - Embeddings of messages, docs, and memory items.
  - Text content (or fragments) associated with those embeddings.

- **Filesystem operations**
  - Files under the project root (as configured per project).
  - AI edits are applied to real files on disk when accepted.
  - Filesystem endpoints guard against path escapes; `fs/read` accepts `file_path` or `subpath`, and `fs/ai_edit` accepts `instruction` or `instructions`.
  - Telemetry and usage are local: `GET /debug/telemetry` exposes in-memory counters; `GET /conversations/{id}/usage` shows model usage/cost per conversation.

### 1.2 External data (LLM provider)

When you send a message or request an AI operation:

- Relevant text is sent to the configured LLM API (e.g., OpenAI).
- This may include:
  - Conversation text.
  - Extracts from docs, memory, or files.
  - System prompts and instructions.

The exact data sent depends on the prompt composition logic in `app/llm/openai_client.py` and related helpers.

---

## 2. Secrets and credentials

- **OpenAI API key**:
  - Stored in environment variables or `.env` (backend).
  - Should not be committed to version control.
  - Used only by the backend to call the LLM API.

- **Other credentials**:
  - At present there are no additional third‑party integrations documented (e.g., Slack/LibreChat integrations are not active here).

Best practices:

- Keep `.env` out of version control.
- Avoid printing secrets in logs.

---

## 3. Access model

InfinityWindow is currently designed as a **single‑user local tool**:

- It assumes:
  - You control the machine where backend and frontend run.
  - You control access to the DB and Chroma directories.
  - There is no explicit multi‑user authentication/authorization layer.

Implications:

- Anyone who can reach the backend (e.g., `http://127.0.0.1:8000`) and frontend can act as “you”.
- For production or shared environments, you would need:
  - Network‑level controls (firewall, VPN).
  - An authentication layer in front of FastAPI (e.g., reverse proxy with auth).

---

## 4. Filesystem & terminal safety

### 4.1 Filesystem

- File operations are scoped to a **project root path** configured per project.
- Endpoints under `/projects/{project_id}/fs/*` resolve relative paths safely and reject attempts to traverse outside the project root (e.g., `..` segments). `fs/read` accepts `file_path` or `subpath`; `fs/ai_edit` accepts `instruction` or `instructions`.

Recommendations:

- Set project roots to dedicated directories, not your entire system drive.
- Review file edit operations before accepting AI‑proposed diffs.

### 4.2 Terminal

- Terminal commands are executed via backend endpoints (see `docs/API_REFERENCE_UPDATED.md`).
- InfinityWindow does **not** prevent destructive commands by itself.

Recommendations:

- Treat the Terminal tab as you would a normal shell:
  - Be cautious with `rm`, `del`, `format`, or recursive deletes.
  - Prefer running tests and harmless diagnostics.

Future Autopilot features (see `AUTOPILOT_LIMITATIONS.md`) will add an explicit terminal allowlist and alignment layer for **autonomous** commands, but those safeguards do not remove the need for human review when running manual commands.

---

## 5. Privacy considerations

- **Local storage**:
  - All data (projects, messages, embeddings) lives on your machine by default.
  - Backups and retention are under your control (e.g., manual DB/Chroma backups).

- **Cloud LLM provider**:
  - Text sent to the LLM provider may be logged or used per that provider’s terms.
  - If this is a concern, review:
    - The provider’s data retention and training policies.
    - Options to disable data retention where available.

Recommendations:

- Avoid sending highly sensitive or regulated data (e.g., secrets, production PII) unless you have a compliant deployment and provider agreement.
- Use project scoping and memory/docs wisely to minimize unnecessary exposure of data.

---

## 6. Future hardening ideas

Items that can be addressed in future phases (tracked in `docs/PROGRESS.md` / `docs/TODO_CHECKLIST.md`):

- Add authentication and authorization mechanisms.
- Provide configuration for:
  - Redacting or masking certain data before LLM calls.
  - Per‑project policies about what content can be embedded or sent upstream.
- Encrypt local storage for DB and/or embeddings (where OS support is available).
- Provide clearer UI affordances when actions may be destructive.

Use this document as a living checklist for security/privacy topics; update it as the system or deployment model evolves.


