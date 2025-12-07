# 11) Resilience & Recovery

**M-Res-01 – Backend kill/restart during chat** → no data loss; resume OK.  
**M-Res-02 – Kill during ingestion** → job ends as cancelled/failed; no partial state.  
**M-Res-03 – Power failure simulation** (kill DB process) → DB not corrupted.  
**M-Res-04 – Disk full during write** → error surfaced; system remains functional.  
**M-Res-05 – Chroma unavailable** → graceful degradation of search.  
**M-Res-06 – LLM provider 429/5xx burst** → retry/backoff/fallback chain.  
**M-Res-07 – Telemetry counter integrity after failures.**  
**M-Res-08 – Concurrency of 5 chats + ingestion + terminal.**  
**M-Res-09 – DB backup/restore correctness.**  
**M-Res-10 – Schema evolution/migration rehearsal (if introduced).**
