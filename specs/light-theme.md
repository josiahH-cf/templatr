# Feature: Light Theme

**Status:** Not started
**Project:** templatr

## Description

templatr ships with a polished dark theme but the `LIGHT_THEME` constant in `templatr/ui/theme.py` is a stub with a TODO comment. This spec completes the light theme stylesheet, adds a View → Theme toggle to the menu bar, persists the user's preference, and applies it at startup — matching every selector already covered by `DARK_THEME`.

### Current State

- `DARK_THEME` in `theme.py`: ~300 lines of fully styled CSS covering all widgets, chat bubbles, scrollbars, menus, tabs, status bar, etc.
- `LIGHT_THEME` in `theme.py`: 4-line stub with only `QMainWindow/QWidget` background + a TODO comment.
- `get_theme_stylesheet()` already dispatches on `"light"` vs `"dark"`.
- `UIConfig.theme` in `config.py` stores the preference (defaults to `"dark"`).
- `MainWindow._apply_scaling()` reads `config.ui.theme` and calls `get_theme_stylesheet()`.
- `run_gui()` applies the theme stylesheet to `QApplication` at startup.
- No UI exists to switch themes — the user would have to edit config JSON manually.

### Target Behavior

- **View → Theme** submenu with "Dark" and "Light" radio options; current selection is checked.
- Selecting a different theme applies it immediately (no restart required) and persists to config.
- Light theme stylesheet covers every CSS selector present in `DARK_THEME` — no visual regressions.
- Light theme follows a VS Code–inspired light palette: white backgrounds, dark text, blue accents matching the dark theme's accent color.

## Acceptance Criteria

- [ ] `LIGHT_THEME` covers every CSS selector present in `DARK_THEME`
- [ ] Light theme uses readable contrast: dark text on light backgrounds, distinct hover/selected states
- [ ] Chat bubbles (user, AI, system, error) are visually distinct in light theme
- [ ] View menu contains a "Theme" submenu with "Dark" and "Light" options
- [ ] Active theme is indicated with a checkmark in the menu
- [ ] Switching themes applies immediately without restarting the app
- [ ] Theme preference is persisted to config and restored on next launch
- [ ] `get_theme_stylesheet("light")` returns the complete light theme CSS
- [ ] `get_theme_stylesheet("dark")` behavior is unchanged
- [ ] Tests cover: light theme CSS completeness, `get_theme_stylesheet` both variants, theme toggle persistence

## Affected Areas

| Area | Files |
|------|-------|
| **Modify** | `templatr/ui/theme.py` — complete `LIGHT_THEME` CSS |
| **Modify** | `templatr/ui/main_window.py` — add View → Theme submenu, theme switch method |
| **Create** | `tests/test_light_theme.py` — theme tests |

## Constraints

- No new dependencies
- Light theme colors should be cohesive and VS Code–inspired (not random)
- The `DARK_THEME` CSS must not be touched — light theme is additive
- Theme switch must be immediate — no restart dialog
- Diff under 300 lines for new/modified Python code (CSS is declarative and excluded from this limit)

## Out of Scope

- System/auto theme detection (follow OS preference)
- Per-widget theme customization
- Theme editor UI
- Custom accent color picker

## Notes

### Color palette (light theme)

| Role | Color | Usage |
|------|-------|-------|
| Background | `#ffffff` | Main window, widgets |
| Surface | `#f3f3f3` | Sidebars, menus, list backgrounds |
| Border | `#d4d4d4` | Widget borders, separators |
| Text | `#1e1e1e` | Primary text |
| Muted text | `#6e6e6e` | Secondary labels, placeholders |
| Accent | `#0078d4` | Focus borders, selected items, primary buttons |
| Accent hover | `#106ebe` | Button hover, accent hover states |
| Selection bg | `#cce5ff` | List item selection, text selection |
| User bubble | `#d6e8f7` | User chat messages |
| AI bubble | `#f0f0f0` | AI chat messages |
| System bubble | `#e8f5e9` | System messages |
| Error bubble | `#fde8e8` | Error messages |
| Error accent | `#c42b1c` | Error borders, danger buttons |
| Status bar | `#007acc` | Status bar (same as dark) |
