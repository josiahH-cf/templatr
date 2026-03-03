# Task: Template Duplicate / Clone

## Status: Complete

## Goal
Allow users to clone any template directly from the context menu, getting a ready-to-edit copy without having to create a new template from scratch.

## Acceptance Criteria
- [ ] `TemplateManager.duplicate(template, new_name=None)` creates a copy with a unique name
- [ ] Default name is `"Copy of <name>"`, with `(2)`, `(3)` … suffix on collision
- [ ] Optional `new_name` parameter overrides the default
- [ ] Copy is saved to disk in the same folder as the original
- [ ] Original template is unchanged after duplication
- [ ] "Duplicate" appears in the template context menu
- [ ] Selecting "Duplicate" emits `duplicate_requested` signal and triggers the handler
- [ ] After duplication the tree refreshes and the new copy is selected
- [ ] Status bar shows confirmation message

## Tasks
1. **[done]** Write failing tests (`tests/test_template_duplicate.py`)
2. **[done]** Add `TemplateManager.duplicate()` (`templatr/core/templates.py`)
3. **[done]** Add `duplicate_requested` signal + context menu item (`templatr/ui/template_tree.py`)
4. **[done]** Add `_duplicate_template()` handler (`templatr/ui/_template_actions.py`)
5. **[done]** Wire signal in `MainWindow._wire_tree_signals()` (`templatr/ui/main_window.py`)

## Tests
All 10 tests in `tests/test_template_duplicate.py` pass (545/545 total).
