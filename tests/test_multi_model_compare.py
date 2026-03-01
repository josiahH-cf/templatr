"""Tests for multi-model comparison slash command behavior."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from templatr.integrations.llm import ModelInfo


def _make_window(qtbot):
    """Create a MainWindow with mocked external dependencies."""
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
        )
        qtbot.addWidget(win)
        win.show()
        return win


def test_select_compare_models_defaults_to_first_two(qtbot):
    """Empty model query falls back to first two discovered models."""
    win = _make_window(qtbot)
    models = [
        ModelInfo(path=Path("/tmp/alpha.gguf"), name="alpha", size_gb=1.0),
        ModelInfo(path=Path("/tmp/beta.gguf"), name="beta", size_gb=1.0),
        ModelInfo(path=Path("/tmp/gamma.gguf"), name="gamma", size_gb=1.0),
    ]

    selected = win._select_compare_models("", models)

    assert not isinstance(selected, str)
    assert [m.name for m in selected] == ["alpha", "beta"]


def test_select_compare_models_reports_unknown_model(qtbot):
    """Unknown explicit model names return a user-facing error string."""
    win = _make_window(qtbot)
    models = [
        ModelInfo(path=Path("/tmp/alpha.gguf"), name="alpha", size_gb=1.0),
        ModelInfo(path=Path("/tmp/beta.gguf"), name="beta", size_gb=1.0),
    ]

    selected = win._select_compare_models("alpha,missing", models)

    assert isinstance(selected, str)
    assert "Unknown model(s): missing" in selected


def test_compare_command_requires_prompt(qtbot):
    """/compare returns handled=True and shows guidance when no prompt is available."""
    from templatr.ui.message_bubble import MessageBubble

    win = _make_window(qtbot)
    win._last_prompt = None

    assert win._handle_compare_command("/compare")

    bubbles = win.chat_widget.findChildren(MessageBubble)
    assert bubbles
    assert "No prompt available" in bubbles[-1].get_raw_text()


def test_compare_command_dispatches_worker(qtbot):
    """/compare with explicit models and inline prompt starts compare worker."""
    win = _make_window(qtbot)

    models = [
        ModelInfo(path=Path("/tmp/alpha.gguf"), name="alpha", size_gb=1.0),
        ModelInfo(path=Path("/tmp/beta.gguf"), name="beta", size_gb=1.0),
    ]

    captured = {}

    class _Signal:
        def connect(self, _fn):
            return None

    class FakeCompareWorker:
        def __init__(self, prompt, model_paths):
            captured["prompt"] = prompt
            captured["model_paths"] = model_paths
            self.progress = _Signal()
            self.error = _Signal()
            self.finished = _Signal()

        def isRunning(self):  # noqa: N802
            return False

        def start(self):
            captured["started"] = True

    server_mock = MagicMock()
    server_mock.find_models.return_value = models

    with patch("templatr.ui.main_window.get_llm_server", return_value=server_mock), patch(
        "templatr.ui.main_window.MultiModelCompareWorker", FakeCompareWorker
    ):
        handled = win._handle_compare_command("/compare alpha,beta | compare this prompt")

    assert handled is True
    assert captured.get("started") is True
    assert captured["prompt"] == "compare this prompt"
    assert captured["model_paths"] == [Path("/tmp/alpha.gguf"), Path("/tmp/beta.gguf")]
