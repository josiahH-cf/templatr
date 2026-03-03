"""Version history browser dialog for Templatr.

Displays a list of template version snapshots with a content preview pane
and a restore action. Replaces the old QInputDialog-based version picker.
"""

from __future__ import annotations

from typing import List, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from templatr.core.templates import Template, TemplateVersion


class VersionHistoryDialog(QDialog):
    """Dialog for browsing and restoring template version history.

    Attributes:
        version_restored: Emitted with the version number when the user
            clicks Restore.
    """

    version_restored = pyqtSignal(int)

    def __init__(
        self,
        template: Template,
        versions: List[TemplateVersion],
        parent: Optional[QWidget] = None,
    ) -> None:
        """Initialize the version history dialog.

        Args:
            template: The template whose history is being browsed.
            versions: List of TemplateVersion objects (ascending order).
            parent: Parent widget.
        """
        super().__init__(parent)
        self.template = template
        self.versions = versions
        # Store reversed for display (most recent first)
        self._display_versions = list(reversed(versions))

        self.setWindowTitle(f"Version History — {template.name}")
        self.setMinimumSize(700, 450)
        self._setup_ui()
        self._populate_versions()

    def _setup_ui(self) -> None:
        """Build the dialog layout."""
        layout = QVBoxLayout(self)

        # Header
        header = QLabel(f"Version History — {self.template.name}")
        header.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(header)

        # Splitter: version list | content preview
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: version list
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)

        list_label = QLabel("Versions")
        list_label.setStyleSheet("font-weight: bold;")
        left_layout.addWidget(list_label)

        self.version_list = QListWidget()
        self.version_list.currentRowChanged.connect(self._on_version_selected)
        left_layout.addWidget(self.version_list)

        splitter.addWidget(left)

        # Right: content preview
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)

        preview_label = QLabel("Content Preview")
        preview_label.setStyleSheet("font-weight: bold;")
        right_layout.addWidget(preview_label)

        self.preview_pane = QPlainTextEdit()
        self.preview_pane.setReadOnly(True)
        self.preview_pane.setPlaceholderText("Select a version to preview its content.")
        right_layout.addWidget(self.preview_pane)

        splitter.addWidget(right)
        splitter.setSizes([250, 450])

        layout.addWidget(splitter)

        # Bottom: restore + close buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.restore_btn = QPushButton("Restore")
        self.restore_btn.setEnabled(False)
        self.restore_btn.setToolTip("Restore the selected version (current state is backed up)")
        self.restore_btn.clicked.connect(self._on_restore)
        btn_layout.addWidget(self.restore_btn)

        close_btn = QPushButton("Close")
        close_btn.setObjectName("secondary")
        close_btn.clicked.connect(self.reject)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def _populate_versions(self) -> None:
        """Fill the version list from the display-order versions."""
        self.version_list.clear()
        for v in self._display_versions:
            timestamp = v.timestamp[:19].replace("T", " ") if v.timestamp else "Unknown"
            label = f"v{v.version}"
            if v.version == 1:
                label += " (Original)"
            if v.note:
                label += f" — {v.note}"
            label += f"  [{timestamp}]"

            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, v.version)
            self.version_list.addItem(item)

    def _on_version_selected(self, row: int) -> None:
        """Handle version list selection change.

        Args:
            row: The selected row index, or -1 if no selection.
        """
        if row < 0 or row >= len(self._display_versions):
            self.preview_pane.clear()
            self.restore_btn.setEnabled(False)
            return

        version = self._display_versions[row]
        content = version.template_data.get("content", "")
        self.preview_pane.setPlainText(content)
        self.restore_btn.setEnabled(True)

    def _on_restore(self) -> None:
        """Handle restore button click."""
        current = self.version_list.currentItem()
        if current is None:
            return

        version_num = current.data(Qt.ItemDataRole.UserRole)
        self.version_restored.emit(version_num)
        self.accept()
