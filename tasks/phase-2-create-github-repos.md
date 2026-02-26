# Tasks: Phase 2 — Create Fresh GitHub Repositories

**Spec:** /specs/final-split-and-retirement.md

## Status

- Total: 4
- Complete: 0
- Remaining: 4

## Prerequisites

- Phase 1 complete (clean codebase, zero lint errors, bug fixed)

## Task List

### Task 1: Update pyproject.toml URLs for prompt app

- **Files:** `pyproject.toml`
- **Done when:** (1) `Homepage` URL updated to `https://github.com/josiahH-cf/automatr-prompt`. (2) `Repository` URL updated to `https://github.com/josiahH-cf/automatr-prompt`. (3) `pip install -e .` still works. (4) Commit the change
- **Criteria covered:** AC-4
- **Status:** [ ] Not started

### Task 2: Create josiahH-cf/automatr-prompt on GitHub and push

- **Files:** None (GitHub + git operations)
- **Done when:** (1) Empty repo `josiahH-cf/automatr-prompt` created on GitHub (no default files). (2) Local repo's `origin` remote updated to point to new repo. (3) Cleaned `main` branch pushed to `josiahH-cf/automatr-prompt`. (4) Branch protections configured (require CI to pass before merge). (5) Repo description set to: "Local prompt optimizer with reusable templates and llama.cpp integration"
- **Criteria covered:** AC-4
- **Status:** [ ] Not started

### Task 3: Create josiahH-cf/automatr-espanso on GitHub and push

- **Files:** None (GitHub + git operations, from `/home/josiah/automatr-espanso/`)
- **Done when:** (1) Empty repo `josiahH-cf/automatr-espanso` created on GitHub. (2) Remote `origin` added to local `/home/josiah/automatr-espanso/` pointing to new repo. (3) `main` branch pushed. (4) `pyproject.toml` URLs point to `josiahH-cf/automatr-espanso`. (5) Repo description set to: "Espanso automation GUI with template-to-trigger sync"
- **Criteria covered:** AC-5
- **Status:** [ ] Not started

### Task 4: Transfer relevant issues from legacy repo

- **Files:** None (GitHub operations)
- **Done when:** (1) Open issues on `josiahH-cf/automatr` reviewed. (2) Prompt-related issues transferred to `automatr-prompt`. (3) Espanso-related issues transferred to `automatr-espanso`. (4) Legacy-only issues closed with a note. (5) No orphaned open issues remain on the legacy repo
- **Criteria covered:** AC-4, AC-5
- **Status:** [ ] Not started

## Test Strategy

| Criterion | Verified by |
|-----------|-------------|
| AC-4 | Task 2: repo exists, code pushed, `git clone` + `pip install -e .` works |
| AC-5 | Task 3: repo exists, code pushed, `git clone` + install works |

## Rollback Strategy

GitHub repos can be deleted and recreated. Local git remotes can be re-pointed. No destructive operations on code.

## Session Log

<!-- Append after each session: date, completed, blockers -->
