"""Message bubble widget for the chat UI.

Provides MessageBubble, a single message in the chat thread.
User messages appear as plain-text right-aligned bubbles.
AI messages render Markdown as HTML in a QTextBrowser with a Copy button.
"""

from enum import Enum

import mistune
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QClipboard, QGuiApplication
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

# Module-level Markdown renderer — created once for performance.
_MARKDOWN = mistune.create_markdown(
    renderer=mistune.HTMLRenderer(escape=False),
    plugins=["strikethrough", "table"],
)


class MessageRole(str, Enum):
    """Role of the message author in the chat thread."""

    USER = "user"
    AI = "ai"
    SYSTEM = "system"


class MessageBubble(QWidget):
    """A single message in the chat thread.

    Displays user messages as plain text in a right-aligned bubble,
    and AI messages as Markdown-rendered HTML in a QTextBrowser with a
    Copy button. Stores the raw Markdown source separately so the Copy
    button never copies rendered HTML.

    Attributes:
        role: The MessageRole (USER or AI) for this bubble.
        copy_requested: Signal emitted with raw Markdown text when Copy is clicked.
    """

    copy_requested = pyqtSignal(str)

    def __init__(self, role: MessageRole, parent: QWidget | None = None) -> None:
        """Initialize a bubble for the given role.

        Args:
            role: MessageRole.USER or MessageRole.AI.
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self.role = role
        self._raw_text: str = ""

        self._setup_ui()

    # -- Public API ----------------------------------------------------------

    def set_text(self, text: str) -> None:
        """Set the full content, replacing any prior content.

        For user bubbles: sets plain text.
        For AI bubbles: stores raw Markdown and renders HTML.

        Args:
            text: Plain text for user bubbles; Markdown for AI bubbles.
        """
        self._raw_text = text
        if self.role in (MessageRole.USER, MessageRole.SYSTEM):
            self._label.setText(text)
        else:
            self._browser.setHtml(self._render_markdown(text))

    def append_token(self, token: str) -> None:
        """Append a streaming token to an AI bubble.

        Accumulates raw Markdown and re-renders HTML from the full string.
        Scroll management is handled by ChatWidget, not here.

        Args:
            token: A single streaming token (may be partial word/line).
        """
        self._raw_text += token
        if self.role == MessageRole.AI:
            self._browser.setHtml(self._render_markdown(self._raw_text))

    def get_raw_text(self) -> str:
        """Return the raw text/Markdown source (never HTML).

        Returns:
            The accumulated raw Markdown string for AI bubbles,
            or plain text for user bubbles.
        """
        return self._raw_text

    def _render_markdown(self, text: str) -> str:
        """Convert Markdown to styled HTML for display in QTextBrowser.

        Injects inline CSS for code blocks and tables because QTextBrowser
        does not inherit the Qt application stylesheet for inner HTML content.

        Args:
            text: Markdown-formatted text.

        Returns:
            HTML string suitable for QTextBrowser.setHtml().
        """
        html = _MARKDOWN(text)
        return (
            "<style>"
            "body { color: #d4d4d4; }"
            "pre { background-color: #1a1a1a; padding: 8px;"
            "      border-radius: 4px; overflow-x: auto; }"
            "code { font-family: monospace; color: #ce9178; }"
            "table { border-collapse: collapse; }"
            "td, th { border: 1px solid #3c3c3c; padding: 4px; }"
            "</style>"
            f"{html}"
        )

    def _copy_to_clipboard(self) -> None:
        """Copy raw Markdown text to the system clipboard.

        Slot for the Copy button. Emits copy_requested with raw text.
        """
        clipboard: QClipboard = QGuiApplication.clipboard()
        clipboard.setText(self._raw_text)
        self.copy_requested.emit(self._raw_text)

    # -- Internal setup ------------------------------------------------------

    def _setup_ui(self) -> None:
        """Build the bubble layout based on role."""
        outer = QHBoxLayout(self)
        outer.setContentsMargins(4, 2, 4, 2)

        if self.role == MessageRole.USER:
            self._setup_user_bubble(outer)
        elif self.role == MessageRole.SYSTEM:
            self._setup_system_bubble(outer)
        else:
            self._setup_ai_bubble(outer)

    def _setup_user_bubble(self, outer: QHBoxLayout) -> None:
        """Right-aligned plain-text bubble for user messages."""
        outer.addStretch(1)

        container = QWidget()
        container.setObjectName("user_bubble")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 6, 10, 6)

        self._label = QLabel()
        self._label.setWordWrap(True)
        self._label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        layout.addWidget(self._label)

        outer.addWidget(container)

    def _setup_system_bubble(self, outer: QHBoxLayout) -> None:
        """Center-aligned system prompt bubble (no avatar, neutral style)."""
        container = QWidget()
        container.setObjectName("system_bubble")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 6, 10, 6)

        self._label = QLabel()
        self._label.setWordWrap(True)
        self._label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        layout.addWidget(self._label)

        outer.addWidget(container)

    def _setup_ai_bubble(self, outer: QHBoxLayout) -> None:
        """Left-aligned Markdown-rendering bubble with Copy button for AI messages."""
        container = QWidget()
        container.setObjectName("ai_bubble")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(4)

        # Header row: sender label + copy button
        header = QHBoxLayout()
        sender = QLabel("AI")
        sender.setObjectName("bubble_sender")
        header.addWidget(sender)
        header.addStretch(1)

        self._copy_btn = QPushButton("Copy")
        self._copy_btn.setObjectName("secondary")
        self._copy_btn.setFixedHeight(22)
        self._copy_btn.clicked.connect(self._copy_to_clipboard)
        header.addWidget(self._copy_btn)
        layout.addLayout(header)

        # QTextBrowser for Markdown-rendered HTML
        self._browser = QTextBrowser()
        self._browser.setOpenExternalLinks(False)
        self._browser.setReadOnly(True)
        self._browser.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        self._browser.document().setDocumentMargin(0)
        layout.addWidget(self._browser)

        outer.addWidget(container)
        outer.addStretch(1)
