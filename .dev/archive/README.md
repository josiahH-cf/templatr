# Archive

This directory contains completed task files, specs, and decision records from Templatr's development history.

## Contents

### `/archive/specs/`
- **app-split-refactor.md** — Original spec for splitting Automatr into two independent apps. All 7 acceptance criteria met.
- **final-split-and-retirement.md** — Final split spec: repo creation, CI setup, governance, legacy retirement. All 9 ACs met.

### `/archive/tasks/`

**Original Split (completed 2026-02-25):**
- **phase-1-create-prompt-repo.md** — Remove Espanso code, clean launch (7/7 tasks done)
- **phase-2-baseline-tests.md** — 58 baseline tests for core + LLM (6/6 tasks done)
- **phase-3-decompose-mainwindow.md** — Extract 5 widgets from MainWindow (6/6 tasks done)
- **phase-4-template-ownership.md** — All 33 templates → prompt app (3/3 tasks done)
- **phase-5-create-espanso-repo.md** — Separate repo with CLI + GUI + 14 tests (7/7 tasks done)

**Final Split & Retirement (completed 2026-02-26):**
- **phase-1-current-state-cleanup.md** — Remove stale references, fix bugs, lint cleanup (5/5 tasks done)
- **phase-2-create-github-repos.md** — Create GitHub repos, update URLs, push code (4/4 tasks done)
- **phase-3-ci-cd-setup.md** — CI workflows for both repos (3/3 tasks done)
- **phase-4-retire-legacy-repo.md** — Tag, update README, archive legacy repo (3/3 tasks done)
- **phase-5-governance.md** — AGENTS.md updates and GOVERNANCE.md for both apps (3/3 tasks done)
- **phase-6-validation.md** — Independence verification: fresh clone, tests, cross-ref audit (3/3 tasks done)
- **phase-7-task-system-reset.md** — Archive completed tasks, create roadmaps (3/3 tasks done)

### `/archive/decisions/`
- **0001-template-ownership-split.md** — Copy of decision record (active copy remains in `/decisions/`)

## Context

These files document the full development lifecycle that separated the monolithic Automatr app into two independent applications:
- [templatr](https://github.com/josiahH-cf/templatr) — Local prompt optimizer (formerly automatr-prompt)
- [templatr-espanso](https://github.com/josiahH-cf/templatr-espanso) — Espanso automation GUI (formerly automatr-espanso)

They are preserved for historical reference and traceability.
