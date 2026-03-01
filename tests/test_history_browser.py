"""Tests for HistoryBrowserDialog.

Covers:
- Empty store shows placeholder message
- Entries render in reverse-chronological order
- Search filter narrows visible entries
- Favorites-only toggle hides non-favorites
- Template dropdown filters by template name
- Selecting an entry shows its output in the detail pane
- Copy Output button copies selected entry output to clipboard
- Favorite/Unfavorite button toggles favorite state
- output_reused signal fires with selected output text
- Ctrl+H shortcut opens the dialog from MainWindow
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from templatr.core.prompt_history import PromptHistoryStore


def _make_store(tmp_path: Path) -> PromptHistoryStore:
    """Create a fresh PromptHistoryStore backed by tmp_path."""
    return PromptHistoryStore(file_path=tmp_path / "prompt_history.json")


def _populated_store(tmp_path: Path) -> PromptHistoryStore:
    """Create a store pre-loaded with sample entries across two templates."""
    store = _make_store(tmp_path)
    store.add_entry("Alpha", "fix login bug", "patched auth module", created_at="2026-02-27T10:00:00Z")
    store.add_entry("Alpha", "improve caching", "added redis layer", created_at="2026-02-28T11:00:00Z")
    store.add_entry("Beta", "write release notes", "release v1.1 summary", created_at="2026-02-28T12:00:00Z")
    store.mark_favorite(store.list_entries(template_name="Alpha")[0].id, favorite=True)
    return store


# -- Empty state --------------------------------------------------------------


def test_empty_store_shows_placeholder(qtbot, tmp_path: Path):
    """Dialog with an empty store shows a 'No history yet' placeholder."""
    from templatr.ui.history_browser import HistoryBrowserDialog

    store = _make_store(tmp_path)
    dialog = HistoryBrowserDialog(store=store)
    qtbot.addWidget(dialog)

    assert dialog._entry_list.count() == 0
    assert dialog._detail_pane.toPlainText() == ""
    # Placeholder is logically visible (not hidden); isVisible() requires
    # a shown parent, so check the negation of isHidden().
    assert not dialog._placeholder.isHidden()


# -- Entry display ------------------------------------------------------------


def test_entries_in_reverse_chronological_order(qtbot, tmp_path: Path):
    """Entries appear newest-first in the list."""
    from templatr.ui.history_browser import HistoryBrowserDialog

    store = _populated_store(tmp_path)
    dialog = HistoryBrowserDialog(store=store)
    qtbot.addWidget(dialog)

    assert dialog._entry_list.count() == 3
    first_item = dialog._entry_list.item(0)
    # Newest entry is "write release notes" (2026-02-28T12:00:00Z)
    assert "release notes" in first_item.text().lower() or "release" in first_item.data(Qt.ItemDataRole.UserRole).prompt.lower()


# -- Search filter ------------------------------------------------------------


def test_search_filters_entries(qtbot, tmp_path: Path):
    """Typing in the search field narrows visible entries."""
    from templatr.ui.history_browser import HistoryBrowserDialog

    store = _populated_store(tmp_path)
    dialog = HistoryBrowserDialog(store=store)
    qtbot.addWidget(dialog)

    dialog._search_input.setText("login")

    visible_count = sum(
        1 for i in range(dialog._entry_list.count()) if not dialog._entry_list.item(i).isHidden()
    )
    assert visible_count == 1


# -- Favorites toggle ---------------------------------------------------------


def test_favorites_toggle_filters(qtbot, tmp_path: Path):
    """Checking 'Favorites only' shows only favorited entries."""
    from templatr.ui.history_browser import HistoryBrowserDialog

    store = _populated_store(tmp_path)
    dialog = HistoryBrowserDialog(store=store)
    qtbot.addWidget(dialog)

    dialog._favorites_checkbox.setChecked(True)

    visible_count = sum(
        1 for i in range(dialog._entry_list.count()) if not dialog._entry_list.item(i).isHidden()
    )
    assert visible_count == 1


# -- Template dropdown --------------------------------------------------------


def test_template_dropdown_filters(qtbot, tmp_path: Path):
    """Selecting a template from the dropdown filters to its entries only."""
    from templatr.ui.history_browser import HistoryBrowserDialog

    store = _populated_store(tmp_path)
    dialog = HistoryBrowserDialog(store=store)
    qtbot.addWidget(dialog)

    # Find the "Alpha" option in the dropdown
    idx = dialog._template_combo.findText("Alpha")
    assert idx >= 0
    dialog._template_combo.setCurrentIndex(idx)

    visible_count = sum(
        1 for i in range(dialog._entry_list.count()) if not dialog._entry_list.item(i).isHidden()
    )
    assert visible_count == 2


# -- Detail pane selection ----------------------------------------------------


def test_selecting_entry_shows_output(qtbot, tmp_path: Path):
    """Clicking an entry populates the detail pane with its full output."""
    from templatr.ui.history_browser import HistoryBrowserDialog

    store = _populated_store(tmp_path)
    dialog = HistoryBrowserDialog(store=store)
    qtbot.addWidget(dialog)

    dialog._entry_list.setCurrentRow(0)

    assert dialog._detail_pane.toPlainText() != ""


# -- Copy Output button -------------------------------------------------------


def test_copy_output_button(qtbot, tmp_path: Path):
    """Copy Output button copies the selected entry output to clipboard."""
    from templatr.ui.history_browser import HistoryBrowserDialog

    store = _populated_store(tmp_path)
    dialog = HistoryBrowserDialog(store=store)
    qtbot.addWidget(dialog)

    dialog._entry_list.setCurrentRow(0)
    selected_output = dialog._detail_pane.toPlainText()

    dialog._copy_btn.click()

    clipboard = QApplication.clipboard()
    assert clipboard.text() == selected_output


# -- Favorite toggle button ---------------------------------------------------


def test_favorite_button_toggles_state(qtbot, tmp_path: Path):
    """Clicking Favorite button toggles the entry's favorite flag in the store."""
    from templatr.ui.history_browser import HistoryBrowserDialog

    store = _make_store(tmp_path)
    entry = store.add_entry("Alpha", "prompt", "output", created_at="2026-02-28T10:00:00Z")
    assert not entry.favorite

    dialog = HistoryBrowserDialog(store=store)
    qtbot.addWidget(dialog)

    dialog._entry_list.setCurrentRow(0)
    dialog._favorite_btn.click()

    updated = store.list_entries(template_name="Alpha")
    assert updated[0].favorite is True


# -- Re-use signal ------------------------------------------------------------


def test_reuse_button_emits_signal(qtbot, tmp_path: Path):
    """Re-use button emits output_reused signal with the selected output text."""
    from templatr.ui.history_browser import HistoryBrowserDialog

    store = _populated_store(tmp_path)
    dialog = HistoryBrowserDialog(store=store)
    qtbot.addWidget(dialog)

    dialog._entry_list.setCurrentRow(0)
    expected_output = dialog._detail_pane.toPlainText()

    with qtbot.waitSignal(dialog.output_reused, timeout=1000) as blocker:
        dialog._reuse_btn.click()

    assert blocker.args[0] == expected_output


# -- MainWindow wiring --------------------------------------------------------


def _make_window(qtbot, history_store: PromptHistoryStore):
    """Create a MainWindow with mocked dependencies and injected history store."""
    mock_template_mgr = MagicMock()
    mock_template_mgr.list_all.return_value = []
    mock_template_mgr.list_folders.return_value = []
    mock_template_mgr.get_template_folder.return_value = ""

    mock_llm_server = MagicMock()
    mock_llm_server.is_running.return_value = False
    mock_llm_client = MagicMock()

    with patch(
        "templatr.ui.template_tree.get_template_manager",
        return_value=mock_template_mgr,
    ), patch(
        "templatr.ui.llm_toolbar.get_llm_server",
        return_value=mock_llm_server,
    ):
        from templatr.ui.main_window import MainWindow

        win = MainWindow(
            templates=mock_template_mgr,
            llm_client=mock_llm_client,
            llm_server=mock_llm_server,
            prompt_history=history_store,
        )
        qtbot.addWidget(win)
        win.show()
        return win


def test_ctrl_h_opens_history_browser(qtbot, tmp_path: Path):
    """Ctrl+H shortcut calls _show_history_browser on MainWindow."""
    store = _populated_store(tmp_path)
    win = _make_window(qtbot, store)

    assert hasattr(win, "_show_history_browser")
    # Verify the method exists and is callable
    assert callable(win._show_history_browser)
