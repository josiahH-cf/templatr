# Tasks: Phase 4 — Retire Legacy Repository

**Spec:** /specs/final-split-and-retirement.md

## Status

- Total: 3
- Complete: 0
- Remaining: 3

## Prerequisites

- Phase 2 complete (both new repos exist and have code)
- Phase 3 complete (CI is green on both new repos)

## Task List

### Task 1: Tag final commit on legacy repo

- **Files:** None (git operations on `josiahH-cf/automatr`)
- **Done when:** (1) Current HEAD on `main` of the legacy repo is tagged as `v1.0.0-legacy-final`. (2) Tag is pushed to GitHub. (3) Tag message documents that this is the final release before the split into `automatr-prompt` and `automatr-espanso`
- **Criteria covered:** AC-6
- **Status:** [ ] Not started

### Task 2: Update legacy README with retirement notice

- **Files:** `README.md` (on the legacy `josiahH-cf/automatr` repo)
- **Done when:** (1) README begins with a prominent deprecation banner. (2) Banner links to `josiahH-cf/automatr-prompt` and `josiahH-cf/automatr-espanso`. (3) Migration instructions included (for users: "clone the new repo, run install.sh"). (4) Original README content preserved below the banner for historical reference. (5) Commit and push to `main`
- **Criteria covered:** AC-6
- **Status:** [ ] Not started

### Task 3: Archive the legacy repo on GitHub

- **Files:** None (GitHub settings)
- **Done when:** (1) `josiahH-cf/automatr` is set to archived (read-only) via GitHub settings. (2) Existing issues are closed with a note pointing to the new repos. (3) Repo description updated to: "ARCHIVED — Replaced by automatr-prompt and automatr-espanso". (4) Verify the repo is read-only (no new pushes, issues, or PRs accepted)
- **Criteria covered:** AC-6
- **Status:** [ ] Not started

## Test Strategy

| Criterion | Verified by |
|-----------|-------------|
| AC-6 | Task 1: tag exists on GitHub. Task 2: README shows deprecation notice. Task 3: repo is archived |

## Rollback Strategy

Repository archival can be undone via GitHub settings. Tags can be deleted. README can be reverted. All operations are reversible.

## Session Log

<!-- Append after each session: date, completed, blockers -->
