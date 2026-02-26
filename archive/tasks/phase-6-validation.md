# Tasks: Phase 6 — Validation and Hard Separation

**Spec:** /specs/final-split-and-retirement.md

## Status

- Total: 3
- Complete: 0
- Remaining: 3

## Prerequisites

- Phase 1–3 complete (both repos on GitHub with CI)
- Phase 5 complete (governance docs in place)

## Task List

### Task 1: Independence verification — automatr-prompt

- **Files:** None (fresh clone verification)
- **Done when:** (1) `git clone josiahH-cf/automatr-prompt` into an isolated temp directory. (2) `./install.sh` completes without errors. (3) `ruff check .` returns 0 errors. (4) `pytest` passes all tests (58+ tests, 0 failures). (5) App launches and displays templates. (6) `grep -rn "automatr_espanso\|automatr-espanso" .` returns zero results (excluding docs that intentionally reference the sister project). (7) No imports reference the espanso app
- **Criteria covered:** AC-7
- **Status:** [ ] Not started

### Task 2: Independence verification — automatr-espanso

- **Files:** None (fresh clone verification)
- **Done when:** (1) `git clone josiahH-cf/automatr-espanso` into an isolated temp directory. (2) Install process completes without errors. (3) `pytest` passes all tests (14+ tests, 0 failures). (4) GUI and CLI both launch without errors. (5) `grep -rn "automatr_prompt\|automatr-prompt" .` returns zero results (excluding docs). (6) No imports reference the prompt app. (7) `pyproject.toml` does not list `requests` as a dependency (espanso app uses PyYAML, not requests for LLM)
- **Criteria covered:** AC-7
- **Status:** [ ] Not started

### Task 3: Cross-dependency audit

- **Files:** None (verification only)
- **Done when:** (1) Neither app's `pyproject.toml` references the other as a dependency. (2) No shared filesystem paths are assumed (each uses its own `~/.config/` subdirectory). (3) CI pipelines are fully independent (neither triggers the other). (4) Template JSON files in each repo are self-contained (no symlinks or shared paths). (5) Document results in an independence verification summary (can be a comment in the spec or a brief note in this task file's session log)
- **Criteria covered:** AC-7
- **Status:** [ ] Not started

## Test Strategy

| Criterion | Verified by |
|-----------|-------------|
| AC-7 | All tasks: fresh clone builds, tests pass, grep confirms no cross-references |

## Rollback Strategy

Verification-only phase — no code changes. If issues are found, they are fixed in the relevant app's repo and this phase is re-run.

## Session Log

<!-- Append after each session: date, completed, blockers -->
