# Tasks: chat-ui-core

**Spec:** /specs/chat-ui-core.md

## Status

- Total: 5
- Complete: 5
- Remaining: 0

## Task List

### Task 1: Pin mistune dependency and write test stubs

- **Files:** `pyproject.toml`, `tests/test_chat_widget.py` (new), `tests/test_slash_input.py` (new)
- **Done when:** `mistune>=3.0,<4.0` pinned; test stubs exist and pass ruff; import fails with expected ModuleNotFoundError.
- **Status:** [x] Complete

### Task 2: Implement MessageBubble and ChatWidget

- **Files:** `templatr/ui/message_bubble.py` (new), `templatr/ui/chat_widget.py` (new)
- **Done when:** `MessageBubble` renders user (right-aligned plain text) and AI (QTextBrowser Markdown→HTML via mistune) bubbles; Copy button emits raw Markdown; `ChatWidget` scroll-guard prevents jump when user has scrolled up; all 20 tests in `test_chat_widget.py` pass.
- **Criteria covered:** 1 (chat thread), 2 (visual distinction), 3 (Markdown rendering), 4 (streaming without scroll-jump), 7 (copy raw Markdown)
- **Status:** [x] Complete

### Task 3: Implement SlashInputWidget

- **Files:** `templatr/ui/slash_input.py` (new), `tests/test_slash_input.py` (updated for widget.show())
- **Done when:** `_TemplatePalette` filters and navigates with keyboard; `_InlineVariableForm` appears inline when template has variables; `SlashInputWidget` emits `template_submitted` or `plain_submitted`; all 16 tests pass.
- **Criteria covered:** 8 (/ palette), 9 (inline variable form)
- **Status:** [x] Complete

### Task 4: Wire generation flow and layout swap

- **Files:** `templatr/ui/_generation.py`, `templatr/ui/main_window.py`, `templatr/ui/_template_actions.py`, `tests/test_smoke.py`, `tests/test_decoupling.py`, `tests/test_responsive_layout.py`, `tests/test_cross_platform_packaging.py`
- **Done when:** `_generate(prompt: str)` streams to `ChatWidget`; 2-pane layout replaces 3-pane; sidebar defaults hidden with Ctrl+B toggle; `self.variable_form = None`; all 208 tests pass.
- **Criteria covered:** 5 (collapsible sidebar), 6 (session-only history)
- **Status:** [x] Complete

### Task 5: Theme CSS and spec/task doc updates

- **Files:** `templatr/ui/theme.py`, `specs/chat-ui-core.md`, `specs/slash-commands.md`, `tasks/chat-ui-core.md`, `tasks/roadmap-v1.1.md`
- **Done when:** Chat bubble CSS added to dark theme; spec/task docs updated; all acceptance criteria marked; ruff + pytest clean.
- **Criteria covered:** All (styling and documentation)
- **Status:** [x] Complete

## Test Strategy

| Criterion | Tested in Task |
|-----------|---------------|
| 1. Chat thread displays | Task 2 |
| 2. Visual distinction | Task 2 |
| 3. Markdown rendering | Task 2 |
| 4. Streaming without scroll-jump | Task 2 |
| 5. Collapsible sidebar | Task 4 |
| 6. Session-only history | Task 4 (no persistence file created) |
| 7. Copy raw Markdown | Task 2 |
| 8. / palette | Task 3 |
| 9. Inline variable form | Task 3 |

## Session Log

- 2026-02-28: Implemented all 5 tasks. 208 tests passing, zero lint errors.
  Layout replaced: 3-pane (tree/form/output) → 2-pane (sidebar toggle + chat+input).
  Slash-commands core pulled forward into slash_input.py.
  mistune 3.2.0 added for Markdown→HTML rendering in QTextBrowser.
