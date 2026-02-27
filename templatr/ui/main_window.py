"""Main window for Automatr GUI."""

import sys
from typing import Optional

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import (
    QAction,
    QDesktopServices,
    QFont,
    QKeySequence,
    QResizeEvent,
    QShortcut,
    QWheelEvent,
)
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStatusBar,
    QWidget,
)

from templatr import __version__
from templatr.core.config import get_config, get_config_manager, save_config
from templatr.core.templates import Template, get_template_manager
from templatr.integrations.llm import get_llm_client, get_llm_server
from templatr.ui._generation import GenerationMixin
from templatr.ui._template_actions import TemplateActionsMixin
from templatr.ui._window_state import WindowStateMixin
from templatr.ui.llm_settings import LLMSettingsDialog
from templatr.ui.llm_toolbar import LLMToolbar
from templatr.ui.output_pane import OutputPaneWidget
from templatr.ui.template_tree import TemplateTreeWidget
from templatr.ui.theme import get_theme_stylesheet
from templatr.ui.variable_form import VariableFormWidget
from templatr.ui.workers import GenerationWorker


class MainWindow(TemplateActionsMixin, GenerationMixin, WindowStateMixin, QMainWindow):
    """Main application window."""

    def __init__(self, config=None, templates=None, llm_client=None, llm_server=None):
        """Initialize the main window.

        Args:
            config: ConfigManager instance. Uses the global singleton if None.
            templates: TemplateManager instance. Uses the global singleton if None.
            llm_client: LLMClient instance. Uses the global singleton if None.
            llm_server: LLMServerManager instance. Uses the global singleton if None.
        """
        super().__init__()

        # Store injected dependencies (fall back to global singletons)
        self.config_manager = config or get_config_manager()
        self.template_manager = templates or get_template_manager()
        self.llm_client = llm_client or get_llm_client()
        self.llm_server = llm_server or get_llm_server()
        self.setWindowTitle(f"Automatr v{__version__}")
        self.setMinimumSize(600, 400)  # Allow proper window snapping on all screen sizes

        cfg = self.config_manager.config
        self.resize(cfg.ui.window_width, cfg.ui.window_height)

        self.current_template: Optional[Template] = None
        self.worker: Optional[GenerationWorker] = None

        # Responsive layout: track whether user manually dragged the splitter
        self._splitter_user_dragged = False
        # Factory default splitter sizes for auto-proportion detection
        self._factory_splitter = [200, 300, 400]
        # Proportional ratios for auto-sizing (20% / 35% / 45%)
        self._splitter_ratios = [0.20, 0.35, 0.45]

        # Feedback tracking - stores last AI generation for feedback
        self._last_prompt: Optional[str] = None
        self._last_output: Optional[str] = None

        self._setup_menu_bar()
        self._setup_ui()
        self._setup_status_bar()
        self._setup_shortcuts()
        self._wire_tree_signals()
        self.template_tree_widget.load_templates()
        self._restore_state()
        self.llm_toolbar.check_status()

        # Apply initial proportional splitter if factory default
        self._apply_proportional_splitter()
        # Apply initial scaling to child widgets
        self._apply_scaling()

    # ------------------------------------------------------------------
    # Responsive layout helpers
    # ------------------------------------------------------------------

    def _is_factory_splitter(self) -> bool:
        """Check if current splitter sizes match the factory default."""
        config = get_config()
        return config.ui.splitter_sizes == self._factory_splitter

    def _apply_proportional_splitter(self):
        """Recalculate splitter sizes as proportions of the window width.

        Only applies when the splitter has factory-default sizes and the
        user has not manually dragged the splitter handle.
        """
        if self._splitter_user_dragged:
            return
        if not self._is_factory_splitter():
            return
        width = self.splitter.width()
        if width <= 0:
            return
        sizes = [max(1, int(width * r)) for r in self._splitter_ratios]
        self.splitter.setSizes(sizes)

    def _on_splitter_moved(self, pos: int, index: int):
        """Mark the splitter as user-dragged to stop auto-resizing."""
        self._splitter_user_dragged = True

    @staticmethod
    def _compute_base_font(height: int) -> int:
        """Compute base font size from window height (13–18pt)."""
        return max(13, min(18, height // 50))

    @staticmethod
    def _compute_padding(width: int) -> int:
        """Compute scaled padding from window width (min 8px)."""
        return max(8, width // 120)

    def _apply_scaling(self):
        """Push scaled font, header, and padding values to child widgets."""
        w = self.width()
        h = self.height()
        for child in (
            self.template_tree_widget,
            self.variable_form,
            self.output_pane,
        ):
            child.scale_to(w, h)

    def resizeEvent(self, event: QResizeEvent):  # noqa: N802
        """Handle window resize: update splitter proportions and scaling."""
        super().resizeEvent(event)
        self._apply_proportional_splitter()
        self._apply_scaling()

    def _on_server_running_changed(self, is_running: bool):
        """Update menu actions when server status changes."""
        self.start_server_action.setEnabled(not is_running)
        self.stop_server_action.setEnabled(is_running)

    def _wire_tree_signals(self):
        """Connect TemplateTreeWidget signals to MainWindow slots."""
        tree = self.template_tree_widget
        tree.template_selected.connect(self._on_template_selected)
        tree.folder_selected.connect(self._on_folder_selected)
        tree.edit_requested.connect(lambda t: self._edit_template(t))
        tree.improve_requested.connect(lambda t: self._improve_template(t))
        tree.version_history_requested.connect(
            lambda t: self._show_version_history(t)
        )
        tree.new_template_requested.connect(self._new_template)
        tree.template_deleted.connect(self._on_template_deleted)
        tree.status_message.connect(
            lambda msg, ms: self.status_bar.showMessage(msg, ms)
        )

    def _on_template_selected(self, template: Template):
        """Handle template selection from tree widget."""
        self.current_template = template
        self.variable_form.set_template(template)
        self.variable_form.set_buttons_enabled(True)

    def _on_folder_selected(self):
        """Handle folder selection (deselect template)."""
        self.current_template = None
        self.variable_form.clear()
        self.variable_form.set_buttons_enabled(False)

    def _on_template_deleted(self, name: str):
        """Handle template deletion from tree widget."""
        self.current_template = None
        self.variable_form.clear()
        self.variable_form.set_buttons_enabled(False)

    def _setup_menu_bar(self):
        """Set up the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")
        new_action = QAction("&New Template", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self._new_template)
        file_menu.addAction(new_action)
        file_menu.addSeparator()
        quit_action = QAction("&Quit", self)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        ai_menu = file_menu.addMenu("AI &Instructions")
        gen_instr = QAction("Edit &Generate Template Instructions...", self)
        gen_instr.triggered.connect(self._edit_generate_instructions)
        ai_menu.addAction(gen_instr)
        imp_instr = QAction("Edit &Improve Template Instructions...", self)
        imp_instr.triggered.connect(self._edit_improve_instructions)
        ai_menu.addAction(imp_instr)
        file_menu.addSeparator()

        # LLM menu
        llm_menu = menubar.addMenu("&LLM")
        self.start_server_action = QAction("&Start Server", self)
        llm_menu.addAction(self.start_server_action)
        self.stop_server_action = QAction("S&top Server", self)
        llm_menu.addAction(self.stop_server_action)
        llm_menu.addSeparator()
        self.model_menu = llm_menu.addMenu("Select &Model")
        download_action = QAction("&Download Models (Hugging Face)...", self)
        llm_menu.addAction(download_action)
        llm_menu.addSeparator()
        refresh_action = QAction("&Check Status", self)
        llm_menu.addAction(refresh_action)
        llm_menu.addSeparator()
        settings_action = QAction("S&ettings...", self)
        settings_action.triggered.connect(self._show_llm_settings)
        llm_menu.addAction(settings_action)
        self._llm_menu_actions = {
            "start": self.start_server_action,
            "stop": self.stop_server_action,
            "download": download_action,
            "refresh": refresh_action,
        }

        # Help menu
        help_menu = menubar.addMenu("&Help")
        view_log_action = QAction("View &Log File", self)
        view_log_action.triggered.connect(self._view_log_file)
        help_menu.addAction(view_log_action)
        help_menu.addSeparator()
        about_action = QAction("&About Automatr", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_shortcuts(self):
        """Set up additional keyboard shortcuts."""
        QShortcut(QKeySequence("Ctrl++"), self).activated.connect(self._increase_font)
        QShortcut(QKeySequence("Ctrl+="), self).activated.connect(self._increase_font)
        QShortcut(QKeySequence("Ctrl+-"), self).activated.connect(self._decrease_font)
        QShortcut(QKeySequence("Ctrl+0"), self).activated.connect(self._reset_font)

    def wheelEvent(self, event: QWheelEvent):  # noqa: N802
        """Handle mouse wheel events for font scaling with Ctrl."""
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self._increase_font()
            elif delta < 0:
                self._decrease_font()
            event.accept()
        else:
            super().wheelEvent(event)

    def _apply_font_size(self, size: int):
        """Apply a new font size to the application."""
        size = max(8, min(24, size))
        config = get_config()
        config.ui.font_size = size
        save_config(config)
        stylesheet = get_theme_stylesheet(config.ui.theme, size)
        app = QApplication.instance()
        if app:
            app.setStyleSheet(stylesheet)
            app.setFont(QFont(app.font().family(), size))
        label_style = f"font-weight: bold; font-size: {size + 1}pt;"
        for label in self.findChildren(QLabel):
            if label.text() in ("Templates", "Variables", "Output"):
                label.setStyleSheet(label_style)
        self.status_bar.showMessage(f"Font size: {size}pt", 2000)

    def _increase_font(self):
        """Increase font size by 1pt."""
        self._apply_font_size(get_config().ui.font_size + 1)

    def _decrease_font(self):
        """Decrease font size by 1pt."""
        self._apply_font_size(get_config().ui.font_size - 1)

    def _reset_font(self):
        """Reset font size to default (13pt)."""
        self._apply_font_size(13)

    def _show_about(self):
        """Show the about dialog."""
        QMessageBox.about(
            self, "About Templatr",
            f"<h2>Templatr v{__version__}</h2>"
            "<p>Local prompt optimizer with reusable templates.</p>"
            "<p><b>Features:</b></p><ul>"
            "<li>Template-driven prompts</li>"
            "<li>Local llama.cpp integration</li></ul>"
            "<p><a href='https://github.com/josiahH-cf/templatr'>GitHub</a></p>",
        )

    def _setup_ui(self):
        """Set up the main UI."""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        self.template_tree_widget = TemplateTreeWidget()
        self.template_tree = self.template_tree_widget.tree  # alias for state save/restore
        self.splitter.addWidget(self.template_tree_widget)

        self.variable_form = VariableFormWidget()
        self.variable_form.generate_requested.connect(self._generate)
        self.variable_form.render_template_requested.connect(self._render_template_only)
        self.splitter.addWidget(self.variable_form)

        self.output_pane = OutputPaneWidget()
        self.output_pane.stop_requested.connect(self._stop_generation)
        self.output_pane.retry_requested.connect(self._retry_generation)
        self.output_pane.status_message.connect(
            lambda msg, ms: self.status_bar.showMessage(msg, ms)
        )
        self.splitter.addWidget(self.output_pane)

        config = get_config()
        self.splitter.setSizes(config.ui.splitter_sizes)
        self.splitter.splitterMoved.connect(self._on_splitter_moved)
        main_layout.addWidget(self.splitter)

    def _setup_status_bar(self):
        """Set up the status bar with the LLM toolbar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.llm_toolbar = LLMToolbar()
        self.llm_toolbar.status_message.connect(
            lambda msg, ms: self.status_bar.showMessage(msg, ms)
        )
        self.llm_toolbar.server_running_changed.connect(
            self._on_server_running_changed
        )
        self.status_bar.addWidget(self.llm_toolbar)
        self.llm_toolbar.set_model_menu(self.model_menu)

        # Wire deferred menu actions to toolbar
        actions = self._llm_menu_actions
        actions["start"].triggered.connect(self.llm_toolbar.start_server)
        actions["stop"].triggered.connect(self.llm_toolbar.stop_server)
        actions["download"].triggered.connect(
            self.llm_toolbar.open_hugging_face
        )
        actions["refresh"].triggered.connect(self.llm_toolbar.check_status)

    def _view_log_file(self):
        """Open the log directory in the system file manager."""
        from templatr.core.config import get_log_dir

        log_dir = get_log_dir()
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(log_dir)))

    def _show_llm_settings(self):
        """Show the LLM settings dialog."""
        LLMSettingsDialog(self).exec()


def run_gui() -> int:
    """Run the GUI application.

    Returns:
        Exit code.
    """
    app = QApplication(sys.argv)
    app.setApplicationName("Automatr")
    app.setApplicationVersion(__version__)

    # Apply theme with font size
    config = get_config()
    stylesheet = get_theme_stylesheet(config.ui.theme, config.ui.font_size)
    app.setStyleSheet(stylesheet)
    app.setFont(QFont(app.font().family(), config.ui.font_size))

    window = MainWindow()
    window.show()

    return app.exec()
