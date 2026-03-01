# Feature: keyboard-shortcuts

## Description

Add a set of configurable keyboard shortcuts to Templatr covering the most
common single-session actions: submitting a generation, copying the last
output, toggling the template sidebar/tree focus, clearing the chat thread,
and navigating between templates in the tree. Shortcut bindings are stored in
`config.json` under `ui.shortcuts` so power users can remap them without
touching source code.

## Acceptance Criteria

- [ ] AC-1: Pressing the generate shortcut (default Ctrl+Return) while the
  text input contains a plain-text message submits that message exactly as if
  the Send button were clicked; no duplicate message is emitted.
- [ ] AC-2: Pressing the generate shortcut has no effect when the slash-command
  palette is visible or when the inline variable form is active.
- [ ] AC-3: Pressing the copy-output shortcut (default Ctrl+Shift+C) copies the
  last AI-generated text to the system clipboard; if there is no previous
  output the shortcut does nothing.
- [ ] AC-4: Pressing the next-template shortcut (default Ctrl+]) selects the
  next template in tree order; pressing the previous-template shortcut
  (default Ctrl+[) selects the previous template; both wrap around.
- [ ] AC-5: Pressing the clear-chat shortcut (default Ctrl+L) clears the chat
  thread; the shortcut is ignored while a generation is in progress.
- [ ] AC-6: Default shortcut bindings are persisted in and loaded from
  `config.json` under `ui.shortcuts`; overriding a key in the JSON file
  changes the active binding on next launch without code changes.
- [ ] AC-7: All five shortcut actions are listed in the `/help` command output
  displayed in the chat thread.

## Affected Areas

**Source files to modify:**
- `templatr/core/config.py` — Add `shortcuts: dict` field to `UIConfig`
  with default bindings; update `from_dict` to populate it.
- `templatr/ui/main_window.py` — Extend `_setup_shortcuts()` to register
  the five new `QShortcut` instances reading keys from config; add
  `_copy_last_output()`, `_select_next_template()`,
  `_select_prev_template()`, `_clear_chat()` helper methods; update
  `_on_system_command("help")` text.
- `templatr/ui/slash_input.py` — Expose a `is_palette_visible()` method
  so `MainWindow` can guard shortcuts correctly.

**Test files to create:**
- `tests/test_keyboard_shortcuts.py` — pytest-qt widget-level tests
  covering AC-1 through AC-7.

## Constraints

- No new package dependencies. PyQt6's `QShortcut` and `QKeySequence` are
  already imported in `main_window.py`.
- Shortcut bindings must be readable from `config.json` at startup; the
  field must use a dict so arbitrary remapping is possible.
- The generate shortcut (Ctrl+Return) must not interfere with the existing
  Enter-to-send logic in `slash_input.py`'s `_key_event_filter`. The
  shortcut must be guarded to fire only when the palette is not visible and
  the inline form is not active. Use `QShortcut` context
  `Qt.ShortcutContext.WindowShortcut` combined with a Python-level guard in
  the slot, not `QShortcut.setEnabled()` polling, to avoid race conditions.
- The existing Ctrl+B sidebar toggle shortcut must not be duplicated or
  replaced — it is already registered in `_setup_shortcuts()`.
- Diff must stay under 300 lines total across all modified files.

## Out of Scope

- A graphical shortcut-remapping dialog (future work).
- Per-template shortcut bindings.
- Global system-level hotkeys (OS hooks outside the app window).
- Shortcut hints shown in tooltips or menus (nice-to-have, separate task).
- Ctrl+N for new template (already claimed by the File > New Template menu
  action via `QKeySequence.StandardKey.New`).

## Dependencies

- `chat-ui-core` (complete) — `ChatWidget.clear_history()` is required for
  the clear-chat shortcut (AC-5).
- `slash-commands` (complete) — the `/help` system command infrastructure
  is required for AC-7.
- No dependency on `platform-config-consolidation` (complete); shortcuts
  config goes into the existing `UIConfig` dataclass which already
  round-trips correctly on all platforms.

## Notes

- PyQt6 distinguishes `QShortcut` (standalone key binding) from `QAction`
  shortcut (tied to a menu item). For shortcuts with no corresponding menu
  action, `QShortcut` is correct. For shortcuts that mirror an existing
  `QAction` (e.g., Ctrl+N), adding a second `QShortcut` would cause an
  ambiguity conflict — rely on the action's built-in shortcut instead.
- `UIConfig.from_dict` already silently ignores unknown keys, so adding a
  `shortcuts` field is backward-compatible: existing config files without
  this key will receive the default dict automatically.
- `_last_output` is stored on `MainWindow` by `GenerationMixin`
  (`_generation.py`). The copy-output helper reads this attribute directly.
- Template navigation order must follow `template_manager.list_all()`
  sorted by `(folder, name)` to match the visual tree order. The
  `TemplateTreeWidget.select_template_by_name()` method handles the
  tree-side selection after navigation.
