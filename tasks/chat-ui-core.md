# Tasks: chat-ui-core

**Spec:** /specs/chat-ui-core.md

## Status

- Total: 3
- Complete: 0
- Remaining: 3

## Task List

### Task 1: Chat widget and message bubble components

- **Files:** `templatr/ui/chat_widget.py` (new), `templatr/ui/message_bubble.py` (new), `tests/test_chat_widget.py` (new)
- **Done when:** `ChatWidget` displays a scrolling list of message bubbles. `MessageBubble` renders user messages (visually distinct style) and AI messages (separate style with sender label and "Copy" button). Bubbles accept raw text for user messages and HTML for AI messages. Widget is testable with pytest-qt.
- **Criteria covered:** Criterion 1 (chat thread), Criterion 2 (visual distinction), Criterion 7 (copy button on AI messages)
- **Status:** [ ] Not started

### Task 2: Markdown rendering and streaming integration

- **Files:** `templatr/ui/chat_widget.py` (Markdown→HTML pipeline), `templatr/ui/_generation.py` (redirect output to chat widget), `pyproject.toml` (add `mistune` dependency)
- **Done when:** AI responses convert Markdown to styled HTML via `mistune` and render in QTextBrowser. Streaming tokens append to the current AI bubble in real-time. Scrolling stays at bottom only when user was already at bottom (no scroll-jump when reading above). Copy button extracts raw Markdown source, not rendered HTML.
- **Criteria covered:** Criterion 3 (Markdown rendering), Criterion 4 (streaming without scroll-jump), Criterion 7 (copy raw Markdown)
- **Status:** [ ] Not started

### Task 3: Layout swap, collapsible sidebar, and theme

- **Files:** `templatr/ui/main_window.py` (replace 3-pane with chat layout), `templatr/ui/theme.py` (chat-specific styles: bubble colors, code block backgrounds), `templatr/ui/template_tree.py` (make collapsible)
- **Done when:** Main window shows chat widget as the central area. Template tree sidebar is collapsible, defaults to hidden, toggles via button or `Ctrl+B`. Theme includes chat bubble styles for dark and light modes. The old 3-pane widgets (`output_pane.py`, `variable_form.py`) remain in the codebase but are no longer instantiated by default.
- **Criteria covered:** Criterion 5 (collapsible sidebar), Criterion 6 (session-only history, cleared on restart)
- **Status:** [ ] Not started

## Test Strategy

| Criterion | Tested in Task |
|-----------|---------------|
| 1. Chat thread displays | Task 1 (test: add messages, verify widget count and layout) |
| 2. Visual distinction | Task 1 (test: verify user vs AI bubble have different style properties) |
| 3. Markdown rendering | Task 2 (test: send Markdown text, verify HTML output contains `<h1>`, `<code>`, `<strong>`) |
| 4. Streaming without scroll-jump | Task 2 (test: scroll up, append tokens, verify scroll position unchanged) |
| 5. Collapsible sidebar | Task 3 (test: toggle sidebar, verify visibility state and Ctrl+B shortcut) |
| 6. Session-only history | Task 3 (test: add messages, no persistence file created, widget starts empty) |
| 7. Copy raw Markdown | Task 1 + Task 2 (test: click copy, verify clipboard contains Markdown not HTML) |

## Session Log

<!-- Append after each session: date, completed, blockers -->
