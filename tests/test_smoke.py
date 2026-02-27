"""Smoke tests verifying the app can launch and key modules import correctly.

These tests validate the minimum viability of the installed package:
- CLI entry point resolves and returns a version string
- MainWindow can be instantiated without errors
- Core modules import and initialize
"""

from unittest.mock import patch

from templatr import __version__
from templatr.core.config import get_config
from templatr.core.templates import TemplateManager
from templatr.ui.main_window import MainWindow


def test_version_is_set():
    """Package exposes a non-empty version string."""
    assert __version__
    assert isinstance(__version__, str)


def test_config_loads():
    """Config module loads without error and returns a valid object."""
    config = get_config()
    assert config.llm.server_port > 0
    assert config.ui.theme in ("dark", "light")


def test_template_manager_lists_templates(tmp_templates_dir):
    """TemplateManager can list templates from a directory."""
    manager = TemplateManager(tmp_templates_dir)
    templates = manager.list_all()
    assert len(templates) >= 1


def test_main_window_creates(qtbot):
    """MainWindow can be instantiated and shows expected widgets."""
    with patch("templatr.ui.template_tree.get_template_manager") as mock_mgr:
        from unittest.mock import MagicMock

        manager = MagicMock()
        manager.list_all.return_value = []
        manager.list_folders.return_value = []
        mock_mgr.return_value = manager

        window = MainWindow()
        qtbot.addWidget(window)

        assert window.windowTitle().startswith("Templatr")
        assert window.template_tree_widget is not None
        assert window.variable_form is not None
        assert window.output_pane is not None
        assert window.llm_toolbar is not None
