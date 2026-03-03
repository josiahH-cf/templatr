# Tasks: Version History Browser

**Spec:** /specs/version-history-browser.md

## Status

- Total: 3
- Complete: 3
- Remaining: 0

## Task List

### Task 1: Version history dialog (`templatr/ui/version_history.py`)

- **Files:** `templatr/ui/version_history.py`
- **Done when:** Dialog exists with version list, content preview pane, and restore button; handles empty history gracefully
- **Criteria covered:** AC 1, 2, 3, 4, 5, 6
- **Status:** [x] Complete

### Task 2: Wire dialog into `_template_actions.py`

- **Files:** `templatr/ui/_template_actions.py`
- **Done when:** `_show_version_history()` opens the new dialog instead of QInputDialog; restore callback refreshes template editor
- **Criteria covered:** AC 7
- **Status:** [x] Complete

### Task 3: Tests

- **Files:** `tests/test_version_history.py`
- **Done when:** Tests cover dialog creation, version list population, content preview on selection, restore action
- **Criteria covered:** AC 8
- **Status:** [x] Complete
