# Tasks: Phase 7 — Task System Reset

**Spec:** /specs/final-split-and-retirement.md

## Status

- Total: 3
- Complete: 0
- Remaining: 3

## Prerequisites

- Phase 6 complete (both apps verified as independent)

## Task List

### Task 1: Clean task/spec structure in automatr-prompt

- **Files:** `tasks/`, `specs/`, `archive/` (in `automatr-prompt` repo)
- **Done when:** (1) Completed phase task files remain in `/archive/tasks/` (already moved). (2) Completed spec remains in `/archive/specs/` (already moved). (3) Archived decision copy remains in `/archive/decisions/`. (4) Active decision `0001-template-ownership-split.md` stays in `/decisions/`. (5) Task and spec templates (`_TEMPLATE.md`) stay in `/tasks/` and `/specs/`. (6) This split's task files (phase-1 through phase-7) are moved to `/archive/tasks/` after they are all completed. (7) `archive/README.md` exists explaining the archive contents. (8) Commit and push
- **Criteria covered:** AC-9
- **Status:** [ ] Not started

### Task 2: Clean task structure in automatr-espanso

- **Files:** `tasks/`, `specs/` (in `automatr-espanso` repo at `/home/josiah/automatr-espanso/`)
- **Done when:** (1) If legacy task/spec files exist, they are archived to `/archive/`. (2) Task and spec templates exist. (3) Clean `/tasks/` and `/specs/` directories ready for new work. (4) Commit and push
- **Criteria covered:** AC-9
- **Status:** [ ] Not started

### Task 3: Create fresh roadmaps for both apps

- **Files:** `tasks/roadmap-v1.1.md` (prompt app), `tasks/roadmap-v1.0.md` (espanso app)
- **Done when:** (1) `automatr-prompt` roadmap defines v1.1 milestones. Suggested items: fix oversized dialogs (template_generate 604 lines, template_improve 436 lines), prompt history/favorites, multi-model comparison, keyboard shortcuts. (2) `automatr-espanso` roadmap defines v1.0 milestones. Suggested items: CI hardening, lint cleanup, first public release, Espanso config validation, template import from prompt app. (3) Each roadmap has Backlog / Active / Completed sections. (4) Commit and push to respective repos
- **Criteria covered:** AC-9
- **Status:** [ ] Not started

## Test Strategy

| Criterion | Verified by |
|-----------|-------------|
| AC-9 | Task 1–3: archive folders populated, roadmap files exist, no stale task files in active directories |

## Rollback Strategy

File moves and new files only. Revert commits if structure needs adjustment.

## Session Log

<!-- Append after each session: date, completed, blockers -->
