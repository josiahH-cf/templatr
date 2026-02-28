"""Tests for prompt history and favorites MVP behavior."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from templatr.core.prompt_history import PromptHistoryStore
from templatr.core.templates import Template


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


def test_store_lists_entries_per_template(tmp_path: Path):
    """Store returns history entries filtered by template name."""
    store = PromptHistoryStore(file_path=tmp_path / "prompt_history.json")

    store.add_entry("Alpha", "prompt one", "output one", created_at="2026-02-28T10:00:00Z")
    store.add_entry("Beta", "prompt two", "output two", created_at="2026-02-28T10:01:00Z")

    alpha_entries = store.list_entries(template_name="Alpha")

    assert len(alpha_entries) == 1
    assert alpha_entries[0].template_name == "Alpha"
    assert alpha_entries[0].output == "output one"


def test_store_marks_favorites_and_filters(tmp_path: Path):
    """Store can mark an entry favorite and list favorites-only results."""
    store = PromptHistoryStore(file_path=tmp_path / "prompt_history.json")

    first = store.add_entry("Alpha", "prompt one", "output one", created_at="2026-02-28T10:00:00Z")
    store.add_entry("Alpha", "prompt two", "output two", created_at="2026-02-28T10:01:00Z")

    assert store.mark_favorite(first.id, favorite=True)

    favorites = store.list_entries(favorites_only=True)

    assert len(favorites) == 1
    assert favorites[0].id == first.id
    assert favorites[0].favorite is True


def test_store_searches_by_content_and_date(tmp_path: Path):
    """Store search supports free-text query and YYYY-MM-DD date filters."""
    store = PromptHistoryStore(file_path=tmp_path / "prompt_history.json")

    store.add_entry(
        "Alpha",
        "fix login bug",
        "applied patch",
        created_at="2026-02-28T09:00:00Z",
    )
    store.add_entry(
        "Alpha",
        "write release notes",
        "release summary",
        created_at="2026-02-27T09:00:00Z",
    )

    text_matches = store.list_entries(template_name="Alpha", query="login")
    date_matches = store.list_entries(template_name="Alpha", date_prefix="2026-02-28")

    assert len(text_matches) == 1
    assert text_matches[0].prompt == "fix login bug"
    assert len(date_matches) == 1
    assert date_matches[0].created_at.startswith("2026-02-28")


def test_history_command_shows_filtered_entries(qtbot, tmp_path: Path):
    """/history command renders filtered history for the current template."""
    from templatr.ui.message_bubble import MessageBubble

    store = PromptHistoryStore(file_path=tmp_path / "prompt_history.json")
    store.add_entry("Alpha", "fix login bug", "output one", created_at="2026-02-28T09:00:00Z")
    store.add_entry("Alpha", "release notes", "output two", created_at="2026-02-28T09:01:00Z")

    win = _make_window(qtbot, store)
    win.current_template = Template(name="Alpha", content="ignored")

    assert win._handle_history_command("/history login")

    bubbles = win.chat_widget.findChildren(MessageBubble)
    assert bubbles
    assert "fix login bug" in bubbles[-1].get_raw_text()


def test_favorite_command_marks_last_output(qtbot, tmp_path: Path):
    """/favorite marks the most recent matching generated output as favorite."""
    store = PromptHistoryStore(file_path=tmp_path / "prompt_history.json")
    store.add_entry("Alpha", "fix login bug", "output one", created_at="2026-02-28T09:00:00Z")

    win = _make_window(qtbot, store)
    win.current_template = Template(name="Alpha", content="ignored")
    win._last_output = "output one"

    assert win._handle_history_command("/favorite")

    favorites = store.list_entries(template_name="Alpha", favorites_only=True)
    assert len(favorites) == 1
    assert favorites[0].output == "output one"
