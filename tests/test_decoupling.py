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
