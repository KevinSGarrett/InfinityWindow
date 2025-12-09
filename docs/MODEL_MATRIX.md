# InfinityWindow – Model Matrix (Design)

Status: Chat mode defaults below must stay in sync with `backend/app/llm/openai_client.py` and `docs/CONFIG_ENV.md`. Autopilot role aliases are **design-only** until the Autopilot modules ship.

Purpose: provide a single mapping from chat modes and planned Autopilot/ingestion roles to environment variables and default models, based on `Project_Plans/Updated_Project_Plans/Updated_Project_Plan_2_Model_Matrix.txt`. Use this to keep code, env files, and docs consistent.

See also: `docs/CONFIG_ENV.md` (env knobs) and `docs/SYSTEM_OVERVIEW.md` (current behavior overview).

---

## How to read this matrix

- Env vars override everything; if unset, use the defaults below.
- Chat modes are live today. Role aliases are planned for Autopilot/ingestion; treat them as design-only until the related services exist.
- If code defaults drift from this table, either align the code to these values or update both the table and `CONFIG_ENV.md` together.

---

## Chat modes (current surface)

| Mode  | Env var             | Default model (if unset) | Notes |
|-------|---------------------|---------------------------|-------|
| auto  | `OPENAI_MODEL_AUTO` | `gpt-4.1-mini`            | UI default; `_infer_auto_submode` still applies. |
| fast  | `OPENAI_MODEL_FAST` | `gpt-4.1-nano`            | Cheap/short replies. |
| deep  | `OPENAI_MODEL_DEEP` | `gpt-5.1`                 | Strong reasoning. |
| budget| `OPENAI_MODEL_BUDGET`| `gpt-4.1-nano`           | Lowest cost. |
| research | `OPENAI_MODEL_RESEARCH` | `o3-deep-research`  | Long-form research. |
| code  | `OPENAI_MODEL_CODE` | `gpt-5.1` (or `gpt-5.1-codex`) | For code-heavy prompts. |

---

## Role aliases (Autopilot & ingestion – design)

These map future subsystems to env vars. Defaults come from the model matrix plan; wire helpers like `get_model_for_role` / `call_model_for_role` to honor them when Autopilot lands.

| Role alias      | Env var                     | Default model |
|-----------------|-----------------------------|---------------|
| summary         | `OPENAI_MODEL_SUMMARY`      | `gpt-4.1-nano` |
| snapshot        | `OPENAI_MODEL_SNAPSHOT`     | `gpt-4.1-mini` |
| blueprint       | `OPENAI_MODEL_BLUEPRINT`    | `gpt-4.1-mini` |
| plan_tasks      | `OPENAI_MODEL_PLAN_TASKS`   | `gpt-5-mini` |
| manager         | `OPENAI_MODEL_MANAGER`      | `gpt-5.1` |
| worker_code     | `OPENAI_MODEL_WORKER_CODE`  | `gpt-5.1` |
| worker_test     | `OPENAI_MODEL_WORKER_TEST`  | `gpt-4.1-mini` (or `gpt-5-mini`) |
| worker_doc      | `OPENAI_MODEL_WORKER_DOC`   | `gpt-4.1-mini` |
| alignment       | `OPENAI_MODEL_ALIGNMENT`    | `gpt-4.1-nano` |
| intent          | `OPENAI_MODEL_INTENT`       | `gpt-4.1-nano` |
| research_deep   | `OPENAI_MODEL_RESEARCH_DEEP`| `o3-deep-research` |
| embeddings      | `OPENAI_EMBEDDING_MODEL`    | `text-embedding-3-small` |

---

## Routing & helpers (design intent)

- Add `_ROLE_ENV_VARS` / `_ROLE_DEFAULT_MODELS` to `openai_client.py` and expose `get_model_for_role` + `call_model_for_role`.
- Keep chat-mode routing (`_infer_auto_submode`, fallbacks) aligned with the chat table above.
- Centralize embeddings via `get_embedding_model()` and reuse `embed_texts_batched` for repo/blueprint ingestion.

---

## Where to update when things change

- Code: `backend/app/llm/openai_client.py` (chat routing, helpers), ingestion/Autopilot services when they exist.
- Docs: this file, `docs/CONFIG_ENV.md`, `docs/SYSTEM_OVERVIEW.md`, and any Autopilot design docs.
- Env: `backend/.env` (or deployment secrets) for overrides; keep QA/CI stubs consistent with these defaults.


