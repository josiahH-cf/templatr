# Feature: Version History Browser

**Status:** Not started
**Project:** templatr

## Description

Template versioning backend exists (`create_version`, `list_versions`, `get_version`, `restore_version`) but the UI is a bare `QInputDialog.getItem` dropdown that shows version labels with no way to preview content, compare versions, or see what changed. This spec adds a dedicated `VersionHistoryDialog` that shows a version list, content preview pane, and restore action — following the same pattern as `HistoryBrowserDialog`.

### Current State

- Backend: `TemplateManager` has full version CRUD — `create_version`, `list_versions`, `get_version`, `restore_version`, `delete_version_history`, `_prune_versions`
- `TemplateVersion` dataclass: `version`, `timestamp`, `note`, `template_data` (full template dict)
- UI: `_show_version_history()` in `_template_actions.py` uses `QInputDialog.getItem` — flat list, no preview, no diff
- Context menu: Template tree right-click has "Version History" triggering `_show_version_history`

### Target Behavior

- **Version list**: Left panel showing all versions with number, timestamp, and note
- **Content preview**: Right panel showing the full template content of the selected version
- **Restore button**: Restores selected version (with backup), refreshes template editor
- **Non-modal dialog**: Replaces the `QInputDialog` flow entirely

## Acceptance Criteria

- [ ] `VersionHistoryDialog` exists in `templatr/ui/version_history.py`
- [ ] Dialog shows a version list (version number, timestamp, note) in a QListWidget
- [ ] Selecting a version shows its template content in a read-only preview pane
- [ ] "Restore" button restores the selected version and creates a backup of current state
- [ ] Dialog closes after successful restore
- [ ] Dialog shows informative message when template has no version history
- [ ] `_show_version_history()` in `_template_actions.py` opens the new dialog instead of QInputDialog
- [ ] Tests cover: dialog creation, version list population, content preview on selection, restore action

## Affected Areas

| Area | Files |
|------|-------|
| **Create** | `templatr/ui/version_history.py` — new dialog |
| **Create** | `tests/test_version_history.py` — tests |
| **Modify** | `templatr/ui/_template_actions.py` — replace QInputDialog with new dialog |

## Constraints

- No new dependencies
- Dialog layout follows the same split-pane pattern as HistoryBrowserDialog
- Diff under 300 lines of new Python code
- Backend API is unchanged — dialog is a pure UI addition
