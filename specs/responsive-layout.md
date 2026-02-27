# Feature: Responsive Layout & Dynamic Sizing

## Description

The current 3-pane layout (template tree, variable form, output pane) uses hardcoded splitter ratios (200:300:400), small fixed font sizes, tight margins, and no awareness of actual window or screen dimensions. On a typical 1080p+ display the result is cramped text surrounded by dead space — text inputs are narrow, the output pane wastes vertical room, and the template tree barely shows full names.

This feature makes every text element, spacing margin, and pane proportion **scale dynamically** based on the window's actual size, so the UI fills the available space on first launch and adapts fluidly when the window is resized or snapped.

## Problem

1. **Splitter ratios are fixed pixels** — the 200:300:400 default was tuned for 900×700. On a 1920×1080 window the tree is still 200px and the output pane has ~400px of horizontal dead space.
2. **Font sizes are small and static** — the default `font_size: 13` is readable but doesn't grow when the window is large, leaving text swimming in whitespace.
3. **Input fields don't stretch** — `QLineEdit` and `QPlainTextEdit` for variables have no minimum height scaling; single-line inputs are tiny even when the form has unused vertical space.
4. **Section headers are barely larger than body text** — only +1pt from body, making visual hierarchy weak.
5. **Margins/padding don't scale** — hard `5px`/`10px` margins look cramped at larger sizes and wasteful at smaller ones.

## Acceptance Criteria

- [x] On first launch (no saved state), splitter sizes are calculated as proportions of the window width (e.g., 20%/35%/45%) instead of fixed pixel values
- [x] When the window is resized, QLineEdit/QPlainTextEdit minimum heights and font sizes scale proportionally (no text stays tiny in a large window)
- [x] Section headers ("Templates", "Variables", "Output") scale to at least 1.3× body font size, never below 14pt
- [x] Inner margins and padding scale with window size (minimum 8px, grow proportionally)
- [x] The output pane's QTextEdit fills all available vertical space (stretch factor)
- [x] Variable form inputs for multi-line fields have a minimum height that grows with window height (at least 15% of pane height)
- [x] Existing users' saved splitter sizes are preserved — proportional defaults only apply when `splitter_sizes` is the factory default `[200, 300, 400]`
- [x] All 3 panes remain usable at the minimum window size (600×400) — no clipping or overlapping
- [x] `pytest` passes with zero failures after changes
- [x] No new dependencies added

## Affected Areas

- `templatr/ui/main_window.py` — splitter initialization, resize event hook
- `templatr/ui/variable_form.py` — input field sizing, margin scaling
- `templatr/ui/output_pane.py` — stretch factor, margin scaling
- `templatr/ui/template_tree.py` — margin scaling
- `templatr/ui/theme.py` — dynamic font/padding CSS generation
- `templatr/core/config.py` — default splitter as proportions

## Constraints

- Must not break saved window state for existing users
- Must not add new dependencies
- Must remain usable at minimum 600×400 window size
- Must not change the 3-pane layout structure (that's a separate spec: chat-ui-core)

## Out of Scope

- Changing the 3-pane layout to chat UI (separate spec)
- DPI/HiDPI awareness beyond Qt's built-in scaling
- User-configurable layout proportions (settings dialog)
- Light theme (incomplete, separate work)

## Dependencies

- project-rename (completed) — files are at `templatr/` paths
- No other blockers

## Notes

- The key insight from the screenshot: with a typical maximized window on 1920×1080, roughly 40% of every pane is empty padding that could be used by content.
- Approach: hook `resizeEvent` on `MainWindow`, compute scaled values, and push them to child widgets. Children expose a `scale_to(width, height)` method.
- For the splitter, detect if current sizes match the factory default `[200, 300, 400]`; if so, recalculate as proportions on resize. Once the user manually drags a splitter handle, stop auto-resizing the splitter (the user has expressed intent).
- Font scaling formula suggestion: `base_font = max(13, min(18, window_height / 50))`. At 700px height → 14pt, at 900px → 18pt cap. Section headers = `base_font * 1.3`.
- Padding scaling: `pad = max(8, window_width // 120)`. At 900px → 7→8px floor. At 1920px → 16px.
