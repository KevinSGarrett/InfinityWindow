# 12) Release Gates & CI

**Hard gates to ship a window to `main`:**
- All Smoke S-001..S-020 ✅
- All API Contract A-* ✅ (no new known‑bad)
- E2E U-* critical flows ✅
- Security K-SEC-10..K-SEC-22 (files/terminal injection) ✅
- Perf: no >20% regression vs last window on key metrics ✅
- Test report filled (template), artifacts attached ✅

**CI sequence (example):**
1. Backend unit/integration tests (`pytest -n auto --maxfail=1`)
2. Frontend build + Playwright E2E (headedless with video)
3. LLM‑stubbed determinism tests
4. Coverage gates fail below targets
5. Publish HTML reports + JSON telemetry to artifact store
