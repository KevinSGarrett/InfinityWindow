[PS.SAFETY.FS.001] Filesystem confinement — Correct
Plan: Updated_Project_Plan_2_AUTOPILOT_LIMITATIONS.txt::3.1 Filesystem safety
Expected contract:
- All file ops normalized and confined to project local_root_path (no path escape).
Observed evidence:
- backend/app/api/main.py:685-706 — Filesystem helpers use _safe_join to confine paths under project local_root_path and enforce relative paths.
Rationale: Filesystem helpers use _safe_join to confine paths under project local_root_path and enforce relative paths.
Owner: TBD; Suggested milestone: Safety

[PT.INGEST.EMBED.001] embed_texts_batched & embed_batch helper — Correct
Plan: Updated_Project_Plan_2_Ingestion_Plan.txt::T1.1 Centralized batched embeddings helper
Expected contract:
- Centralized embeddings batching respecting MAX_EMBED_TOKENS_PER_BATCH and MAX_EMBED_ITEMS_PER_BATCH using embed_batch wrapper.
Observed evidence:
- backend/app/llm/embeddings.py:92-165 — embed_texts_batched implements batching with token/item caps and env overrides for embedding model.
Rationale: embed_texts_batched implements batching with token/item caps and env overrides for embedding model.
Owner: TBD; Suggested milestone: Phase T

[PT.INGEST.MODEL.001] IngestionJob model and endpoints — Correct
Plan: Updated_Project_Plan_2_Ingestion_Plan.txt::T1.2 IngestionJob model for resumable ingestion
Expected contract:
- IngestionJob with progress fields plus POST/GET endpoints for project-scoped ingestion jobs and cancel.
Observed evidence:
- backend/app/db/models.py:422-470 — IngestionJob model plus project-scoped ingestion job endpoints (create/list/cancel) implemented.
Rationale: IngestionJob model plus project-scoped ingestion job endpoints (create/list/cancel) implemented.
Owner: TBD; Suggested milestone: Phase T

[PT.INGEST.MODEL.002] FileIngestionState hash tracking — Correct
Plan: Updated_Project_Plan_2_Ingestion_Plan.txt::T2.2 Hash-based incremental ingestion
Expected contract:
- file_ingestion_state table tracking sha256 per project/path for incremental re-ingestion.
Observed evidence:
- backend/app/db/models.py:451-470 — file_ingestion_state table exists with project/path unique constraint and sha256 tracking.
Rationale: file_ingestion_state table exists with project/path unique constraint and sha256 tracking.
Owner: TBD; Suggested milestone: Phase T
