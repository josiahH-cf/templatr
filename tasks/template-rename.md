# Task: Template Rename

Spec: `/specs/template-rename.md`

## Status: In Progress

## Tasks

1. **[ ]** Write failing tests (`tests/test_template_rename.py`)
2. **[ ]** Add `TemplateManager.rename()` backend (`templatr/core/templates.py`)
3. **[ ]** Add `rename_requested` signal + "Rename..." context menu item (`templatr/ui/template_tree.py`)
4. **[ ]** Add `_rename_template()` handler (`templatr/ui/_template_actions.py`)
5. **[ ]** Wire signal in `MainWindow._wire_tree_signals()` (`templatr/ui/main_window.py`)
