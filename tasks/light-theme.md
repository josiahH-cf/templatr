# Tasks: Light Theme

**Spec:** /specs/light-theme.md

## Status

- Total: 3
- Complete: 3
- Remaining: 0

## Task List

### Task 1: Complete `LIGHT_THEME` CSS in `theme.py`

- **Files:** `templatr/ui/theme.py`
- **Done when:** `LIGHT_THEME` covers every CSS selector in `DARK_THEME` with a cohesive light palette; `get_theme_stylesheet("light")` returns complete CSS
- **Criteria covered:** AC 1, 2, 3, 8, 9
- **Status:** [x] Complete

### Task 2: Add View → Theme menu toggle

- **Files:** `templatr/ui/main_window.py`
- **Done when:** View menu exists with Theme submenu containing Dark/Light radio options; selecting applies immediately; preference saved to config; restored at startup
- **Criteria covered:** AC 4, 5, 6, 7
- **Status:** [x] Complete

### Task 3: Tests

- **Files:** `tests/test_light_theme.py`
- **Done when:** Tests cover CSS completeness (all selectors), `get_theme_stylesheet` both variants, theme toggle persistence, View → Theme menu existence
- **Criteria covered:** AC 10
- **Status:** [x] Complete
