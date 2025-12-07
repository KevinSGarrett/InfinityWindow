# 10) Performance & Scale

**Targets (tune to your hardware):**
- Ingestion throughput: ≥ 250 files/s for small files; ≥ 5 MB/s for large files.
- Search 95p latency @ K=10: ≤ 150 ms from local embeddings.
- Chat 95p latency: tracked per‑mode; alerts if regression > 20% window‑over‑window.

**Workloads:**
- `SmallRepo` (50 files), `MedRepo` (5k files), `LargeRepo` (10k–50k files).  
- Mixed sizes, with 20% binary, 10% non‑ASCII names.

**Tests L-Perf-01..16:**
- L-Perf-01: Baseline ingestion (SmallRepo) – cold vs warm cache.
- L-Perf-02: Hash re‑ingestion (skip) – end‑to‑end ≤ 3s.
- L-Perf-03: LargeRepo throughput & memory ceiling.
- L-Perf-04: Search latency under concurrent chat (N=3).
- L-Perf-05: Terminal long-run CPU leak check (60 min soak).
- L-Perf-06: UI responsiveness @ 3 active ingestion jobs (if parallel allowed).
- ...

**Measurement:**
- Capture `/debug/telemetry` before/after; export JSON to `test-results/`.
- Record system perf counters (CPU, RAM) each 5s, diff and chart.
