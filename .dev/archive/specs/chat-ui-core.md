# Feature: Chat UI Core

## Description

Replace the 3-pane splitter layout with a single-pane conversational chat interface where user prompts and AI responses appear in a scrolling thread, with Markdown rendering for rich output. Uses `QTextBrowser` with HTML/CSS — not QWebEngineView — to avoid pulling in Chromium (~200 MB dependency that would double the installer size).

**Important:** Before building this, share the current packaged app with 2–3 real users. If they prefer the current 3-panel layout, make the chat view an alternative mode (toggled in View menu) rather than a full replacement.

## Acceptance Criteria

- [ ] The main window displays a single chat thread (scrolling message list) with a text input area docked at the bottom
- [ ] User messages appear visually distinct from AI responses (different background color, alignment, or sender label)
- [ ] AI responses render Markdown (headers, bold, italic, code blocks with syntax styling, numbered/bulleted lists) as styled HTML in a `QTextBrowser`
- [ ] Streaming tokens append to the current AI message bubble in real-time without scroll-jumping when the user has scrolled up to read earlier messages
- [ ] The template sidebar is collapsible and defaults to hidden; toggled via a hamburger/panel button or `Ctrl+B` keyboard shortcut
- [ ] Chat history persists for the current session and is cleared on app restart (no cross-session persistence)
- [ ] A "Copy" button on each AI response copies the raw Markdown source, not the rendered HTML
- [ ] Typing `/` in the chat input opens a filterable template palette (slash-commands pulled forward)
- [ ] Selecting a template with variables shows a compact inline variable form above the text input (no popup)

## Affected Areas

- New: `templatr/ui/chat_widget.py`, `templatr/ui/message_bubble.py`
- Modified: `templatr/ui/main_window.py` (layout swap), `templatr/ui/_generation.py` (output target), `templatr/ui/theme.py` (chat-specific styles)
- Retained: `templatr/ui/llm_toolbar.py` (unchanged), `templatr/ui/template_tree.py` (becomes collapsible sidebar)
- Preserved: `templatr/ui/output_pane.py`, `templatr/ui/variable_form.py` (not deleted — kept as fallback)

## Constraints

- No QWebEngineView — `QTextBrowser` with HTML4/CSS2 subset only
- Markdown→HTML conversion via a lightweight dependency (`markdown` or `mistune`, ~100 KB) or Python stdlib
- Streaming must not block the UI thread
- Must support both dark and light themes
- `QTextBrowser` HTML subset — test code block rendering carefully, pre-render fenced code as `<pre><code>` blocks

## Out of Scope

- Multi-conversation tabs
- Conversation persistence across app restarts (save/load chat history)
- File attachments or image rendering in chat
- Conversation export (print/PDF/markdown file)
- Voice input

## Dependencies

- Hard dep: `repo-migration` — codebase must be in the new `templatr` repo before adding major new UI
- Benefits from Spec: `graceful-error-recovery` (error messages display inline in chat)

## Notes

- The existing `OutputPaneWidget` and `VariableFormWidget` are superseded but not deleted. They remain importable for a potential "classic mode" toggle.
- `QTextBrowser` supports a subset of HTML4 + CSS2 — this covers headers, lists, bold/italic, code blocks, and basic table rendering. No JavaScript.
- For Markdown conversion: `mistune` (~50 KB, pure Python, fast) is preferred over `markdown` (larger, more extensions).
- Streaming append strategy: get the `QTextCursor` at the end, insert new HTML fragment, then only scroll-to-bottom if the user was already at the bottom (check `verticalScrollBar().value() == verticalScrollBar().maximum()`).
- **User testing gate:** The decision between "replace layout" vs "add alternative mode" should be recorded in `/decisions/` after user feedback.
