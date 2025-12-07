# 3) Test Suites – Overview

- **Smoke**: S-001..S-020 – health, projects list, create project, basic chat ping, docs tab render.
- **API Contract**: A-* – schema, validation, negative tests per endpoint.
- **Chat & Tasks**: C-* – routing, fallbacks, streaming, token limits, auto‑task updates.
- **Ingestion & Search**: D-* and E-* – hashing, batching, cancel/resume, Chroma parity, search recall.
- **Files & Terminal**: F-* and G-* – AI edits apply/rollback, safe terminal, long‑running jobs.
- **Telemetry & Usage**: H-* and J-* – counters, error increment, reset, UI parity.
- **UI E2E**: U-* – Playwright flows with screenshots/videos.
- **Security**: K-* – STRIDE/OWASP, prompt‑injection, path traversal, terminal injection.
- **Performance & Resilience**: L-* and M-* – load/soak/stress + crash/failure injection.
- **Accessibility**: N-* – keyboarding, roles/labels, contrast, screen reader.
- **Release Gates**: R-* – minimum checks to push a window to main.
