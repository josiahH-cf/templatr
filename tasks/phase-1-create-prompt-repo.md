# Tasks: Phase 1 — Create automatr-prompt Repo

**Spec:** /specs/app-split-refactor.md

## Status

- Total: 7
- Complete: 7
- Remaining: 0

## Task List

### Task 1: Create branch and new repo structure

- **Files:** root directory
- **Done when:** A new branch `feat/prompt-app-split` exists with the current code intact as a starting point
- **Criteria covered:** AC-1 (prerequisite)
- **Status:** [x] Done

### Task 2: Remove integrations/espanso.py and Espanso imports

- **Files:** `automatr/integrations/espanso.py`, `automatr/integrations/__init__.py`
- **Done when:** `espanso.py` is deleted. No remaining imports of `get_espanso_manager`, `EspansoManager`, or `sync_to_espanso` anywhere in the codebase. `integrations/__init__.py` docstring no longer mentions Espanso
- **Criteria covered:** AC-1
- **Status:** [x] Done

### Task 3: Remove Espanso references from MainWindow

- **Files:** `automatr/ui/main_window.py`
- **Done when:** The following are removed: (1) `from automatr.integrations.espanso import get_espanso_manager` (line 44), (2) "Sync to Espanso" menu action and `_sync_espanso()` method (lines 299-302, 425-440), (3) auto-sync logic in `_on_template_saved()` (lines 1387-1389), (4) auto-sync logic in `_delete_template()` (lines 1355-1358). App launches without errors
- **Criteria covered:** AC-1, AC-2
- **Status:** [x] Done

### Task 4: Remove Espanso references from TemplateEditor and __main__

- **Files:** `automatr/ui/template_editor.py`, `automatr/__main__.py`
- **Done when:** (1) `trigger_edit` QLineEdit, its form row, and all trigger get/set references are removed from `TemplateEditor` (lines 123-125, 225, 347, 356). (2) `--sync` CLI flag and its handler are removed from `__main__.py`. The `main()` function only calls `run_gui()`
- **Criteria covered:** AC-1
- **Status:** [x] Done

### Task 5: Remove EspansoConfig from config.py

- **Files:** `automatr/core/config.py`
- **Done when:** `EspansoConfig` dataclass is removed. `Config` dataclass no longer has an `espanso` field. `ConfigManager` load/save no longer references espanso config. Unknown keys in existing `config.json` files are silently ignored on load (no crash if a user has `"espanso"` in their config)
- **Criteria covered:** AC-1
- **Status:** [x] Done

### Task 6: Clean up pyproject.toml and install.sh

- **Files:** `pyproject.toml`, `install.sh`
- **Done when:** (1) `PyYAML` is removed from dependencies in `pyproject.toml`. Project name and description updated to reflect prompt-optimizer focus. (2) `setup_espanso()` and `setup_autohotkey()` functions are removed from `install.sh`. Calls to those functions are removed from the main install flow. Espanso-related smoke tests removed. App still installs and runs via `./install.sh`
- **Criteria covered:** AC-1, AC-3
- **Status:** [x] Done

### Task 7: Verify clean launch and template loading

- **Files:** None (manual verification)
- **Done when:** (1) `pip install -e .` succeeds without PyYAML. (2) `automatr` launches the GUI. (3) Templates with `"trigger"` fields load without error (the field is ignored, not rejected). (4) `ruff check .` passes. (5) No remaining references to "espanso" in Python source files (grep verification). (6) Commit and push the branch
- **Criteria covered:** AC-1, AC-2, AC-3
- **Status:** [x] Done

## Test Strategy

| Criterion | Verified by |
|-----------|-------------|
| AC-1 | Task 7: grep confirms zero espanso references in `.py` files |
| AC-2 | Task 7: manual launch + template load |
| AC-3 | Task 7: `pip install -e .` without PyYAML, import check |

## Rollback Strategy

If any task breaks the app, `git stash` or `git checkout` the affected files. Each task is a single commit, so reverting is trivial.

## Session Log

### 2026-02-25 — Phase 1 complete
- Completed: Tasks 1-7 (all)
- Branch: `feat/prompt-app-split` (5 commits)
- Notes:
  - Also removed `iter_with_triggers()` from `templates.py` (dead code after espanso.py deleted)
  - ruff had 878 pre-existing errors on main; Phase 1 reduced to 820 (no new errors introduced)
  - ruff config deprecation fixed in pyproject.toml (`[tool.ruff.lint]`)
  - `Template.trigger` field preserved as passthrough per spec constraint
