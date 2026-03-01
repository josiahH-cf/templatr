# Tasks: keyboard-shortcuts

**Spec:** /specs/keyboard-shortcuts.md

## Status

- Total: 4
- Complete: 4
- Remaining: 0

## Task List

### Task 1: Add shortcuts config field to UIConfig

- **Files:**
  - `templatr/core/config.py`
- **Done when:** `UIConfig` contains a `shortcuts` dict field with five
  default bindings (`generate`, `copy_output`, `clear_chat`, `next_template`,
  `prev_template`), `from_dict` populates it from config.json (defaulting to
  the built-in dict when the key is absent), and
  `test_keyboard_shortcuts.py::test_shortcuts_defaults_in_config` passes.
- **Criteria covered:** AC-6
- **Status:** [x] Complete

### Task 2: Implement generate, copy-output, and clear-chat shortcuts

- **Files:**
  - `templatr/ui/main_window.py`
  - `templatr/ui/slash_input.py`
  - `tests/test_keyboard_shortcuts.py`
- **Done when:** `_setup_shortcuts()` registers Ctrl+Return (generate),
  Ctrl+Shift+C (copy output), and Ctrl+L (clear chat) read from config;
  the generate shortcut is guarded against palette-visible and form-active
  states; all tests for AC-1, AC-2, AC-3, and AC-5 pass.
- **Criteria covered:** AC-1, AC-2, AC-3, AC-5
- **Status:** [x] Complete

### Task 3: Implement next/previous template navigation shortcuts

- **Files:**
  - `templatr/ui/main_window.py`
  - `tests/test_keyboard_shortcuts.py`
- **Done when:** Ctrl+] selects the next template (with wrap-around) and
  Ctrl+[ selects the previous template (with wrap-around) using the ordered
  list from `template_manager.list_all()`; both navigation tests for AC-4
  pass.
- **Criteria covered:** AC-4
- **Status:** [x] Complete

### Task 4: Update /help output to list shortcut actions

- **Files:**
  - `templatr/ui/main_window.py`
  - `tests/test_keyboard_shortcuts.py`
- **Done when:** The `/help` system command displays all five shortcut
  actions with their default key strings; the test for AC-7 passes by
  asserting the help bubble text contains each key string.
- **Criteria covered:** AC-7
- **Status:** [x] Complete

## Test Strategy

| Acceptance Criterion | Task | Test Name(s) in `test_keyboard_shortcuts.py` |
|---|---|---|
| AC-1 — generate shortcut submits text | Task 2 | `test_generate_shortcut_submits_text` |
| AC-2 — shortcut suppressed during palette/form | Task 2 | `test_generate_shortcut_no_op_when_palette_visible`, `test_generate_shortcut_no_op_when_form_active` |
| AC-3 — copy-output shortcut | Task 2 | `test_copy_output_shortcut_copies_last_output`, `test_copy_output_shortcut_no_op_when_no_output` |
| AC-4 — next/prev template navigation | Task 3 | `test_next_template_shortcut_advances_selection`, `test_prev_template_shortcut_reverses_selection`, `test_template_navigation_wraps_around` |
| AC-5 — clear-chat shortcut | Task 2 | `test_clear_chat_shortcut_clears_thread`, `test_clear_chat_shortcut_no_op_during_generation` |
| AC-6 — shortcuts persist in config | Task 1 | `test_shortcuts_defaults_in_config`, `test_shortcut_override_loaded_from_config` |
| AC-7 — /help lists shortcuts | Task 4 | `test_help_command_lists_shortcuts` |

## Session Log

- 2026-02-28: Task 1 complete. Added _DEFAULT_SHORTCUTS, UIConfig.shortcuts field, merge logic in Config.from_dict. 333 tests pass, 16 failing (Tasks 2–4 pending).
- 2026-02-28: Tasks 2–4 complete. Added keyPressEvent fallback (QShortcut requires active window in offscreen tests). _on_generate_shortcut calls _handle_plain_input directly so monkeypatch intercepts. 349 tests pass, 0 failing.
