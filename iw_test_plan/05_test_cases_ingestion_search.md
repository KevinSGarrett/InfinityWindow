# 5) Ingestion & Search – Detailed Tests

**D-Docs-01 – Basic ingestion (happy path)**  
**D-Docs-02 – Re‑ingestion hash skip**  
**D-Docs-03 – Progress metrics snapshot**  
**D-Docs-04 – Cancel mid‑run; ensure no partial commits**  
**D-Docs-05 – History table parity (API vs UI)**  
**D-Docs-06 – Failure surfacing & error text**  
**D-Docs-07 – Telemetry snapshot & reset**  
**D-Docs-08 – Non‑ASCII filenames**  
**D-Docs-09 – Long paths (>260) on Windows**  
**D-Docs-10 – Large repo (10k files) throughput & memory**  
**D-Docs-11 – Binary files skipped & logged**  
**D-Docs-12 – Ingestion after DB/Chroma restore**

**E-Search-01 – Exact phrase vs fuzzy match**  
**E-Search-02 – Top‑K bounds and ordering stability**  
**E-Search-03 – Query with code blocks and markdown**  
**E-Search-04 – Stop‑word handling**  
**E-Search-05 – Namespace isolation by project**  
**E-Search-06 – Stale index after file delete**  
**E-Search-07 – Multi‑language documents**  
**E-Search-08 – Performance @ K=50 (95p latency)**  
**E-Search-09 – Error injection: Chroma offline**  
**E-Search-10 – Telemetry parity**
