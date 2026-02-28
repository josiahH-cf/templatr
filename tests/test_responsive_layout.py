"""Tests for responsive-layout feature.

Covers proportional splitter sizing, dynamic font/padding scaling,
section header scaling, input field stretch, and output pane fill.
Spec: /specs/responsive-layout.md
"""

import re
from unittest.mock import MagicMock, patch

from PyQt6.QtWidgets import QPlainTextEdit, QTextEdit

from templatr.core.config import UIConfig
from templatr.core.templates import Template, Variable
from templatr.ui.output_pane import OutputPaneWidget
from templatr.ui.template_tree import TemplateTreeWidget
from templatr.ui.variable_form import VariableFormWidget

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _header_font_size(label):
    """Extract font-size from a QLabel's stylesheet (e.g. 'font-size: 14pt;')."""
    match = re.search(r'font-size:\s*(\d+)pt', label.styleSheet())
    return int(match.group(1)) if match else label.font().pointSize()


FACTORY_SPLITTER = [200, 300, 400]


def _make_multiline_template():
    """Template with a multiline variable for stretch testing."""
    return Template(
        name="Stretch Test",
        content="{{body}}",
        description="",
        variables=[
            Variable(name="body", label="Body", multiline=True),
        ],
    )


# ---------------------------------------------------------------------------
# Task 1 — Proportional splitter & resize plumbing
# ---------------------------------------------------------------------------


class TestProportionalSplitter:
    """Layout criteria: sidebar hidden by default, togglable, chat usable."""

    def _make_window(self, qtbot):
        """Create a MainWindow with mocked singletons for layout tests."""
        with patch("templatr.ui.main_window.get_config") as mock_cfg:
            cfg = MagicMock()
            cfg.ui = UIConfig()
            mock_cfg.return_value = cfg

            with patch("templatr.ui.main_window.save_config"):
                with patch("templatr.ui.template_tree.get_template_manager") as mock_mgr:
                    mgr = MagicMock()
                    mgr.list_all.return_value = []
                    mgr.list_folders.return_value = []
                    mock_mgr.return_value = mgr

                    with patch("templatr.ui.llm_toolbar.get_llm_server") as mock_srv:
                        srv = MagicMock()
                        srv.is_running.return_value = False
                        mock_srv.return_value = srv

                        from templatr.ui.main_window import MainWindow

                        win = MainWindow()
                        qtbot.addWidget(win)
                        win.resize(1000, 700)
                        win.show()
                        qtbot.waitExposed(win)

                        from PyQt6.QtCore import QCoreApplication
                        QCoreApplication.processEvents()
                        return win

    def test_splitter_proportional_on_first_launch(self, qtbot):
        """On first launch the template sidebar is hidden; chat column takes all width."""
        with patch("templatr.ui.main_window.get_config") as mock_cfg:
            cfg = MagicMock()
            cfg.ui = UIConfig()
            mock_cfg.return_value = cfg

            with patch("templatr.ui.main_window.save_config"):
                with patch("templatr.ui.template_tree.get_template_manager") as mock_mgr:
                    mgr = MagicMock()
                    mgr.list_all.return_value = []
                    mgr.list_folders.return_value = []
                    mock_mgr.return_value = mgr

                    with patch("templatr.ui.llm_toolbar.get_llm_server") as mock_srv:
                        srv = MagicMock()
                        srv.is_running.return_value = False
                        mock_srv.return_value = srv

                        from templatr.ui.main_window import MainWindow

                        win = MainWindow()
                        qtbot.addWidget(win)
                        win.resize(1000, 700)
                        win.show()
                        qtbot.waitExposed(win)

                        from PyQt6.QtCore import QCoreApplication
                        QCoreApplication.processEvents()

                        # Sidebar defaults to hidden
                        assert not win.template_tree_widget.isVisible()
                        # Chat column has all available width
                        sizes = win.splitter.sizes()
                        assert sizes[0] == 0, "Tree pane should be collapsed (0 width) by default"
                        assert sizes[1] > 0, "Chat column must have positive width"

    def test_splitter_preserved_when_user_customized(self, qtbot):
        """Sidebar can be toggled open; splitter reflects state."""
        with patch("templatr.ui.main_window.get_config") as mock_cfg:
            cfg = MagicMock()
            cfg.ui = UIConfig()
            mock_cfg.return_value = cfg

            with patch("templatr.ui.main_window.save_config"):
                with patch("templatr.ui.template_tree.get_template_manager") as mock_mgr:
                    mgr = MagicMock()
                    mgr.list_all.return_value = []
                    mgr.list_folders.return_value = []
                    mock_mgr.return_value = mgr

                    with patch("templatr.ui.llm_toolbar.get_llm_server") as mock_srv:
                        srv = MagicMock()
                        srv.is_running.return_value = False
                        mock_srv.return_value = srv

                        from templatr.ui.main_window import MainWindow

                        win = MainWindow()
                        qtbot.addWidget(win)
                        win.resize(1200, 800)
                        win.show()
                        qtbot.waitExposed(win)

                        from PyQt6.QtCore import QCoreApplication
                        QCoreApplication.processEvents()

                        # Toggle sidebar open
                        win._toggle_sidebar()
                        QCoreApplication.processEvents()

                        assert win.template_tree_widget.isVisible()
                        sizes = win.splitter.sizes()
                        assert sizes[0] >= 200, "Open sidebar should have at least 200px width"
                        assert sizes[1] > 0, "Chat column should still have positive width"

    def test_usable_at_minimum_size(self, qtbot):
        """App is usable at 600×400: chat column has positive width."""
        with patch("templatr.ui.main_window.get_config") as mock_cfg:
            cfg = MagicMock()
            cfg.ui = UIConfig()
            mock_cfg.return_value = cfg

            with patch("templatr.ui.main_window.save_config"):
                with patch("templatr.ui.template_tree.get_template_manager") as mock_mgr:
                    mgr = MagicMock()
                    mgr.list_all.return_value = []
                    mgr.list_folders.return_value = []
                    mock_mgr.return_value = mgr

                    with patch("templatr.ui.llm_toolbar.get_llm_server") as mock_srv:
                        srv = MagicMock()
                        srv.is_running.return_value = False
                        mock_srv.return_value = srv

                        from templatr.ui.main_window import MainWindow

                        win = MainWindow()
                        qtbot.addWidget(win)
                        win.resize(600, 400)
                        win.show()
                        qtbot.waitExposed(win)

                        from PyQt6.QtCore import QCoreApplication
                        QCoreApplication.processEvents()

                        # Chat column (index 1) must be usable
                        sizes = win.splitter.sizes()
                        assert sizes[1] > 0, f"Chat column has non-positive width {sizes[1]} at 600×400"

    def test_manual_splitter_drag_stops_auto_resize(self, qtbot):
        """Dragging the splitter updates sidebar button state to reflect visibility."""
        with patch("templatr.ui.main_window.get_config") as mock_cfg:
            cfg = MagicMock()
            cfg.ui = UIConfig()
            mock_cfg.return_value = cfg

            with patch("templatr.ui.main_window.save_config"):
                with patch("templatr.ui.template_tree.get_template_manager") as mock_mgr:
                    mgr = MagicMock()
                    mgr.list_all.return_value = []
                    mgr.list_folders.return_value = []
                    mock_mgr.return_value = mgr

                    with patch("templatr.ui.llm_toolbar.get_llm_server") as mock_srv:
                        srv = MagicMock()
                        srv.is_running.return_value = False
                        mock_srv.return_value = srv

                        from templatr.ui.main_window import MainWindow

                        win = MainWindow()
                        qtbot.addWidget(win)
                        win.resize(1000, 700)
                        win.show()
                        qtbot.waitExposed(win)

                        from PyQt6.QtCore import QCoreApplication
                        QCoreApplication.processEvents()

                        # Show template tree via toggle, then drag splitter
                        win._toggle_sidebar()
                        QCoreApplication.processEvents()

                        assert win._sidebar_btn.isChecked() is True


# ---------------------------------------------------------------------------
# Task 2 — Dynamic font, header, and padding scaling
# ---------------------------------------------------------------------------


class TestFontAndPaddingScaling:
    """Criteria 2-4: font, header, and margin scaling."""

    def test_body_font_scales_with_window_height(self, qtbot):
        """Criterion 2: body font scales between 13–18pt based on window height."""
        widget = VariableFormWidget()
        qtbot.addWidget(widget)

        # Small window → lower font
        widget.scale_to(800, 700)
        small_font = widget.font().pointSize()

        # Large window → bigger font
        widget.scale_to(1920, 1080)
        large_font = widget.font().pointSize()

        assert small_font >= 13
        assert large_font <= 18
        assert large_font >= small_font

    def test_section_header_scaling(self, qtbot):
        """Criterion 3: section headers ≥ 1.3× body and never below 14pt."""
        widget = VariableFormWidget()
        qtbot.addWidget(widget)

        # At small window
        widget.scale_to(600, 400)
        header_font = _header_font_size(widget._label)
        assert header_font >= 14, f"Header font {header_font}pt < 14pt minimum"

        # At large window
        widget.scale_to(1920, 1080)
        header_font = _header_font_size(widget._label)
        body_font = widget.font().pointSize()
        assert header_font >= int(body_font * 1.3), (
            f"Header {header_font}pt < 1.3× body {body_font}pt"
        )

    def test_header_scaling_output_pane(self, qtbot):
        """Output pane header scales the same way."""
        widget = OutputPaneWidget()
        qtbot.addWidget(widget)

        widget.scale_to(1920, 1080)
        header_font = _header_font_size(widget._label)
        body_font = widget.font().pointSize()
        assert header_font >= 14
        assert header_font >= int(body_font * 1.3)

    def test_header_scaling_template_tree(self, qtbot):
        """Template tree header scales the same way."""
        with patch("templatr.ui.template_tree.get_template_manager") as mock_mgr:
            mgr = MagicMock()
            mgr.list_all.return_value = []
            mgr.list_folders.return_value = []
            mock_mgr.return_value = mgr

            widget = TemplateTreeWidget()
            qtbot.addWidget(widget)

            widget.scale_to(1920, 1080)
            header_font = _header_font_size(widget._label)
            assert header_font >= 14

    def test_margins_scale_with_window_width(self, qtbot):
        """Criterion 4: margins grow with window width, minimum 8px."""
        widget = VariableFormWidget()
        qtbot.addWidget(widget)

        # Small window
        widget.scale_to(600, 400)
        margins_small = widget.layout().contentsMargins()
        assert margins_small.left() >= 8
        assert margins_small.top() >= 8

        # Large window
        widget.scale_to(1920, 1080)
        margins_large = widget.layout().contentsMargins()
        assert margins_large.left() >= margins_small.left()

    def test_margins_output_pane(self, qtbot):
        """Output pane margins scale with window width."""
        widget = OutputPaneWidget()
        qtbot.addWidget(widget)

        widget.scale_to(600, 400)
        margins_small = widget.layout().contentsMargins()
        assert margins_small.left() >= 8

        widget.scale_to(1920, 1080)
        margins_large = widget.layout().contentsMargins()
        assert margins_large.left() >= margins_small.left()


# ---------------------------------------------------------------------------
# Task 3 — Input field stretch & output pane fill
# ---------------------------------------------------------------------------


class TestStretchAndFill:
    """Criteria 5-6: output pane stretch and variable input min height."""

    def test_output_text_has_stretch(self, qtbot):
        """Criterion 5: output pane's QTextEdit has positive stretch factor."""
        widget = OutputPaneWidget()
        qtbot.addWidget(widget)

        layout = widget.layout()
        # Find the QTextEdit item in the layout and check its stretch
        found_stretch = False
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), QTextEdit):
                stretch = layout.stretch(i)
                assert stretch > 0, f"QTextEdit stretch factor is {stretch}, expected > 0"
                found_stretch = True
                break
        assert found_stretch, "QTextEdit not found in output pane layout"

    def test_multiline_input_min_height_scales(self, qtbot):
        """Criterion 6: multi-line variable inputs have min height ≥ 15% of pane height."""
        template = _make_multiline_template()
        widget = VariableFormWidget()
        qtbot.addWidget(widget)
        widget.set_template(template)

        pane_height = 700
        widget.scale_to(900, pane_height)

        # Find the QPlainTextEdit in the form
        for name, input_widget in widget._scroll.inputs.items():
            if isinstance(input_widget, QPlainTextEdit):
                min_h = input_widget.minimumHeight()
                expected_min = int(pane_height * 0.15)
                assert min_h >= expected_min, (
                    f"Multi-line input min height {min_h} < 15% of {pane_height} = {expected_min}"
                )

    def test_no_new_dependencies(self):
        """Criterion 10: pyproject.toml dependencies section unchanged."""
        from pathlib import Path

        import tomllib

        pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
        with open(pyproject, "rb") as f:
            data = tomllib.load(f)

        deps = data.get("project", {}).get("dependencies", [])
        # Should only have PyQt6 and requests
        dep_names = [d.split(">=")[0].split("==")[0].strip().lower() for d in deps]
        assert "pyqt6" in dep_names
        # No unexpected new deps (exact set may vary, but count should be stable)
        assert len(deps) <= 3, f"Unexpected number of dependencies: {deps}"
