"""History browser dialog for browsing and re-using past generated outputs.

Provides a filterable dialog with search, template dropdown, favorites toggle,
per-entry detail pane, copy/favorite/re-use actions. Backed by PromptHistoryStore.
"""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from templatr.core.prompt_history import PromptHistoryEntry, PromptHistoryStore


class HistoryBrowserDialog(QDialog):
    """Dialog for browsing, filtering, and re-using prompt history entries.

    Attributes:
        output_reused: Emitted with the output text when the user clicks Re-use.
    """

    output_reused = pyqtSignal(str)

    def __init__(
        self,
        store: Optional[PromptHistoryStore] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        """Initialize the history browser dialog.

        Args:
            store: PromptHistoryStore instance. Falls back to the global singleton.
            parent: Parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Prompt History")
        self.setMinimumSize(600, 400)
        self.resize(750, 520)

        if store is None:
            from templatr.core.prompt_history import get_prompt_history_store

            store = get_prompt_history_store()
        self._store = store
        self._entries: list[PromptHistoryEntry] = []

        self._setup_ui()
        self._load_entries()
        self._apply_filters()

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        """Build the dialog layout: toolbar, entry list, detail pane, actions."""
        layout = QVBoxLayout(self)

        # -- Toolbar row: search + template dropdown + favorites checkbox --
        toolbar = QHBoxLayout()

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Search prompts and outputs…")
        self._search_input.setClearButtonEnabled(True)
        self._search_input.textChanged.connect(self._apply_filters)
        toolbar.addWidget(self._search_input, stretch=1)

        self._template_combo = QComboBox()
        self._template_combo.setMinimumWidth(140)
        self._template_combo.addItem("All Templates")
        self._template_combo.currentIndexChanged.connect(self._apply_filters)
        toolbar.addWidget(self._template_combo)

        self._favorites_checkbox = QCheckBox("Favorites only")
        self._favorites_checkbox.toggled.connect(self._apply_filters)
        toolbar.addWidget(self._favorites_checkbox)

        layout.addLayout(toolbar)

        # -- Splitter: entry list | detail pane --
        splitter = QSplitter(Qt.Orientation.Vertical)

        self._entry_list = QListWidget()
        self._entry_list.currentRowChanged.connect(self._on_selection_changed)
        splitter.addWidget(self._entry_list)

        detail_container = QWidget()
        detail_layout = QVBoxLayout(detail_container)
        detail_layout.setContentsMargins(0, 4, 0, 0)

        detail_header = QLabel("Output")
        detail_header.setStyleSheet("font-weight: bold;")
        detail_layout.addWidget(detail_header)

        self._detail_pane = QPlainTextEdit()
        self._detail_pane.setReadOnly(True)
        detail_layout.addWidget(self._detail_pane)

        splitter.addWidget(detail_container)
        splitter.setSizes([200, 200])
        layout.addWidget(splitter, stretch=1)

        # -- Placeholder label (shown when list is empty) --
        self._placeholder = QLabel("No history yet.")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setStyleSheet("color: #888; font-style: italic; padding: 20px;")
        self._placeholder.setVisible(False)
        layout.addWidget(self._placeholder)

        # -- Action buttons --
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self._copy_btn = QPushButton("Copy Output")
        self._copy_btn.setEnabled(False)
        self._copy_btn.clicked.connect(self._copy_output)
        btn_row.addWidget(self._copy_btn)

        self._favorite_btn = QPushButton("Favorite")
        self._favorite_btn.setEnabled(False)
        self._favorite_btn.clicked.connect(self._toggle_favorite)
        btn_row.addWidget(self._favorite_btn)

        self._reuse_btn = QPushButton("Re-use")
        self._reuse_btn.setEnabled(False)
        self._reuse_btn.clicked.connect(self._reuse_output)
        btn_row.addWidget(self._reuse_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _load_entries(self) -> None:
        """Load all entries from the store and populate the template dropdown."""
        self._entries = self._store.list_entries(limit=None)
        # Newest first (list_entries already sorts reverse-chronological)

        # Populate template dropdown with unique template names
        templates = sorted({e.template_name for e in self._entries if e.template_name != "__plain__"})
        self._template_combo.blockSignals(True)
        current = self._template_combo.currentText()
        while self._template_combo.count() > 1:
            self._template_combo.removeItem(1)
        for name in templates:
            self._template_combo.addItem(name)
        # Restore previous selection if still valid
        idx = self._template_combo.findText(current)
        if idx >= 0:
            self._template_combo.setCurrentIndex(idx)
        self._template_combo.blockSignals(False)

        # Populate list widget
        self._entry_list.clear()
        for entry in self._entries:
            item = QListWidgetItem()
            star = "★ " if entry.favorite else ""
            prompt_preview = entry.prompt.strip().replace("\n", " ")
            if len(prompt_preview) > 60:
                prompt_preview = f"{prompt_preview[:57]}..."
            template_label = entry.template_name if entry.template_name != "__plain__" else "plain"
            item.setText(f"{star}[{template_label}] {prompt_preview}  ({entry.created_at})")
            item.setData(Qt.ItemDataRole.UserRole, entry)
            self._entry_list.addItem(item)

    # ------------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------------

    def _apply_filters(self) -> None:
        """Show/hide list items based on current search, template, and favorites filters."""
        query = self._search_input.text().strip().lower()
        template_filter = self._template_combo.currentText()
        fav_only = self._favorites_checkbox.isChecked()

        visible_count = 0
        for i in range(self._entry_list.count()):
            item = self._entry_list.item(i)
            entry: PromptHistoryEntry = item.data(Qt.ItemDataRole.UserRole)
            hidden = False

            if template_filter != "All Templates" and entry.template_name != template_filter:
                hidden = True
            if fav_only and not entry.favorite:
                hidden = True
            if query and query not in entry.prompt.lower() and query not in entry.output.lower():
                hidden = True

            item.setHidden(hidden)
            if not hidden:
                visible_count += 1

        self._placeholder.setVisible(visible_count == 0)

    # ------------------------------------------------------------------
    # Selection
    # ------------------------------------------------------------------

    def _on_selection_changed(self, row: int) -> None:
        """Update detail pane and button states when the selected entry changes.

        Args:
            row: Current row index, or -1 when nothing is selected.
        """
        if row < 0 or row >= self._entry_list.count():
            self._detail_pane.setPlainText("")
            self._copy_btn.setEnabled(False)
            self._favorite_btn.setEnabled(False)
            self._reuse_btn.setEnabled(False)
            return

        item = self._entry_list.item(row)
        entry: PromptHistoryEntry = item.data(Qt.ItemDataRole.UserRole)
        self._detail_pane.setPlainText(entry.output)

        self._copy_btn.setEnabled(True)
        self._reuse_btn.setEnabled(True)
        self._favorite_btn.setEnabled(True)
        self._favorite_btn.setText("Unfavorite" if entry.favorite else "Favorite")

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _copy_output(self) -> None:
        """Copy the selected entry's output to the system clipboard."""
        text = self._detail_pane.toPlainText()
        if text:
            QApplication.clipboard().setText(text)

    def _toggle_favorite(self) -> None:
        """Toggle the favorite state of the selected entry."""
        row = self._entry_list.currentRow()
        if row < 0:
            return

        item = self._entry_list.item(row)
        entry: PromptHistoryEntry = item.data(Qt.ItemDataRole.UserRole)
        new_state = not entry.favorite
        self._store.mark_favorite(entry.id, favorite=new_state)

        # Refresh the entry in-place
        entry.favorite = new_state
        star = "★ " if entry.favorite else ""
        prompt_preview = entry.prompt.strip().replace("\n", " ")
        if len(prompt_preview) > 60:
            prompt_preview = f"{prompt_preview[:57]}..."
        template_label = entry.template_name if entry.template_name != "__plain__" else "plain"
        item.setText(f"{star}[{template_label}] {prompt_preview}  ({entry.created_at})")
        self._favorite_btn.setText("Unfavorite" if new_state else "Favorite")

        # Re-apply filters (may hide if favorites-only is on)
        self._apply_filters()

    def _reuse_output(self) -> None:
        """Emit output_reused signal with the selected entry's output and close."""
        text = self._detail_pane.toPlainText()
        if text:
            self.output_reused.emit(text)
            self.accept()
