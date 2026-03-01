"""Detail view dialog for A/B test results.

Provides ABTestResultsDialog: a modal dialog showing all iteration outputs
with per-entry latency/token metadata, full-text preview, and a "Pick as
Winner" action.
"""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)


class ABTestResultsDialog(QDialog):
    """Modal dialog for reviewing all A/B test iteration outputs.

    Displays a list of iterations on the left and the full output for the
    selected iteration on the right.  The "Pick as Winner" button emits
    ``winner_selected`` with the 0-based index of the chosen iteration so
    the caller can mark it as a favourite in history.

    Attributes:
        winner_selected: Emitted with the 0-based iteration index when the
            user clicks "Pick as Winner".
        list_widget: The QListWidget showing iteration summaries (public for
            tests to inspect item count and labels).
    """

    winner_selected = pyqtSignal(int)  # 0-based index

    def __init__(
        self,
        results: list[dict],
        history_ids: list[str],
        parent: Optional[QWidget] = None,
    ) -> None:
        """Initialise the dialog.

        Args:
            results: List of per-iteration result dicts, each containing:
                ``iteration``, ``output``, ``latency_seconds``,
                ``prompt_tokens_est``, ``output_tokens_est``.
            history_ids: Parallel list of prompt-history entry IDs; same
                length as ``results``.
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("A/B Test Results")
        self.setMinimumSize(700, 450)
        self.resize(820, 540)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        self._results = results
        self._history_ids = history_ids

        self._setup_ui()
        if results:
            self.list_widget.setCurrentRow(0)

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        """Build the dialog layout."""
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        header = QLabel(
            f"<b>A/B Test Results</b> — {len(self._results)} iterations"
        )
        header.setTextFormat(Qt.TextFormat.RichText)
        root.addWidget(header)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # Left: list of iterations
        self.list_widget = QListWidget()
        self.list_widget.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding
        )
        for r in self._results:
            label = (
                f"Iteration {r['iteration']}  "
                f"({r['latency_seconds']:.2f}s, "
                f"~{r['output_tokens_est']} tok)"
            )
            item = QListWidgetItem(label)
            self.list_widget.addItem(item)

        self.list_widget.currentRowChanged.connect(self._on_row_changed)
        splitter.addWidget(self.list_widget)

        # Right: full output view + metadata
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(6)

        self._meta_label = QLabel()
        self._meta_label.setTextFormat(Qt.TextFormat.RichText)
        right_layout.addWidget(self._meta_label)

        self._output_edit = QPlainTextEdit()
        self._output_edit.setReadOnly(True)
        self._output_edit.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        right_layout.addWidget(self._output_edit)

        splitter.addWidget(right_panel)
        splitter.setSizes([220, 560])
        root.addWidget(splitter, stretch=1)

        # Bottom: action buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self._copy_btn = QPushButton("Copy Output")
        self._copy_btn.clicked.connect(self._copy_output)
        btn_row.addWidget(self._copy_btn)

        btn_row.addStretch()

        self._pick_btn = QPushButton("Pick as Winner ★")
        self._pick_btn.setDefault(False)
        self._pick_btn.clicked.connect(self._pick_winner)
        btn_row.addWidget(self._pick_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)

        root.addLayout(btn_row)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_row_changed(self, row: int) -> None:
        """Update the right pane when iteration selection changes."""
        if row < 0 or row >= len(self._results):
            self._output_edit.clear()
            self._meta_label.clear()
            return

        r = self._results[row]
        self._meta_label.setText(
            f"<b>Iteration {r['iteration']}</b> &nbsp;|&nbsp; "
            f"Latency: <b>{r['latency_seconds']:.2f}s</b> &nbsp;|&nbsp; "
            f"Prompt tokens (est.): <b>{r['prompt_tokens_est']}</b> &nbsp;|&nbsp; "
            f"Output tokens (est.): <b>{r['output_tokens_est']}</b>"
        )
        self._output_edit.setPlainText(r.get("output") or "")

    def _copy_output(self) -> None:
        """Copy the currently displayed output text to the clipboard."""
        text = self._output_edit.toPlainText()
        if text:
            QApplication.clipboard().setText(text)

    def _pick_winner(self) -> None:
        """Emit winner_selected with the currently selected iteration index."""
        row = self.list_widget.currentRow()
        if row < 0:
            return
        self.winner_selected.emit(row)
