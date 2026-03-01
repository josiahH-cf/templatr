"""Catalog browser dialog for Templatr.

Allows users to browse, search, and install community templates from the
remote catalog index without leaving the application.
"""

import logging
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from templatr.ui.workers import CatalogFetchWorker, CatalogInstallWorker

logger = logging.getLogger(__name__)

_EMPTY_STATE_GUIDANCE = (
    "No templates found.\n\n"
    "This could mean:\n"
    "  • The catalog URL is unreachable — check your internet connection.\n"
    "  • The catalog has not been set up yet.\n\n"
    "To set up or change the catalog URL, open /settings and update the\n"
    "Catalog URL field.  See the catalog README for hosting instructions:\n"
    "  https://github.com/josiahH-cf/templatr-catalog"
)

_TAG_ALL = "All tags"

# Page indices for the stacked widget
_PAGE_LOADING = 0
_PAGE_CONTENT = 1
_PAGE_EMPTY = 2


class CatalogBrowserDialog(QDialog):
    """Dialog for browsing and installing community templates from the catalog.

    Shows a searchable, tag-filtered list of available templates with a
    detail preview pane.  Template installation is performed in a background
    worker.

    Emits ``template_installed(str)`` after a template is successfully saved
    so the caller can refresh the template tree.
    """

    #: Emitted with the installed template's name after a successful install.
    template_installed = pyqtSignal(str)

    def __init__(self, catalog_url: str, manager, parent=None):
        """Initialise the dialog.

        Args:
            catalog_url: URL of the catalog JSON index file.
            manager: The application TemplateManager instance.
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self.catalog_url = catalog_url
        self.manager = manager

        self._all_entries: list[dict] = []
        self._filtered_entries: list[dict] = []
        self._fetch_worker: Optional[CatalogFetchWorker] = None
        self._install_worker: Optional[CatalogInstallWorker] = None
        self._installing = False

        self.setWindowTitle("Browse Community Templates")
        self.setMinimumSize(700, 500)
        self._setup_ui()
        self._start_fetch()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        """Build the dialog layout."""
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        # --- Status bar (loading / error, shown above content) ---
        self._status_label = QLabel()
        self._status_label.setWordWrap(True)
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.hide()
        root.addWidget(self._status_label)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 0)  # marquee / indeterminate
        self._progress_bar.setFixedHeight(6)
        root.addWidget(self._progress_bar)

        # --- Stacked widget: loading | content | empty ---
        self._stack = QStackedWidget()
        root.addWidget(self._stack, stretch=1)

        self._stack.addWidget(self._build_loading_page())   # _PAGE_LOADING
        self._stack.addWidget(self._build_content_page())   # _PAGE_CONTENT
        self._stack.addWidget(self._build_empty_page())     # _PAGE_EMPTY

        self._stack.setCurrentIndex(_PAGE_LOADING)

        # --- Bottom buttons ---
        bottom = QHBoxLayout()
        bottom.setSpacing(8)

        self._install_btn = QPushButton("Install")
        self._install_btn.setEnabled(False)
        self._install_btn.setToolTip("Select a template to install it.")
        self._install_btn.clicked.connect(self._on_install_clicked)
        bottom.addWidget(self._install_btn)

        bottom.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        bottom.addWidget(close_btn)

        root.addLayout(bottom)

    def _build_loading_page(self) -> QWidget:
        """Return a placeholder shown while the catalog is being fetched."""
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.addStretch()
        label = QLabel("Fetching catalog…")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color: #888; font-size: 13px;")
        layout.addWidget(label)
        layout.addStretch()
        return w

    def _build_content_page(self) -> QWidget:
        """Return the main browse/search/preview layout."""
        w = QWidget()
        outer = QVBoxLayout(w)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(6)

        # --- Filter row ---
        filter_row = QHBoxLayout()
        filter_row.setSpacing(6)

        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Search by name, description, author, or tag…")
        self._search_edit.setClearButtonEnabled(True)
        self._search_edit.textChanged.connect(self._apply_filter)
        filter_row.addWidget(self._search_edit, stretch=3)

        self._tag_combo = QComboBox()
        self._tag_combo.addItem(_TAG_ALL)
        self._tag_combo.currentTextChanged.connect(self._apply_filter)
        self._tag_combo.setMinimumWidth(140)
        filter_row.addWidget(self._tag_combo, stretch=1)

        outer.addLayout(filter_row)

        # --- Splitter: list | detail ---
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        self._list_widget = QListWidget()
        self._list_widget.currentRowChanged.connect(self._on_selection_changed)
        splitter.addWidget(self._list_widget)

        detail_widget = self._build_detail_pane()
        splitter.addWidget(detail_widget)
        splitter.setSizes([280, 380])

        outer.addWidget(splitter, stretch=1)
        return w

    def _build_detail_pane(self) -> QWidget:
        """Return the right-hand detail/preview pane."""
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 0, 0, 0)
        layout.setSpacing(6)

        self._detail_name = QLabel()
        self._detail_name.setStyleSheet("font-weight: bold; font-size: 14px;")
        self._detail_name.setWordWrap(True)
        layout.addWidget(self._detail_name)

        self._detail_author = QLabel()
        self._detail_author.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self._detail_author)

        self._detail_version = QLabel()
        self._detail_version.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self._detail_version)

        self._detail_tags = QLabel()
        self._detail_tags.setWordWrap(True)
        self._detail_tags.setStyleSheet("color: #5a9fd4; font-size: 11px;")
        layout.addWidget(self._detail_tags)

        sep = QLabel()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #444; margin: 4px 0;")
        layout.addWidget(sep)

        self._detail_desc = QLabel()
        self._detail_desc.setWordWrap(True)
        self._detail_desc.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self._detail_desc, stretch=1)

        self._clear_detail()
        return w

    def _build_empty_page(self) -> QWidget:
        """Return the empty-state placeholder."""
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.addStretch()
        label = QLabel(_EMPTY_STATE_GUIDANCE)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setWordWrap(True)
        label.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(label)
        layout.addStretch()
        return w

    # ------------------------------------------------------------------
    # Catalog fetch
    # ------------------------------------------------------------------

    def _start_fetch(self) -> None:
        """Start the background catalog fetch worker."""
        self._progress_bar.show()
        self._stack.setCurrentIndex(_PAGE_LOADING)

        self._fetch_worker = CatalogFetchWorker(self.catalog_url)
        self._fetch_worker.catalog_ready.connect(self._on_catalog_ready)
        self._fetch_worker.error.connect(self._on_fetch_error)
        self._fetch_worker.start()

    def _on_catalog_ready(self, entries: list) -> None:
        """Handle the fetched and validated catalog entries."""
        self._progress_bar.hide()
        self._all_entries = entries

        if not entries:
            self._stack.setCurrentIndex(_PAGE_EMPTY)
            return

        self._populate_tags(entries)
        self._apply_filter()
        self._stack.setCurrentIndex(_PAGE_CONTENT)

    def _on_fetch_error(self, message: str) -> None:
        """Display a fetch error and show the empty state."""
        self._progress_bar.hide()
        self._status_label.setText(f"⚠ {message}")
        self._status_label.setStyleSheet("color: #e06c75; font-size: 11px;")
        self._status_label.show()
        self._stack.setCurrentIndex(_PAGE_EMPTY)

    # ------------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------------

    def _populate_tags(self, entries: list[dict]) -> None:
        """Populate the tag combo-box from all tags in the catalog."""
        self._tag_combo.blockSignals(True)
        self._tag_combo.clear()
        self._tag_combo.addItem(_TAG_ALL)

        all_tags: set[str] = set()
        for entry in entries:
            for tag in entry.get("tags", []):
                all_tags.add(str(tag))

        for tag in sorted(all_tags):
            self._tag_combo.addItem(tag)

        self._tag_combo.blockSignals(False)

    def _apply_filter(self) -> None:
        """Filter the entry list by the current search text and tag."""
        query = self._search_edit.text().strip().lower() if hasattr(self, "_search_edit") else ""
        tag_filter = self._tag_combo.currentText() if hasattr(self, "_tag_combo") else _TAG_ALL

        results = []
        for entry in self._all_entries:
            # Tag filter
            if tag_filter != _TAG_ALL:
                entry_tags = [str(t).lower() for t in entry.get("tags", [])]
                if tag_filter.lower() not in entry_tags:
                    continue

            # Text search (case-insensitive across name/description/author/tags)
            if query:
                searchable = " ".join([
                    entry.get("name", ""),
                    entry.get("description", ""),
                    entry.get("author", ""),
                    " ".join(str(t) for t in entry.get("tags", [])),
                ]).lower()
                if query not in searchable:
                    continue

            results.append(entry)

        self._filtered_entries = results
        self._refresh_list()

    def _refresh_list(self) -> None:
        """Repopulate the QListWidget from _filtered_entries."""
        self._list_widget.blockSignals(True)
        self._list_widget.clear()
        for entry in self._filtered_entries:
            item = QListWidgetItem(entry.get("name", "(Unnamed)"))
            item.setToolTip(entry.get("description", ""))
            self._list_widget.addItem(item)
        self._list_widget.blockSignals(False)

        self._clear_detail()
        self._install_btn.setEnabled(False)

    # ------------------------------------------------------------------
    # Selection / detail pane
    # ------------------------------------------------------------------

    def _on_selection_changed(self, row: int) -> None:
        """Update the detail pane and install button for the selected entry."""
        if row < 0 or row >= len(self._filtered_entries):
            self._clear_detail()
            self._install_btn.setEnabled(False)
            return

        entry = self._filtered_entries[row]
        self._detail_name.setText(entry.get("name", ""))
        self._detail_author.setText(f"by {entry.get('author', 'unknown')}")
        self._detail_version.setText(f"v{entry.get('version', '?')}")
        tags = entry.get("tags", [])
        self._detail_tags.setText("  ".join(f"#{t}" for t in tags))
        self._detail_desc.setText(entry.get("description", ""))

        self._install_btn.setEnabled(not self._installing)

    def _clear_detail(self) -> None:
        """Reset all detail-pane labels to empty."""
        self._detail_name.setText("Select a template to preview it.")
        self._detail_name.setStyleSheet("font-size: 12px; color: #888;")
        self._detail_author.clear()
        self._detail_version.clear()
        self._detail_tags.clear()
        self._detail_desc.clear()

    # ------------------------------------------------------------------
    # Install
    # ------------------------------------------------------------------

    def _on_install_clicked(self) -> None:
        """Start installing the currently selected catalog entry."""
        row = self._list_widget.currentRow()
        if row < 0 or row >= len(self._filtered_entries):
            return

        entry = self._filtered_entries[row]
        download_url = entry.get("download_url", "")
        if not download_url:
            QMessageBox.warning(self, "Install Failed", "This entry has no download URL.")
            return

        self._set_installing(True)
        self._install_worker = CatalogInstallWorker(download_url, self.manager)
        self._install_worker.installed.connect(self._on_installed)
        self._install_worker.conflict.connect(self._on_install_conflict)
        self._install_worker.error.connect(self._on_install_error)
        self._install_worker.start()

    def _set_installing(self, busy: bool) -> None:
        """Enable or disable the install button while a download is running."""
        self._installing = busy
        self._install_btn.setEnabled(not busy)
        self._install_btn.setText("Installing…" if busy else "Install")
        if busy:
            self._progress_bar.show()
        else:
            self._progress_bar.hide()

    def _on_installed(self, template_name: str) -> None:
        """Handle a successful template installation."""
        self._set_installing(False)
        self._status_label.setText(f"✓ '{template_name}' installed successfully.")
        self._status_label.setStyleSheet("color: #98c379; font-size: 11px;")
        self._status_label.show()
        self.template_installed.emit(template_name)

    def _on_install_conflict(self, template) -> None:
        """Handle a name conflict: ask the user how to resolve it."""
        self._set_installing(False)

        reply = QMessageBox.question(
            self,
            "Name Conflict",
            f"A template named '{template.name}' already exists.\n\n"
            "Would you like to overwrite it?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No
            | QMessageBox.StandardButton.Cancel,
        )

        if reply == QMessageBox.StandardButton.Cancel:
            return

        if reply == QMessageBox.StandardButton.No:
            new_name, ok = QInputDialog.getText(
                self,
                "Rename Template",
                "Enter a new name for the imported template:",
            )
            if not ok or not new_name.strip():
                return
            template.name = new_name.strip()

        if self.manager.save(template):
            self._status_label.setText(f"✓ '{template.name}' installed successfully.")
            self._status_label.setStyleSheet("color: #98c379; font-size: 11px;")
            self._status_label.show()
            self.template_installed.emit(template.name)
        else:
            QMessageBox.critical(
                self,
                "Install Failed",
                f"Could not save template '{template.name}' to disk.",
            )

    def _on_install_error(self, message: str) -> None:
        """Show an install error in a message box."""
        self._set_installing(False)
        QMessageBox.warning(self, "Install Failed", message)

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def closeEvent(self, event) -> None:  # noqa: N802
        """Stop any running workers before closing."""
        for worker in (self._fetch_worker, self._install_worker):
            if worker is not None and worker.isRunning():
                worker.quit()
                worker.wait(1000)
        super().closeEvent(event)
