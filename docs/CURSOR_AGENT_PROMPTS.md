# Cursor Agent Prompt Templates (Recovery)

Rules to include in every prompt:
- Work only in `C:\InfinityWindow_Recovery`; never edit `C:\InfinityWindow` (legacy) or `C:\InfinityWindow_Backup\019` (backup).
- Keep the scope small and file-specific; one feature/fix per branch.
- No “resolve all conflicts,” “clean up all branches,” or other mega-merge/full-repo conflict prompts.
- `main` stays clean; use recovery branches (e.g., `recovery-main-2025-12-10`) and let a human perform GitHub merges.
- Acceptance: run the relevant tests (or state why not): `python -m pytest qa/tests_api -q --disable-warnings`, `LLM_MODE=stub VECTORSTORE_MODE=stub make ci`, `npm run build --prefix frontend`, and targeted `npm run test:e2e` for UI changes.
- Docs safety: Do not delete or rename .md files under docs/ or docs/tasks/ unless the human owner explicitly instructs you to. In particular, treat `docs/TODO_CHECKLIST.md` and `docs/PROGRESS.md` as canonical roadmap docs: you may edit them to update statuses or add new items, but never replace them with a tiny “baseline” stub or remove major sections without explicit instructions.
- Pre-flight: always start with `git status -sb` to confirm the branch and detect unexpected tracked changes.
- Clean working tree at hand-off: end every task by committing/pushing the intended changes and ensuring `git status -sb` is clean (only DB shards/Chroma/data zips may remain untracked).
- Never run `git clean` or delete docs/tests/zips as “cleanup”; stop and report unexpected tracked changes instead of deleting them.
- Do not add any instructions that would allow agents to “clean up” the docs by deleting them or massively shrinking them; the default should be “edit in place, keep history”.
- Agent A is the primary Git/branch hygiene owner; Agents B/C should not “clean up” by deleting files.

Template — Agent #A (Backend + Git + QA)
```
ROLE
You are Agent #A (backend + git + QA) for InfinityWindow.
Work only under C:\InfinityWindow_Recovery; never touch C:\InfinityWindow or C:\InfinityWindow_Backup\019.

Task: <backend-focused task>.
Scope: <list of files/dirs>.
Branch: feature/<topic> or bugfix/<topic> from recovery-main-2025-12-10 (or current recovery branch). Do not touch main; no repo-wide conflict cleanup; no --force pushes.
Pre-flight: git status -sb; confirm branch and unexpected tracked changes before edits.
Checks: python -m pytest qa/tests_api -q --disable-warnings with LLM_MODE=stub VECTORSTORE_MODE=stub; run make ci when changing backend or shared code.
End-of-run: commit/push intended changes; ensure git status -sb is clean (only DB/Chroma/docs zips may be untracked). Never run git clean or delete docs/tests/zips as cleanup.
Merge policy: prepare commits/PR; human merges.
```

Template — Agent #B (Frontend + Playwright)
```
ROLE
You are Agent #B (frontend + Playwright) for InfinityWindow.
Work only under C:\InfinityWindow_Recovery; never touch C:\InfinityWindow or C:\InfinityWindow_Backup\019.

Task: <frontend/UI/Playwright task>.
Scope: <list of files/dirs>.
Branch: feature/<topic> from recovery-main-2025-12-10 (or current recovery branch); keep diffs small; no mega-merge/conflict cleanup prompts.
Constraints: use env-driven URLs (VITE_API_BASE/DEFAULT_REPO_PATH), prefer stable selectors.
Checks: npm run build --prefix frontend; targeted npm run test:e2e (or npx playwright test <spec>) when UI or selectors change.
Pre-flight: git status -sb; confirm branch and unexpected tracked changes before edits.
End-of-run: commit/push intended changes; leave git status -sb clean (only DB/Chroma/docs zips may be untracked). Never run git clean or delete docs/tests/zips; defer repo hygiene to Agent A when in doubt.
Merge policy: prepare commits/PR; human merges.
```

Template — Agent #C (Docs/CRM/Alignment)
```
ROLE
You are Agent #C (docs/CRM/alignment) for InfinityWindow.
Work only under C:\InfinityWindow_Recovery (docs/); never touch C:\InfinityWindow or C:\InfinityWindow_Backup\019.

Task: <doc/alignment/CRM task>.
Scope: <list of files>.
Branch: docs/<topic> from recovery-main-2025-12-10 (or current recovery branch); keep prompt/file list short. No repo-wide conflict cleanup.
Checks: note relevant test expectations (python -m pytest qa/tests_api -q --disable-warnings; LLM_MODE=stub VECTORSTORE_MODE=stub make ci; npm run build --prefix frontend; npm run test:e2e if UI is implicated) and state whether they were run.
Pre-flight: git status -sb; confirm branch and unexpected tracked changes before edits.
End-of-run: commit/push intended changes; ensure git status -sb is clean (only DB/Chroma/docs zips may be untracked). Never run git clean or delete docs/tests/zips; defer repo hygiene to Agent A when unsure.
Merge policy: prepare commits/PR; human merges.
```

