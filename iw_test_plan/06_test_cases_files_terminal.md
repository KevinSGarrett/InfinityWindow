# 6) Files & Terminal – Detailed Tests

## Files UI + AI Edits

**F-Files-01 – Tree loads and expands**  
**F-Files-02 – Preview encoding (UTF‑8/UTF‑16/CRLF)**  
**F-Files-03 – AI edit – dry‑run diff renders**  
**F-Files-04 – AI edit – apply patch; creates backup**  
**F-Files-05 – AI edit – rollback restores backup**  
**F-Files-06 – Conflict on changed file – reject with guidance**  
**F-Files-07 – Path traversal blocked (`..`, UNC, symlinks)**  
**F-Files-08 – Very large file (size limit)**  
**F-Files-09 – Binary file protection**  
**F-Files-10 – Non‑ASCII path support**  
**F-Files-11 – Telemetry counters**  
**F-Files-12 – Permissions error surfaces gracefully**

## Terminal Integration

**G-Term-01 – Start shell process (PowerShell)**  
**G-Term-02 – Stream stdout/stderr correctly**  
**G-Term-03 – Exit code propagation**  
**G-Term-04 – Cancel (SIGINT/kill) and cleanup**  
**G-Term-05 – Long‑running process watch‑dog**  
**G-Term-06 – Environment isolation (project root)**  
**G-Term-07 – Injection hardening (no raw `; & |` chaining)**  
**G-Term-08 – Path quoting/escaping**  
**G-Term-09 – Output encoding (non‑ASCII)**  
**G-Term-10 – Disk‑full during output**  
**G-Term-11 – Concurrency – 3 terminals**  
**G-Term-12 – Telemetry parity**
