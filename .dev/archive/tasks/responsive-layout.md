# Tasks: responsive-layout

**Spec:** /specs/responsive-layout.md

## Status

- Total: 3
- Complete: 3
- Remaining: 0

## Task List

### Task 1: Proportional splitter and resize event plumbing

- **Files:** `templatr/ui/main_window.py` (add `resizeEvent`, proportional splitter logic), `templatr/core/config.py` (no schema changes — detect factory default at runtime)
- **Done when:** On first launch, splitter sizes are proportional to window width. Resizing the window recalculates unless the user has manually dragged a splitter. Minimum window size (600×400) still works. Saved non-default splitter sizes are preserved.
- **Criteria covered:** Criterion 1 (proportional splitter), Criterion 7 (saved sizes preserved), Criterion 8 (usable at 600×400)
- **Status:** [x] Complete

### Task 2: Dynamic font, header, and padding scaling

- **Files:** `templatr/ui/theme.py` (parameterize padding in CSS), `templatr/ui/main_window.py` (compute scaled font/padding and push to children), `templatr/ui/template_tree.py` (accept scaled values), `templatr/ui/variable_form.py` (accept scaled values), `templatr/ui/output_pane.py` (accept scaled values)
- **Done when:** Body font scales from 13–18pt based on window height. Section headers are ≥1.3× body and never below 14pt. Margins/padding scale with window width (min 8px). All changes are visible on resize.
- **Criteria covered:** Criterion 2 (font scaling), Criterion 3 (header scaling), Criterion 4 (margin scaling)
- **Status:** [x] Complete

### Task 3: Input field stretch and output pane fill

- **Files:** `templatr/ui/variable_form.py` (multi-line field min height), `templatr/ui/output_pane.py` (stretch factor for QTextEdit)
- **Done when:** Output pane's QTextEdit has stretch factor filling all available vertical space. Multi-line variable inputs have min height ≥ 15% of pane height. Single-line inputs scale appropriately. Tests pass.
- **Criteria covered:** Criterion 5 (output stretch), Criterion 6 (variable input height), Criterion 9 (tests pass), Criterion 10 (no new deps)
- **Status:** [x] Complete

## Test Strategy

| Criterion | Tested in Task |
|-----------|---------------|
| 1. Proportional splitter | Task 1 (widget test: resize and check sizes are proportional) |
| 2. Font scaling | Task 2 (widget test: resize and check font sizes) |
| 3. Header scaling | Task 2 (widget test: header label font size ≥ 14pt) |
| 4. Margin scaling | Task 2 (widget test: layout margins grow with size) |
| 5. Output stretch | Task 3 (widget test: QTextEdit stretch factor > 0) |
| 6. Variable input min height | Task 3 (widget test: multi-line field min height) |
| 7. Saved sizes preserved | Task 1 (unit test: non-default sizes unchanged after resize) |
| 8. Usable at 600×400 | Task 1 (widget test: no clipping at minimum size) |
| 9. Tests pass | Task 3 (full pytest run) |
| 10. No new deps | Task 3 (verify pyproject.toml unchanged) |

## Session Log

<!-- Append after each session: date, completed, blockers -->

### 2026-02-27

- **Completed:** All 3 tasks (proportional splitter, dynamic scaling, stretch/fill)
- **Files changed:** `templatr/ui/main_window.py`, `templatr/ui/variable_form.py`, `templatr/ui/output_pane.py`, `templatr/ui/template_tree.py` + `tests/test_responsive_layout.py` (13 new tests)
- **Approach:** Added `resizeEvent` to MainWindow that applies proportional splitter (20/35/45%) when factory-default sizes detected and user hasn't manually dragged. Each child widget exposes `scale_to(w, h)` for font (13–18pt), header (≥1.3× body, min 14pt), margin (min 8px), and input height (≥15% pane height) scaling. Output pane QTextEdit uses `stretch=1`.
- **Surprises:** Qt offscreen renderer handles splitter ratios differently — widget minimum sizes distort exact proportions. Used stylesheet-based header sizing since CSS overrides QFont in Qt. Widened test tolerance to ±12% for splitter ratios to accommodate layout overhead.
- **Result:** 87 tests pass, zero lint errors, zero new dependencies.
