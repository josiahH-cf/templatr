# Tasks: Phase 1 — Current State Cleanup

**Spec:** /specs/final-split-and-retirement.md

## Status

- Total: 5
- Complete: 0
- Remaining: 5

## Prerequisites

- All prior split phases complete (see `/archive/`)

## Task List

### Task 1: Remove stale Espanso/AHK references from source code

- **Files:** `automatr/ui/main_window.py`, `automatr/core/templates.py`
- **Done when:** (1) About dialog in `main_window.py` no longer lists "Espanso text expansion" as a feature. (2) About dialog URL updated from `yourname/automatr` to `josiahH-cf/automatr-prompt`. (3) `templates.py` line 85 comment changed from "Espanso trigger" to "External trigger alias". (4) `templates.py` `create_template()` docstring updated: "trigger" parameter described generically, not as "Espanso trigger". (5) `grep -rn "espanso\|Espanso" automatr/` returns zero results in `.py` files (excluding `__pycache__`)
- **Criteria covered:** AC-1
- **Status:** [ ] Not started

### Task 2: Clean up README.md

- **Files:** `README.md`
- **Done when:** (1) AutoHotkey/WSL2 hotkey section (around lines 69–73) is removed. (2) Espanso FAQ entry (around line 119) is replaced with a note pointing to `josiahH-cf/automatr-espanso`. (3) No remaining references to Espanso, AutoHotkey, or `--sync` as features of this app. (4) Clone URL and project description reference `automatr-prompt`
- **Criteria covered:** AC-1
- **Status:** [ ] Not started

### Task 3: Fix Config.from_dict() crash on unknown nested keys

- **Files:** `automatr/core/config.py`, `tests/test_config.py`
- **Done when:** (1) `Config.from_dict({"llm": {"unknown_key": "value"}})` does not raise `TypeError` — unknown keys are silently ignored (or logged as a warning). (2) Same behavior for `ui` section. (3) At least 2 regression tests added to `test_config.py` verifying both `llm` and `ui` nested unknown keys. (4) All existing config tests still pass
- **Criteria covered:** AC-2
- **Status:** [ ] Not started

### Task 4: Fix all ruff lint errors

- **Files:** All `.py` files in `automatr/` and `tests/`
- **Done when:** (1) `ruff check .` returns 0 errors and exit code 0. (2) `ruff check . --fix` applied for auto-fixable issues. (3) Remaining errors resolved manually. (4) No behavioral changes introduced — lint fixes only. (5) All existing tests still pass
- **Criteria covered:** AC-3
- **Status:** [ ] Not started

### Task 5: Verify clean state

- **Files:** None (verification only)
- **Done when:** (1) `ruff check .` passes with 0 errors. (2) `pytest` passes all tests (58+ existing + new regression tests from Task 3). (3) App launches without errors. (4) `grep -rn "espanso\|Espanso" automatr/*.py automatr/**/*.py` returns zero results. (5) Commit all changes
- **Criteria covered:** AC-1, AC-2, AC-3
- **Status:** [ ] Not started

## Test Strategy

| Criterion | Verified by |
|-----------|-------------|
| AC-1 | Task 1, Task 2: grep verification; manual check of About dialog |
| AC-2 | Task 3: 2 regression tests in `test_config.py` |
| AC-3 | Task 4, Task 5: `ruff check .` exit code 0 |

## Rollback Strategy

Each task is a single commit. Revert individual commits if needed. Tasks 1–3 are independent; Task 4 is a bulk lint fix that can be reverted atomically.

## Session Log

<!-- Append after each session: date, completed, blockers -->
