# 1) Test Strategy & Policy

**Objective.** Drive InfinityWindow to *very high confidence* via layered verification:
- Unit → Contract → Integration → End‑to‑End → Non‑functional
- Static analysis → Property‑based & fuzzing → Fault injection → Observability checks

**Ground truth.** Absolute “zero defects” cannot be *guaranteed* in any non‑trivial system, but we maximize coverage with:
- Complete feature mapping (see `02_traceability_matrix.csv`)
- Deterministic stubbing for LLM and file system where needed
- Adversarial inputs and negative testing for every API
- Cross‑checks: API vs UI parity, telemetry vs state, DB vs UI

## Scope

**Implemented today (primary target)**
- Projects / Conversations / Messages and chat pipeline
- Tasks (auto‑update loop), Usage tab, Decision Log, Notes, Memory
- Docs ingestion (local repo), embeddings store, semantic search
- Files UI with AI edits
- Terminal integration (PowerShell), process lifecycle
- Telemetry & `/debug/telemetry`
- Windows 10/11 environment

**Planned (design‑only)** — create “red” tests that MUST fail until implemented:
- Autopilot (manager/workers), learning layer and plan runs
- Full model/role routing per `MODEL_MATRIX.md`

## Environments

- **Dev**: `C:\InfinityWindow`
- **QA/Staging**: `C:\InfinityWindow_QA` (fresh DB & Chroma per run)
- Optional: WSL/Win path-compatibility checks

## Coverage Philosophy

- **APIs**: >= 95% endpoint-level coverage (happy+negative), schema and validation checks
- **Core Python**: >= 85% branch coverage for pure logic; property-based on data mappers/parsers
- **UI**: Playwright flows for every right-column tab + projects/conversations/messages
- **Security**: STRIDE/OWASP checklists turned into runnable tests
- **Performance**: SLOs for ingestion throughput, search latency, and chat latency; soak stability

## Tooling

- **pytest** with `TestClient` for FastAPI; Hypothesis for properties; `pytest-xdist` for parallel
- **Playwright** for UI; `--trace on` and video for flake analysis
- **Python fault injection** helpers to simulate network/DB/disk failures
- **LLM stub** layer with record/replay cassettes and adversarial prompts
- **Coverage**: `coverage.py` + Playwright code coverage
