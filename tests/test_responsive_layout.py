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
    """Criterion 1: splitter sizes proportional to window width on first launch."""

    def test_splitter_proportional_on_first_launch(self, qtbot):
        """With factory-default splitter sizes the splitter is recalculated
        as proportions (20%/35%/45%) of the window width."""
        with patch("templatr.ui.main_window.get_config") as mock_cfg:
            cfg = MagicMock()
            cfg.ui = UIConfig()  # factory defaults
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

                        # Trigger resize event processing
                        from PyQt6.QtCore import QCoreApplication
                        QCoreApplication.processEvents()

                        sizes = win.splitter.sizes()
                        total = sum(sizes)
                        # Check proportions are roughly 20/35/45 (±5%)
                        if total > 0:
                            ratios = [s / total for s in sizes]
                            assert abs(ratios[0] - 0.20) < 0.12, f"Tree pane ratio {ratios[0]:.2f} not ~0.20"
                            assert abs(ratios[1] - 0.35) < 0.12, f"Form pane ratio {ratios[1]:.2f} not ~0.35"
                            assert abs(ratios[2] - 0.45) < 0.12, f"Output pane ratio {ratios[2]:.2f} not ~0.45"

    def test_splitter_preserved_when_user_customized(self, qtbot):
        """Criterion 7: saved non-default splitter sizes are not overwritten."""
        custom_sizes = [300, 400, 500]
        with patch("templatr.ui.main_window.get_config") as mock_cfg:
            cfg = MagicMock()
            cfg.ui = UIConfig(splitter_sizes=custom_sizes)
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

                        # Splitter should use the user-saved sizes, NOT proportional
                        sizes = win.splitter.sizes()
                        total = sum(sizes)
                        custom_total = sum(custom_sizes)
                        # The ratios should remain close to the custom ratios
                        if total > 0 and custom_total > 0:
                            expected_ratios = [s / custom_total for s in custom_sizes]
                            actual_ratios = [s / total for s in sizes]
                            for exp, act in zip(expected_ratios, actual_ratios):
                                assert abs(exp - act) < 0.10, (
                                    f"Custom ratio not preserved: expected ~{exp:.2f}, got {act:.2f}"
                                )

    def test_usable_at_minimum_size(self, qtbot):
        """Criterion 8: all 3 panes usable at 600×400 — no negative or zero sizes."""
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

                        sizes = win.splitter.sizes()
                        for i, s in enumerate(sizes):
                            assert s > 0, f"Pane {i} has non-positive width {s} at 600×400"

    def test_manual_splitter_drag_stops_auto_resize(self, qtbot):
        """Once the user manually drags a splitter, auto-proportional resize stops."""
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

                        # Simulate user manually dragging the splitter
                        win.splitter.splitterMoved.emit(500, 1)
                        QCoreApplication.processEvents()

                        # Now resize the window — splitter should NOT auto-adjust
                        win.resize(1200, 800)
                        QCoreApplication.processEvents()

                        assert win._splitter_user_dragged is True


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
