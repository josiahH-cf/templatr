# Tasks: Phase 3 — CI/CD Setup

**Spec:** /specs/final-split-and-retirement.md

## Status

- Total: 3
- Complete: 0
- Remaining: 3

## Prerequisites

- Phase 2 complete (both repos exist on GitHub with code pushed)

## Task List

### Task 1: Create CI workflow for automatr-prompt

- **Files:** `.github/workflows/ci.yml` (in `automatr-prompt` repo)
- **Done when:** (1) Workflow triggers on `push` and `pull_request` to `main`. (2) Runs on `ubuntu-latest` with Python version matrix: 3.10, 3.11, 3.12. (3) Steps: checkout → setup-python → `pip install -e .[dev]` → `ruff check .` → `pytest`. (4) Existing `copilot-setup-steps.yml` retained for Copilot agent use. (5) Push to `main` triggers a successful CI run (green badge). (6) Commit and push
- **Criteria covered:** AC-4
- **Status:** [ ] Not started

### Task 2: Create CI workflow for automatr-espanso

- **Files:** `.github/workflows/ci.yml` (in `automatr-espanso` repo at `/home/josiah/automatr-espanso/`)
- **Done when:** (1) Workflow triggers on `push` and `pull_request` to `main`. (2) Runs on `ubuntu-latest` with Python version matrix: 3.10, 3.11, 3.12. (3) Steps: checkout → setup-python → `pip install -e .[dev]` → lint → `pytest`. (4) First CI run passes. (5) Commit and push
- **Criteria covered:** AC-5
- **Status:** [ ] Not started

### Task 3: Verify CI independence

- **Files:** None (verification only)
- **Done when:** (1) Push a trivial commit to `automatr-prompt` — only its CI runs. (2) Push a trivial commit to `automatr-espanso` — only its CI runs. (3) Neither pipeline references or depends on the other repo. (4) Both pipelines show green status badges
- **Criteria covered:** AC-4, AC-5
- **Status:** [ ] Not started

## Test Strategy

| Criterion | Verified by |
|-----------|-------------|
| AC-4 | Task 1, Task 3: CI runs green on push, lint + test pass |
| AC-5 | Task 2, Task 3: CI runs green on push, lint + test pass |

## Rollback Strategy

Workflow files can be reverted or deleted. CI failures don't affect app functionality.

## Session Log

<!-- Append after each session: date, completed, blockers -->
