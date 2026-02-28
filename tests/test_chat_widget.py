"""Tests for ChatWidget and MessageBubble (chat-ui-core).

Tests the scrolling chat thread and message bubble components:
- MessageBubble: user/AI visual distinction, Markdown rendering, Copy button
- ChatWidget: message management, streaming append, scroll guard

These tests were written before the implementation (TDD).
"""

from PyQt6.QtWidgets import QApplication
from templatr.ui.chat_widget import ChatWidget
from templatr.ui.message_bubble import MessageBubble, MessageRole

# -- MessageBubble tests -----------------------------------------------------


def test_user_bubble_role(qtbot):
    """User bubble stores the correct role."""
    bubble = MessageBubble(MessageRole.USER)
    qtbot.addWidget(bubble)
    assert bubble.role == MessageRole.USER


def test_ai_bubble_role(qtbot):
    """AI bubble stores the correct role."""
    bubble = MessageBubble(MessageRole.AI)
    qtbot.addWidget(bubble)
    assert bubble.role == MessageRole.AI


def test_user_bubble_set_text(qtbot):
    """User bubble stores plain text and returns it via get_raw_text."""
    bubble = MessageBubble(MessageRole.USER)
    qtbot.addWidget(bubble)
    bubble.set_text("Hello world")
    assert bubble.get_raw_text() == "Hello world"


def test_ai_bubble_set_text_stores_raw_markdown(qtbot):
    """AI bubble stores raw Markdown (not HTML) in get_raw_text."""
    bubble = MessageBubble(MessageRole.AI)
    qtbot.addWidget(bubble)
    bubble.set_text("# Header\n\nSome **bold** text.")
    raw = bubble.get_raw_text()
    assert "# Header" in raw
    assert "<h1>" not in raw


def test_markdown_renders_headers(qtbot):
    """AI bubble HTML output contains <h1> for # Header Markdown."""
    bubble = MessageBubble(MessageRole.AI)
    qtbot.addWidget(bubble)
    bubble.set_text("# My Header")
    html = bubble._render_markdown("# My Header")
    assert "<h1>" in html.lower()


def test_markdown_renders_bold(qtbot):
    """AI bubble renders **bold** as <strong> in HTML."""
    bubble = MessageBubble(MessageRole.AI)
    qtbot.addWidget(bubble)
    html = bubble._render_markdown("This is **bold** text.")
    assert "<strong>" in html.lower()


def test_markdown_renders_code_blocks(qtbot):
    """AI bubble renders fenced code blocks as <pre> in HTML."""
    bubble = MessageBubble(MessageRole.AI)
    qtbot.addWidget(bubble)
    md = "```python\nprint('hello')\n```"
    html = bubble._render_markdown(md)
    assert "<pre" in html.lower()


def test_markdown_renders_bullet_list(qtbot):
    """AI bubble renders bullet lists as <ul><li> in HTML."""
    bubble = MessageBubble(MessageRole.AI)
    qtbot.addWidget(bubble)
    md = "- item one\n- item two"
    html = bubble._render_markdown(md)
    assert "<ul>" in html.lower() or "<li>" in html.lower()


def test_ai_bubble_append_token_accumulates(qtbot):
    """append_token accumulates text; get_raw_text returns full accumulated string."""
    bubble = MessageBubble(MessageRole.AI)
    qtbot.addWidget(bubble)
    bubble.append_token("Hello")
    bubble.append_token(", ")
    bubble.append_token("world")
    assert bubble.get_raw_text() == "Hello, world"


def test_copy_button_copies_raw_markdown(qtbot):
    """Copy button puts raw Markdown (not HTML) on the clipboard."""
    bubble = MessageBubble(MessageRole.AI)
    qtbot.addWidget(bubble)
    md = "# Title\n\n**Bold** text."
    bubble.set_text(md)

    clipboard = QApplication.clipboard()
    clipboard.clear()
    bubble._copy_to_clipboard()

    text = clipboard.text()
    assert "# Title" in text
    assert "<h1>" not in text


def test_copy_requested_signal_emitted(qtbot):
    """copy_requested signal emits the raw Markdown text."""
    bubble = MessageBubble(MessageRole.AI)
    qtbot.addWidget(bubble)
    md = "Hello **world**"
    bubble.set_text(md)

    with qtbot.waitSignal(bubble.copy_requested, timeout=1000) as sig:
        bubble._copy_to_clipboard()

    assert sig.args[0] == md


# -- ChatWidget tests --------------------------------------------------------


def test_add_user_message_creates_bubble(qtbot):
    """add_user_message adds a MessageBubble with USER role to the thread."""
    widget = ChatWidget()
    qtbot.addWidget(widget)
    widget.add_user_message("Hello!")

    bubbles = widget.findChildren(MessageBubble)
    assert any(b.role == MessageRole.USER for b in bubbles)


def test_add_ai_bubble_returns_message_bubble(qtbot):
    """add_ai_bubble returns a MessageBubble instance."""
    widget = ChatWidget()
    qtbot.addWidget(widget)
    bubble = widget.add_ai_bubble()
    assert isinstance(bubble, MessageBubble)
    assert bubble.role == MessageRole.AI


def test_add_ai_bubble_visible_in_widget(qtbot):
    """AI bubble returned by add_ai_bubble is present in the chat thread."""
    widget = ChatWidget()
    qtbot.addWidget(widget)
    bubble = widget.add_ai_bubble()
    assert bubble in widget.findChildren(MessageBubble)


def test_append_token_to_last_ai(qtbot):
    """append_token_to_last_ai adds to the most recently added AI bubble."""
    widget = ChatWidget()
    qtbot.addWidget(widget)
    bubble = widget.add_ai_bubble()
    widget.append_token_to_last_ai("Hello")
    widget.append_token_to_last_ai(" there")
    assert bubble.get_raw_text() == "Hello there"


def test_finalize_last_ai_updates_bubble(qtbot):
    """finalize_last_ai sets the full text on the last AI bubble."""
    widget = ChatWidget()
    qtbot.addWidget(widget)
    bubble = widget.add_ai_bubble()
    widget.append_token_to_last_ai("partial")
    widget.finalize_last_ai("# Full Markdown\n\nComplete response.")
    assert "# Full Markdown" in bubble.get_raw_text()


def test_show_error_bubble_adds_bubble(qtbot):
    """show_error_bubble adds a MessageBubble to the thread."""
    widget = ChatWidget()
    qtbot.addWidget(widget)
    count_before = len(widget.findChildren(MessageBubble))
    widget.show_error_bubble("Something went wrong")
    count_after = len(widget.findChildren(MessageBubble))
    assert count_after > count_before


def test_clear_history_removes_bubbles(qtbot):
    """clear_history removes all message bubbles from the thread."""
    widget = ChatWidget()
    qtbot.addWidget(widget)
    widget.add_user_message("Hello")
    widget.add_ai_bubble()
    widget.clear_history()
    assert len(widget.findChildren(MessageBubble)) == 0


def test_scroll_guard_does_not_jump_on_token_append(qtbot):
    """Appending a token does not scroll to bottom if user has scrolled up."""
    widget = ChatWidget()
    qtbot.addWidget(widget)
    widget.show()

    # Add several messages to create scrollable content
    for _ in range(10):
        widget.add_user_message("A" * 200)

    # Scroll to top
    scroll_bar = widget._scroll_area.verticalScrollBar()
    scroll_bar.setValue(0)
    position_before = scroll_bar.value()

    # Add an AI bubble and append a token
    widget.add_ai_bubble()
    widget.append_token_to_last_ai("New token")

    # Scroll position should remain at top (user had scrolled away from bottom)
    assert scroll_bar.value() == position_before


def test_scroll_to_bottom_when_already_at_bottom(qtbot):
    """Appending a token scrolls to bottom if the user was already at bottom."""
    widget = ChatWidget()
    qtbot.addWidget(widget)
    widget.show()

    # Add a few messages
    for _ in range(3):
        widget.add_user_message("Short message")

    # Scroll to bottom explicitly
    scroll_bar = widget._scroll_area.verticalScrollBar()
    scroll_bar.setValue(scroll_bar.maximum())

    widget.add_ai_bubble()
    widget.append_token_to_last_ai("Token appended at bottom")

    # Should still be at bottom (or close to it)
    assert widget._is_at_bottom()
