# Archive

This directory contains completed task files, specs, and decision records from the original Automatr split project.

## Contents

### `/archive/specs/`
- **app-split-refactor.md** — Original spec for splitting Automatr into two independent apps. All 7 acceptance criteria met.

### `/archive/tasks/`
- **phase-1-create-prompt-repo.md** — Remove Espanso code, clean launch (7/7 tasks done)
- **phase-2-baseline-tests.md** — 58 baseline tests for core + LLM (6/6 tasks done)
- **phase-3-decompose-mainwindow.md** — Extract 5 widgets from MainWindow (6/6 tasks done)
- **phase-4-template-ownership.md** — All 33 templates → prompt app (3/3 tasks done)
- **phase-5-create-espanso-repo.md** — Separate repo with CLI + GUI + 14 tests (7/7 tasks done)

### `/archive/decisions/`
- **0001-template-ownership-split.md** — Copy of decision record (active copy remains in `/decisions/`)

## Context

These files document the lift-and-reorganize work completed on 2026-02-25 that separated the monolithic Automatr app into `automatr-prompt` and `automatr-espanso`. They are preserved for historical reference and traceability.

The follow-on work (final split, CI setup, legacy retirement) is tracked in `/specs/final-split-and-retirement.md` and `/tasks/phase-{1..7}-*.md`.
