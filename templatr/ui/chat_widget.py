"""Chat widget for the chat-ui-core feature.

Provides ChatWidget, a scrolling list of MessageBubble widgets representing
the conversation thread. Handles streaming token append with scroll-guard
so that reading earlier messages is not interrupted by new tokens.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QLabel,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from templatr.ui.message_bubble import MessageBubble, MessageRole


class ChatWidget(QWidget):
    """Scrolling chat thread that displays MessageBubble widgets.

    Layout: a QScrollArea containing a QVBoxLayout of MessageBubbles,
    with a vertical spacer at the top to push content toward the bottom
    until the thread is taller than the viewport.

    The SlashInputWidget is assembled separately by MainWindow and docked
    below this widget in the window layout.

    Attributes:
        _scroll_area: The QScrollArea containing the message list.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the chat widget with an empty thread."""
        super().__init__(parent)
        self._active_ai_bubble: MessageBubble | None = None
        self._setup_ui()

    # -- Public API ----------------------------------------------------------

    def add_user_message(self, text: str) -> None:
        """Append a user bubble with the given text and scroll to bottom.

        Args:
            text: The user's message text.
        """
        bubble = MessageBubble(MessageRole.USER)
        bubble.set_text(text)
        self._add_bubble(bubble)
        self._scroll_to_bottom()

    def add_ai_bubble(self) -> MessageBubble:
        """Append an empty AI bubble and return it for streaming population.

        The caller (GenerationMixin) retains the bubble reference and calls
        bubble.append_token() on each token_received signal. Scroll management
        during streaming is handled by append_token_to_last_ai().

        Returns:
            The newly created MessageBubble in AI role.
        """
        bubble = MessageBubble(MessageRole.AI)
        self._active_ai_bubble = bubble
        self._add_bubble(bubble)
        self._scroll_to_bottom()
        return bubble

    def append_token_to_last_ai(self, token: str) -> None:
        """Append a streaming token to the most recently added AI bubble.

        Scroll-to-bottom only if the user was already at the bottom, so
        that reading earlier messages is not interrupted by new content.

        Args:
            token: A single streaming token from the LLM worker.
        """
        if self._active_ai_bubble is None:
            return

        at_bottom = self._is_at_bottom()
        scroll_bar = self._scroll_area.verticalScrollBar()
        saved_pos = scroll_bar.value()

        self._active_ai_bubble.append_token(token)
        self._container.adjustSize()

        if at_bottom:
            self._scroll_to_bottom()
        else:
            scroll_bar.setValue(saved_pos)

    def finalize_last_ai(self, full_text: str) -> None:
        """Re-render the last AI bubble from the complete text.

        Called when generation finishes to fix any partial Markdown
        at the stream boundary (e.g., incomplete code fences).

        Args:
            full_text: The complete response text from the LLM.
        """
        if self._active_ai_bubble is not None:
            self._active_ai_bubble.set_text(full_text)
            self._active_ai_bubble = None

    def add_system_message(self, text: str) -> None:
        """Append a system-role bubble for flow prompts.

        Used by conversational flows (e.g., /new quick-create) to display
        non-user, non-AI instructions.

        Args:
            text: System message text.
        """
        bubble = MessageBubble(MessageRole.SYSTEM)
        bubble.set_text(text)
        self._add_bubble(bubble)
        self._scroll_to_bottom()

    def show_error_bubble(self, message: str) -> None:
        """Append an AI-role bubble styled as an error.

        Args:
            message: Human-readable error description.
        """
        bubble = MessageBubble(MessageRole.AI)
        bubble.setObjectName("error_bubble")
        bubble.set_text(f"**Error:** {message}")
        self._add_bubble(bubble)
        self._scroll_to_bottom()
        self._active_ai_bubble = None

    def clear_history(self) -> None:
        """Remove all message bubbles from the thread.

        Called on app restart (not user-accessible in this version).
        """
        self._active_ai_bubble = None
        while self._message_layout.count() > 1:  # keep the top spacer
            item = self._message_layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()

    def _is_at_bottom(self) -> bool:
        """Return True if the scroll area is at or within 10px of the bottom.

        Returns:
            True when the user has not scrolled up from the bottom.
        """
        scroll_bar = self._scroll_area.verticalScrollBar()
        return scroll_bar.value() >= scroll_bar.maximum() - 10

    def _scroll_to_bottom(self) -> None:
        """Scroll the message area to the bottom."""
        scroll_bar = self._scroll_area.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())

    # -- Internal setup ------------------------------------------------------

    def _setup_ui(self) -> None:
        """Build the scroll area and inner message container."""
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        self._container = QWidget()
        self._message_layout = QVBoxLayout(self._container)
        self._message_layout.setContentsMargins(8, 8, 8, 8)
        self._message_layout.setSpacing(8)
        self._message_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Top spacer: pushes bubbles toward bottom until content overflows.
        spacer = QSpacerItem(
            0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )
        self._message_layout.addItem(spacer)

        # Placeholder shown when the thread is empty.
        self._placeholder = QLabel(
            "Select a template with / or type a message to get started."
        )
        self._placeholder.setObjectName("chat_placeholder")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setWordWrap(True)
        self._message_layout.addWidget(self._placeholder)

        self._scroll_area.setWidget(self._container)
        outer.addWidget(self._scroll_area)

    def _add_bubble(self, bubble: MessageBubble) -> None:
        """Add a bubble to the message layout and hide the placeholder.

        Args:
            bubble: The MessageBubble to append.
        """
        if self._placeholder.isVisible():
            self._placeholder.hide()
        self._message_layout.addWidget(bubble)
        self._container.adjustSize()
