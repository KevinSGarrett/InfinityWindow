# InfinityWindow – Requirements CRM

## Retrieval & context shaping — Status: Partial
- Message/doc/memory search and chat injection are live.
- Phase 1 includes:
  - Per-kind retrieval profiles (messages/docs/memory/tasks) with env-configurable `top_k` and `score_threshold` defaults/overrides via `RETRIEVAL_<KIND>_TOP_K` and `RETRIEVAL_<KIND>_SCORE_THRESHOLD`.
  - Shared retrieval helper used by chat and debug surfaces.
  - Retrieval telemetry (counts/aggregates) exposed through `GET /debug/telemetry` under the `retrieval` section.
  - Structured retrieval context debugger at `GET /conversations/{id}/debug/retrieval_context` returning profiles and message/doc/memory snippets (also powers the Usage tab inspector card).
- Future work:
  - Telemetry-driven tuning and per-surface strategies (e.g., different profiles for Search tab, Tasks automation, future Autopilot).
  - Blueprint/Autopilot-specific retrieval graph features once that roadmap starts.

