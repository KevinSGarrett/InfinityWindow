# 9) Security – Threat Model & Tests

Approach: **STRIDE** by component + **OWASP Top 10** web vectors + **LLM prompt‑injection** hardening.

## Global

**K-SEC-01** – TLS/transport assumptions documented (loopback).  
**K-SEC-02** – CORS policy (UI origin only).  
**K-SEC-03** – Rate limiting on hot endpoints (chat, ingest).  
**K-SEC-04** – Input size limits & timeouts.

## Files

**K-SEC-10** – Path traversal attempted via `..` / UNC / symlinks → blocked.  
**K-SEC-11** – Null bytes and reserved device names (`CON`, `NUL`).  
**K-SEC-12** – Overwrite protection & backup on edits.

## Terminal

**K-SEC-20** – Shell metacharacters (`; & | > < ^`) escaped/blocked.  
**K-SEC-21** – No arbitrary environment variable leak.  
**K-SEC-22** – Process kill leaves no zombies; working dir fixed to project root.

## Chat/LLM

**K-SEC-30** – Prompt‑injection corpus (instruct to exfiltrate secrets) blocked at policy layer.  
**K-SEC-31** – Model refusal behavior validated; never runs terminal/FS operations without human action.  
**K-SEC-32** – PII redaction options (if configured) honored.  
**K-SEC-33** – Token logging excludes secrets.

## Web & UI

**K-SEC-40** – Stored/Reflected XSS via notes/memory/decision text → neutralized.  
**K-SEC-41** – Content‑Security‑Policy (if any) prevents inline script.
