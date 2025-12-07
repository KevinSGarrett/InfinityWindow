# 16) LLM Evaluation Harness

Goals:
- Deterministic **record/replay** of responses for regression testing
- **Routing & fallback** verification (auto submode, fallback chain)
- **Safety**: prompt‑injection red‑team prompts with policy assertions

Approach:
- Provide a stub layer: env `LLM_MODE=stub` → returns canned JSON (choice, tokens)
- Cassette format includes: input, mode, chosen_model, output, token_count, errors
- Metamorphic tests: paraphrase prompts but assert invariants (no shell ops; no PII echo; format clauses)
- Telemetry validation: `_LLM_TELEMETRY_COUNTERS` increments match calls/fallbacks/errors

Test IDs:
- **T-LLM-01..08**: routing/fallback correctness
- **T-LLM-09..16**: safety policy assertions
- **T-LLM-17..24**: determinism under replay
