# Progress Log (Recovery Baseline)

## Recovery 2025-12-10
- Restored a clean copy from `C:\InfinityWindow_Backup\019` into `C:\InfinityWindow_Recovery` after merge conflicts and DB drift in the legacy repo.
- Rebuilt SQLite and Chroma stores from models; validated the stack in stub mode.
- Rewired GitHub via staging branch `recovery-main-2025-12-10`; keep `main` clean and human-merged.
- New guardrails: work only in `C:\InfinityWindow_Recovery`, keep branches small (one feature/fix), avoid repo-wide conflict/branch cleanup prompts, and keep human ownership of merges.
- Recommended checks before PRs: `python -m pytest qa/tests_api` with `LLM_MODE=stub` / `VECTORSTORE_MODE=stub` and `npm run build --prefix frontend`.

