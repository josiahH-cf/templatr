"""Tests for incremental decoupling: circular import fix and singleton reset.

Verifies:
- No circular import between feedback and templates modules
- No deferred imports between feedback.py and templates.py
- Singleton reset() functions clear cached instances
"""

import inspect
import sys

import pytest


class TestCircularImportEliminated:
    """Verify the circular import between feedback and templates is gone."""

    def test_import_feedback_then_templates(self):
        """Import feedback and templates in sequence — no ImportError."""
        # Save and restore sys.modules so other tests' pre-imported references
        # (e.g. FeedbackManager.__globals__) stay valid.
        saved = {k: v for k, v in sys.modules.items() if k.startswith("templatr.core")}
        for k in saved:
            del sys.modules[k]
        try:
            from templatr.core import feedback  # noqa: F401, I001
            from templatr.core import templates  # noqa: F401, I001
        finally:
            # Remove the freshly-imported modules and restore originals
            for k in list(sys.modules):
                if k.startswith("templatr.core"):
                    del sys.modules[k]
            sys.modules.update(saved)

    def test_import_templates_then_feedback(self):
        """Import templates then feedback in sequence — no ImportError."""
        saved = {k: v for k, v in sys.modules.items() if k.startswith("templatr.core")}
        for k in saved:
            del sys.modules[k]
        try:
            from templatr.core import templates  # noqa: F401, I001
            from templatr.core import feedback  # noqa: F401, I001
        finally:
            for k in list(sys.modules):
                if k.startswith("templatr.core"):
                    del sys.modules[k]
            sys.modules.update(saved)

    def test_no_deferred_imports_in_feedback(self):
        """feedback.py should not have function-level imports from templates."""
        from templatr.core import feedback

        source = inspect.getsource(feedback)
        # Should not contain deferred imports of templates inside functions
        lines = source.split("\n")
        in_function = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("def ") or stripped.startswith("class "):
                in_function = stripped.startswith("def ")
                continue
            if in_function and "from templatr.core.templates import" in stripped:
                pytest.fail(
                    f"Found deferred import in feedback.py: {stripped}"
                )

    def test_load_meta_template_in_meta_templates_module(self):
        """load_meta_template should live in meta_templates module."""
        from templatr.core.meta_templates import load_meta_template

        assert callable(load_meta_template)


class TestSingletonReset:
    """Verify each singleton module has a working reset() function."""

    def test_config_manager_reset(self, tmp_config_dir):
        from templatr.core import config

        first = config.get_config_manager()
        config.reset()
        second = config.get_config_manager()
        assert first is not second

    def test_template_manager_reset(self, tmp_templates_dir):
        from templatr.core import templates

        first = templates.get_template_manager()
        templates.reset()
        second = templates.get_template_manager()
        assert first is not second

    def test_feedback_manager_reset(self, tmp_config_dir):
        from templatr.core import feedback

        first = feedback.get_feedback_manager()
        feedback.reset()
        second = feedback.get_feedback_manager()
        assert first is not second

    def test_llm_client_reset(self):
        from templatr.integrations import llm

        first = llm.get_llm_client()
        llm.reset_llm_client()
        second = llm.get_llm_client()
        assert first is not second

    def test_llm_server_reset(self):
        from templatr.integrations import llm

        first = llm.get_llm_server()
        llm.reset_llm_server()
        second = llm.get_llm_server()
        assert first is not second


class TestConstructorInjection:
    """Verify MainWindow accepts optional dependency parameters."""

    def test_mainwindow_init_accepts_optional_deps(self):
        """MainWindow.__init__ signature accepts config, templates, llm_client, llm_server."""
        import inspect

        from templatr.ui.main_window import MainWindow

        sig = inspect.signature(MainWindow.__init__)
        params = list(sig.parameters.keys())
        assert "config" in params
        assert "templates" in params
        assert "llm_client" in params
        assert "llm_server" in params

    def test_mainwindow_stores_injected_deps(self, qtbot):
        """MainWindow stores injected dependencies as instance attributes."""
        from unittest.mock import MagicMock

        from templatr.ui.main_window import MainWindow

        mock_config = MagicMock()
        mock_config.config.ui.window_width = 900
        mock_config.config.ui.window_height = 700
        mock_config.config.ui.theme = "dark"
        mock_config.config.ui.font_size = 13
        mock_config.config.ui.splitter_sizes = [200, 300, 400]
        mock_config.config.ui.window_geometry = ""
        mock_config.config.ui.window_maximized = False
        mock_config.config.ui.last_template = ""
        mock_config.config.ui.expanded_folders = []

        mock_templates = MagicMock()
        mock_templates.list_all.return_value = []
        mock_templates.list_folders.return_value = []

        mock_client = MagicMock()
        mock_server = MagicMock()
        mock_server.is_running.return_value = False

        window = MainWindow(
            config=mock_config,
            templates=mock_templates,
            llm_client=mock_client,
            llm_server=mock_server,
        )
        qtbot.addWidget(window)

        assert window.config_manager is mock_config
        assert window.template_manager is mock_templates
        assert window.llm_client is mock_client
        assert window.llm_server is mock_server


class TestMixinDocstrings:
    """Verify each mixin class has a docstring listing expected self attributes."""

    def test_template_actions_mixin_docstring(self):
        from templatr.ui._template_actions import TemplateActionsMixin

        doc = TemplateActionsMixin.__doc__
        assert doc is not None
        assert "Expects self to provide" in doc
        for attr in ["current_template", "variable_form", "template_tree_widget",
                      "status_bar", "llm_toolbar"]:
            assert attr in doc, f"Missing {attr} in TemplateActionsMixin docstring"

    def test_generation_mixin_docstring(self):
        from templatr.ui._generation import GenerationMixin

        doc = GenerationMixin.__doc__
        assert doc is not None
        assert "Expects self to provide" in doc
        for attr in ["current_template", "variable_form", "output_pane",
                      "status_bar", "llm_toolbar", "worker",
                      "_last_prompt", "_last_output"]:
            assert attr in doc, f"Missing {attr} in GenerationMixin docstring"

    def test_window_state_mixin_docstring(self):
        from templatr.ui._window_state import WindowStateMixin

        doc = WindowStateMixin.__doc__
        assert doc is not None
        assert "Expects self to provide" in doc
        for attr in ["current_template", "template_tree",
                      "template_tree_widget", "splitter"]:
            assert attr in doc, f"Missing {attr} in WindowStateMixin docstring"
