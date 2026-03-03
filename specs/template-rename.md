# Spec: Template Rename

## Problem
There is no way to rename a template directly from the template tree. Users must open the full Advanced Edit dialog and manually change the name field, which is non-obvious and heavyweight for a simple name change.

## Goal
Add a "Rename..." context menu action that lets users rename a template in-place with a lightweight dialog.

## Acceptance Criteria

### AC1 — Backend: `TemplateManager.rename(template, new_name)`
- Returns the updated `Template` on success, with `name` and `_path` updated.
- Raises `ValueError("Name cannot be empty")` when `new_name` is blank/whitespace.
- Raises `ValueError("A template named '...' already exists")` when `new_name` conflicts with an existing template (case-insensitive).
- Writes template JSON to the new file path derived from `new_name`.
- Deletes the old JSON file.
- Renames the version history directory (slug → new slug) if it exists.

### AC2 — UI signal
- `TemplateTreeWidget` exposes a `rename_requested = pyqtSignal(object)` signal.

### AC3 — Context menu
- Template context menu includes a "Rename..." action that emits `rename_requested`.

### AC4 — Handler
- `TemplateActionsMixin._rename_template(template)` prompts for a new name, calls `manager.rename()`, refreshes the tree, selects the renamed template, and shows a status bar confirmation.
- On `ValueError` from the backend, the handler shows a `QMessageBox.warning` and does not close the prompt (or surfaces the error clearly).

### AC5 — Signal wiring
- `MainWindow._wire_tree_signals()` connects `tree.rename_requested` → `self._rename_template`.

## Out of Scope
- Folder rename (separate feature)
- Batch rename
