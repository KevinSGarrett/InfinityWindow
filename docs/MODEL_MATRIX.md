# InfinityWindow – Model & Routing Matrix (Design)

Status: Design only – not implemented yet. Current runtime chat-mode defaults live in `backend/app/llm/openai_client.py` (also summarized in `docs/CONFIG_ENV.md`): `auto:gpt-4.1`, `fast:gpt-4.1-mini`, `deep:gpt-5.1`, `budget:gpt-4.1-nano`, `research:o3-deep-research`, `code:gpt-5.1-codex`. Autopilot role aliases below remain design-only until the corresponding modules exist.

This document defines **which LLM model** should be used for each subsystem  
(chat modes, Autopilot manager, workers, ingestion, summaries, etc.) and  
where to wire those choices in the codebase. It is based on `Updated_Project_Plans/Updated_Project_Plan_2_Model_Matrix.txt`.

Chat mode mapping in section 4 reflects the **current** behavior of `backend/app/llm/openai_client.py` and the `OPENAI_MODEL_*` env vars; any drift should be fixed by updating this doc or the code to match. Autopilot‑specific role aliases and helpers described elsewhere in this file are **design‑only** until the corresponding Autopilot modules exist.

---

## 1. Naming Conventions

We use two layers of naming:

1. **Chat modes** (existing, user‑facing):
   - `auto`, `fast`, `deep`, `budget`, `research`, `code`.
   - Selected in the chat UI; already wired into `openai_client.py`.
2. **Role aliases** (planned, backend‑internal):
   - Logical names like `summary`, `snapshot`, `blueprint`, `manager`, `worker_code`, `intent`, etc.
   - Each maps to an env var such as `OPENAI_MODEL_MANAGER`.
   - Used by Autopilot and ingestion subsystems, not exposed directly in the UI.

---

## 2. Global Model Config (Env Variables)

### 2.1 Chat mode envs (current)

These already exist and are used in `backend/app/llm/openai_client.py`:

- `OPENAI_MODEL_AUTO`
- `OPENAI_MODEL_FAST`
- `OPENAI_MODEL_DEEP`
- `OPENAI_MODEL_BUDGET`
- `OPENAI_MODEL_RESEARCH`
- `OPENAI_MODEL_CODE`

If unset, `_DEFAULT_MODELS` provides fallbacks (see `CONFIG_ENV.md` and `SYSTEM_OVERVIEW.md`).

### 2.2 Role alias envs (planned)

New env vars (to be read by Autopilot subsystems via helper functions):

- `OPENAI_MODEL_SUMMARY` – conversation summaries, short doc summaries.
- `OPENAI_MODEL_SNAPSHOT` – project snapshot generation.
- `OPENAI_MODEL_BLUEPRINT` – blueprint outline extraction & merge.
- `OPENAI_MODEL_PLAN_TASKS` – PlanNode → Task decomposition.
- `OPENAI_MODEL_MANAGER` – ManagerAgent planning & retrospectives.
- `OPENAI_MODEL_WORKER_CODE` – code worker (feature impl/refactors).
- `OPENAI_MODEL_WORKER_TEST` – test worker (test design/analysis).
- `OPENAI_MODEL_WORKER_DOC` – docs worker (docs sync).
- `OPENAI_MODEL_ALIGNMENT` – alignment checks for edits/commands.
- `OPENAI_MODEL_INTENT` – intent classifier for chat messages.
- `OPENAI_MODEL_RESEARCH_DEEP` – deep/advanced research tasks.

### 2.3 Embeddings

One env var for embeddings:

- `OPENAI_EMBEDDING_MODEL`
  - Recommended default: `text-embedding-3-small`.
  - Used for messages/docs/memory/plan/ingestion.

`CONFIG_ENV.md` is the canonical place to document current defaults and overrides; as Autopilot code lands, it should be updated to reflect real usage.

---

## 3. Recommended Defaults

These are **design recommendations** when env vars are not set. Before marking any role alias or mode as “implemented”, ensure the actual models used in `backend/app/llm/openai_client.py` and your environment variables match these values (or adjust this matrix to reflect reality).

### 3.1 Chat mode defaults

- **Runtime (current code / CONFIG_ENV.md)**:
  - `OPENAI_MODEL_AUTO`   → `gpt-4.1`
  - `OPENAI_MODEL_FAST`   → `gpt-4.1-mini`
  - `OPENAI_MODEL_DEEP`   → `gpt-5.1`
  - `OPENAI_MODEL_BUDGET` → `gpt-4.1-nano`
  - `OPENAI_MODEL_RESEARCH` → `o3-deep-research`
  - `OPENAI_MODEL_CODE`   → `gpt-5.1-codex`

- **Design targets (adjust if you change runtime)**:
  - `OPENAI_MODEL_AUTO`   → `gpt-4.1-mini`
  - `OPENAI_MODEL_FAST`   → `gpt-4.1-nano`
  - `OPENAI_MODEL_DEEP`   → `gpt-5.1`
  - `OPENAI_MODEL_BUDGET` → `gpt-4.1-nano`
  - `OPENAI_MODEL_RESEARCH` → `o3-deep-research`
  - `OPENAI_MODEL_CODE`   → `gpt-5.1` (or `gpt-5.1-codex`)

### 3.2 Role alias defaults

- `OPENAI_MODEL_SUMMARY`       → `gpt-4.1-nano`
- `OPENAI_MODEL_SNAPSHOT`      → `gpt-4.1-mini`
- `OPENAI_MODEL_BLUEPRINT`     → `gpt-4.1-mini`
- `OPENAI_MODEL_PLAN_TASKS`    → `gpt-5-mini`
- `OPENAI_MODEL_MANAGER`       → `gpt-5.1`
- `OPENAI_MODEL_WORKER_CODE`   → `gpt-5.1`
- `OPENAI_MODEL_WORKER_TEST`   → `gpt-4.1-mini` or `gpt-5-mini`
- `OPENAI_MODEL_WORKER_DOC`    → `gpt-4.1-mini`
- `OPENAI_MODEL_ALIGNMENT`     → `gpt-4.1-nano`
- `OPENAI_MODEL_INTENT`        → `gpt-4.1-nano`
- `OPENAI_MODEL_RESEARCH_DEEP` → `o3-deep-research`

### 3.3 Embeddings

- `OPENAI_EMBEDDING_MODEL` → `text-embedding-3-small`

---

## 4. Chat Modes → Models (Current Surface)

**File:** `backend/app/llm/openai_client.py`

Responsibilities:

- Map `mode` (`auto`/`fast`/…) to concrete model IDs using:
  - Env vars `OPENAI_MODEL_*`.
  - `_DEFAULT_MODELS` as fallback.
- Implement `_infer_auto_submode(messages)`:
  - Code‑heavy → `code`.
  - Long/research‑like → `research`.
  - Very short/simple → `fast`.
  - Everything else → `deep`.
- Apply fallback chain when chosen model fails:
  - Primary model → `OPENAI_MODEL_AUTO` → `OPENAI_MODEL_FAST`.
- Track routing and fallback telemetry in `_LLM_TELEMETRY_COUNTERS`.

`SYSTEM_OVERVIEW.md` and `CONFIG_ENV.md` document the current behavior; this file (`MODEL_MATRIX.md`) extends it with Autopilot‑role planning.

---

## 5. Subsystems → Role Aliases (Design)

### 5.1 Blueprint ingestion & Plan generation

**Use cases**

- Chunk‑level outline extraction from a large blueprint doc.
- Global outline merge into a PlanNode tree.
- PlanNode → Task decomposition.

**Recommended role aliases**

- Outline extraction & merge: `blueprint` → `OPENAI_MODEL_BLUEPRINT`.
- PlanNode → Task: `plan_tasks` → `OPENAI_MODEL_PLAN_TASKS`.

**Implementation targets (future)**

- `backend/app/services/blueprints.py`:
  - `generate_plan_from_document(document_id: int, ...)`
  - `generate_tasks_for_plan_node(plan_node_id: int, ...)`
- These functions should call:
  - `call_model_for_role("blueprint", messages=[...])`
  - `call_model_for_role("plan_tasks", messages=[...])`

### 5.2 Conversation summaries & Project Snapshot

**Use cases**

- Rolling short/detailed conversation summaries.
- ProjectSnapshot documents.

**Role aliases**

- Conversation summaries: `summary` → `OPENAI_MODEL_SUMMARY`.
- Snapshots: `snapshot` → `OPENAI_MODEL_SNAPSHOT`.

**Targets (future)**

- `backend/app/services/conversation_summaries.py`:
  - `update_conversation_summary(conversation_id: int)`
- `backend/app/services/snapshot.py`:
  - `refresh_project_snapshot(project_id: int)`

Both use `call_model_for_role("summary", ...)` / `call_model_for_role("snapshot", ...)`.

### 5.3 ManagerAgent (Autopilot planning)

**Use cases**

- Selecting next tasks and runs.
- Starting/advancing ExecutionRuns.
- Explaining current plan.
- Running retrospectives and refine_plan.

**Role alias**

- `manager` → `OPENAI_MODEL_MANAGER`.

**Targets (future)**

- `backend/app/services/manager.py`:
  - `choose_next_tasks`, `start_run_for_next_task`, `advance_run`, `explain_plan`, `record_run_outcome`, `refine_plan`, etc.
- All LLM calls from ManagerAgent should use:
  - `call_model_for_role("manager", messages=[...], tools=[...])`

Manager internal calls should **not** use `mode="auto"`; they use explicit role + env configuration.

### 5.4 Worker agents (code/test/docs)

**Use cases**

- `code_worker`: implement/refactor code using Files/Terminal/Search.
- `test_worker`: design and run tests, interpret failures.
- `doc_worker`: keep docs and blueprints in sync with code.

**Role aliases**

- `worker_code` → `OPENAI_MODEL_WORKER_CODE`.
- `worker_test` → `OPENAI_MODEL_WORKER_TEST`.
- `worker_doc` → `OPENAI_MODEL_WORKER_DOC`.

**Targets (future)**

- `backend/app/services/workers.py`:
  - `run_code_worker(context_bundle, tools)`
  - `run_test_worker(context_bundle, tools)`
  - `run_doc_worker(context_bundle, tools)`
- Each should call:
  - `call_model_for_role("worker_code" | "worker_test" | "worker_doc", ...)`

### 5.5 Alignment checks

**Use cases**

- Evaluate “Is this file edit / terminal command aligned with current plan/decisions?”

**Role alias**

- `alignment` → `OPENAI_MODEL_ALIGNMENT`.

**Target (future)**

- `backend/app/services/alignment.py`:
  - `check_alignment(project_id, action_type, action_payload) -> AlignmentResult`
- Workers or run orchestrator will call:
  - `call_model_for_role("alignment", messages=[...])`

### 5.6 Intent classification

**Use cases**

- Classify each user message as:
  - `QUESTION`, `START_BUILD`, `CONTINUE_BUILD`, `PAUSE_AUTOPILOT`, `ADJUST_PLAN`, `UPDATE_REQUIREMENTS`, `OTHER`.

**Role alias**

- `intent` → `OPENAI_MODEL_INTENT`.

**Target (future)**

- `backend/app/llm/intent_classifier.py`:
  - `classify_intent(project_name, snapshot_snippet, last_messages, new_message) -> {intent, confidence, notes}`
- Chat endpoint:
  - Calls classifier before `generate_reply_from_history`.
  - Delegates to ManagerAgent on high‑confidence non‑QUESTION intents.

### 5.7 Research / web‑style tasks

**Use cases**

- Deep architecture/research tasks not directly tied to code.

**Role alias**

- `research_deep` → `OPENAI_MODEL_RESEARCH_DEEP`.

**Targets (future)**

- Manager or dedicated research helpers call:
  - `call_model_for_role("research_deep", ...)`

---

## 6. Backend Helpers (Design)

To make these mappings manageable, `openai_client.py` should add:

```python
_ROLE_ENV_VARS = {
    "summary": "OPENAI_MODEL_SUMMARY",
    "snapshot": "OPENAI_MODEL_SNAPSHOT",
    "blueprint": "OPENAI_MODEL_BLUEPRINT",
    "plan_tasks": "OPENAI_MODEL_PLAN_TASKS",
    "manager": "OPENAI_MODEL_MANAGER",
    "worker_code": "OPENAI_MODEL_WORKER_CODE",
    "worker_test": "OPENAI_MODEL_WORKER_TEST",
    "worker_doc": "OPENAI_MODEL_WORKER_DOC",
    "alignment": "OPENAI_MODEL_ALIGNMENT",
    "intent": "OPENAI_MODEL_INTENT",
    "research_deep": "OPENAI_MODEL_RESEARCH_DEEP",
}
```

And defaults:

```python
_ROLE_DEFAULT_MODELS = {
    "summary": "gpt-4.1-nano",
    "snapshot": "gpt-4.1-mini",
    "blueprint": "gpt-4.1-mini",
    "plan_tasks": "gpt-5-mini",
    "manager": "gpt-5.1",
    "worker_code": "gpt-5.1",
    "worker_test": "gpt-4.1-mini",
    "worker_doc": "gpt-4.1-mini",
    "alignment": "gpt-4.1-nano",
    "intent": "gpt-4.1-nano",
    "research_deep": "o3-deep-research",
}
```

Helpers:

```python
def get_model_for_role(role: str) -> str:
    env_var = _ROLE_ENV_VARS.get(role)
    if env_var:
        override = os.getenv(env_var)
        if override:
            return override
    return _ROLE_DEFAULT_MODELS[role]

def call_model_for_role(role: str, messages: list[dict], **kwargs):
    model = get_model_for_role(role)
    return _call_model(model=model, messages=messages, **kwargs)
```

All Autopilot subsystems should call `call_model_for_role` instead of hard‑coding model strings.

---

## 7. Embeddings & Ingestion Batching

**Files:** `backend/app/llm/embeddings.py`, `backend/app/ingestion/docs_ingestor.py`, `backend/app/ingestion/github_ingestor.py`, `backend/app/vectorstore/chroma_store.py`.

Current implementation:

- Centralized embedding model selection:

```python
def get_embedding_model() -> str:
    return os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
```

- `embed_texts_batched(texts: list[str], model: str | None = None) -> list[list[float]]`:
  - Estimate tokens per text.
  - Accumulate into batches capped by:
    - `MAX_EMBED_TOKENS_PER_BATCH` (e.g., 50k).
    - `MAX_EMBED_ITEMS_PER_BATCH` (e.g., 256).
  - Call embeddings API per batch.
  - Flatten results into original order.

- Repo ingestion already uses this helper (Docs tab → ingestion jobs). Blueprint ingestion should reuse it when implemented.

Related env vars (first two are live; the last two are part of the Autopilot design):

- `MAX_EMBED_TOKENS_PER_BATCH`
- `MAX_EMBED_ITEMS_PER_BATCH`
- `MAX_CONTEXT_TOKENS_PER_CALL`
- `AUTOPILOT_MAX_TOKENS_PER_RUN`

---

## 8. Cost Management Patterns (Guidance)

Use small models for:

- Conversation summaries (`summary`).
- Simple intent classification (`intent`).
- Lightweight alignment checks (`alignment`) with short context.

Use mid‑tier models for:

- Project snapshots (`snapshot`).
- PlanNode → Task decomposition (`plan_tasks`) if deep models are too expensive.
- Test worker for moderate test design (`worker_test`).

Use strongest models for:

- Manager planning (`manager`).
- Code worker (`worker_code`) on complex refactors/features.
- Deep research tasks (`research_deep`).

Separating chat modes from role aliases lets you:

- Keep user‑facing chat on cheaper models when appropriate.
- Reserve expensive models for high‑leverage internal tasks (planning, refactors).

---

## 9. Implementation Checklist (for Future Work)

When implementing Autopilot and scalable ingestion:

1. **Backend helpers**
   - Add `_ROLE_ENV_VARS`, `_ROLE_DEFAULT_MODELS`, `get_model_for_role`, `call_model_for_role`.
   - Add `get_embedding_model` + `embed_texts_batched`.
2. **Wire subsystems to roles**
   - Blueprints: `call_model_for_role("blueprint" | "plan_tasks", ...)`.
   - Conversation summaries: `call_model_for_role("summary", ...)`.
   - Snapshot: `call_model_for_role("snapshot", ...)`.
   - Manager: `call_model_for_role("manager", ...)`.
   - Workers: `call_model_for_role("worker_code" | "worker_test" | "worker_doc", ...)`.
   - Alignment: `call_model_for_role("alignment", ...)`.
   - Intent classifier: `call_model_for_role("intent", ...)`.
3. **Centralize embeddings**
   - Ensure all embedding callers use `get_embedding_model` and `embed_texts_batched`.
4. **Update docs**
   - Keep `CONFIG_ENV.md`, `SYSTEM_OVERVIEW.md`, and this file in sync with the actual wiring.
   - Add QA coverage in `TEST_PLAN.md` and `qa/` to confirm role → model routing behaves as expected.

Until then, treat this matrix as the **design reference** for how models should be selected and routed across InfinityWindow’s subsystems.


