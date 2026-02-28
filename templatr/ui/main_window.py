"""Main window for Templatr GUI."""

import sys
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import (
    QAction,
    QDesktopServices,
    QDragEnterEvent,
    QDropEvent,
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
    QPushButton,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from templatr import __version__
from templatr.core.config import (
    get_config,
    get_config_manager,
    get_log_dir,
    save_config,
)
from templatr.core.templates import Template, get_template_manager
from templatr.integrations.llm import get_llm_client, get_llm_server
from templatr.ui._generation import GenerationMixin
from templatr.ui._template_actions import TemplateActionsMixin
from templatr.ui._window_state import WindowStateMixin
from templatr.ui.chat_widget import ChatWidget
from templatr.ui.llm_settings import LLMSettingsDialog
from templatr.ui.llm_toolbar import LLMToolbar
from templatr.ui.slash_input import SlashInputWidget
from templatr.ui.template_tree import TemplateTreeWidget
from templatr.ui.theme import get_theme_stylesheet
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
        self.setWindowTitle(f"Templatr v{__version__}")
        self.setMinimumSize(600, 400)

        cfg = self.config_manager.config
        self.resize(cfg.ui.window_width, cfg.ui.window_height)

        self.current_template: Optional[Template] = None
        self.worker: Optional[GenerationWorker] = None

        # Active streaming bubble (set by GenerationMixin)
        self._active_ai_bubble = None

        # Feedback tracking - stores last AI generation for feedback
        self._last_prompt: Optional[str] = None
        self._last_output: Optional[str] = None

        # Retained as None — kept importable as fallback, not instantiated
        self.variable_form = None
        self.output_pane = None

        # Active conversational flow (e.g., /new quick-create)
        self._active_flow = None

        self.setAcceptDrops(True)

        self._setup_menu_bar()
        self._setup_ui()
        self._setup_status_bar()
        self._setup_shortcuts()
        self._wire_tree_signals()
        self.template_tree_widget.load_templates()
        self._restore_state()
        self.llm_toolbar.check_status()
        self._apply_scaling()

    # ------------------------------------------------------------------
    # Sidebar toggle
    # ------------------------------------------------------------------

    def _toggle_sidebar(self):
        """Toggle template tree sidebar visibility."""
        visible = self.template_tree_widget.isVisible()
        self.template_tree_widget.setVisible(not visible)
        if not visible:
            total = self.splitter.width()
            sidebar_width = max(200, total // 4)
            self.splitter.setSizes([sidebar_width, total - sidebar_width])
        else:
            self.splitter.setSizes([0, self.splitter.width()])
        if hasattr(self, "_sidebar_btn"):
            self._sidebar_btn.setChecked(not visible)

    # ------------------------------------------------------------------
    # Responsive layout helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_base_font(height: int) -> int:
        """Compute base font size from window height (13–18pt)."""
        return max(13, min(18, height // 50))

    @staticmethod
    def _compute_padding(width: int) -> int:
        """Compute scaled padding from window width (min 8px)."""
        return max(8, width // 120)

    def _apply_scaling(self):
        """Push scaled font values to child widgets."""
        w = self.width()
        h = self.height()
        self.template_tree_widget.scale_to(w, h)

    def resizeEvent(self, event: QResizeEvent):  # noqa: N802
        """Handle window resize: update scaling."""
        super().resizeEvent(event)
        self._apply_scaling()

    def _on_server_running_changed(self, is_running: bool):
        """Update menu actions and input bar readiness when server status changes."""
        self.start_server_action.setEnabled(not is_running)
        self.stop_server_action.setEnabled(is_running)
        self.slash_input.set_llm_ready(is_running)

    def _wire_tree_signals(self):
        """Connect TemplateTreeWidget signals to MainWindow slots."""
        tree = self.template_tree_widget
        tree.template_selected.connect(self._on_template_selected)
        tree.folder_selected.connect(self._on_folder_selected)
        tree.edit_requested.connect(lambda t: self._edit_template(t))
        tree.improve_requested.connect(lambda t: self._improve_template(t))
        tree.version_history_requested.connect(lambda t: self._show_version_history(t))
        tree.new_template_requested.connect(self._new_template)
        tree.template_deleted.connect(self._on_template_deleted)
        tree.status_message.connect(
            lambda msg, ms: self.status_bar.showMessage(msg, ms)
        )

    def _on_template_selected(self, template: Template):
        """Handle template selection from tree widget."""
        self.current_template = template

    def _on_folder_selected(self):
        """Handle folder selection (deselect template)."""
        self.current_template = None

    def _on_template_deleted(self, name: str):
        """Handle template deletion from tree widget."""
        self.current_template = None

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
        view_log_action.triggered.connect(self._open_log_directory)
        help_menu.addAction(view_log_action)
        help_menu.addSeparator()
        about_action = QAction("&About Templatr", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

        # Sidebar toggle button in menu bar corner
        self._sidebar_btn = QPushButton("Templates")
        self._sidebar_btn.setObjectName("secondary")
        self._sidebar_btn.setCheckable(True)
        self._sidebar_btn.setChecked(False)
        self._sidebar_btn.setToolTip("Toggle template sidebar (Ctrl+B)")
        self._sidebar_btn.toggled.connect(
            lambda checked: self._set_sidebar_visible(checked)
        )
        menubar.setCornerWidget(self._sidebar_btn, Qt.Corner.TopLeftCorner)

    def _set_sidebar_visible(self, visible: bool):
        """Set sidebar visibility from button state (avoids toggle recursion).

        Args:
            visible: True to show the sidebar, False to hide it.
        """
        if self.template_tree_widget.isVisible() == visible:
            return
        self.template_tree_widget.setVisible(visible)
        if visible:
            total = self.splitter.width()
            sidebar_width = max(200, total // 4)
            self.splitter.setSizes([sidebar_width, total - sidebar_width])
        else:
            self.splitter.setSizes([0, self.splitter.width()])

    def _setup_shortcuts(self):
        """Set up additional keyboard shortcuts."""
        QShortcut(QKeySequence("Ctrl++"), self).activated.connect(self._increase_font)
        QShortcut(QKeySequence("Ctrl+="), self).activated.connect(self._increase_font)
        QShortcut(QKeySequence("Ctrl+-"), self).activated.connect(self._decrease_font)
        QShortcut(QKeySequence("Ctrl+0"), self).activated.connect(self._reset_font)
        QShortcut(QKeySequence("Ctrl+B"), self).activated.connect(self._toggle_sidebar)

        sc = self.config_manager.config.ui.shortcuts
        QShortcut(QKeySequence(sc["generate"]), self).activated.connect(
            self._on_generate_shortcut
        )
        QShortcut(QKeySequence(sc["copy_output"]), self).activated.connect(
            self._copy_last_output
        )
        QShortcut(QKeySequence(sc["clear_chat"]), self).activated.connect(
            self._clear_chat
        )
        QShortcut(QKeySequence(sc["next_template"]), self).activated.connect(
            self._select_next_template
        )
        QShortcut(QKeySequence(sc["prev_template"]), self).activated.connect(
            self._select_prev_template
        )

    def _on_generate_shortcut(self) -> None:
        """Handle the generate keyboard shortcut (default Ctrl+Return).

        Guarded: does nothing when the slash-command palette is visible or
        when the inline variable form is active.
        """
        if self.slash_input.is_palette_visible():
            return
        if self.slash_input._inline_form.isVisible():
            return
        text = self.slash_input._text_input.toPlainText().strip()
        if text:
            self.slash_input._text_input.clear()
            self._handle_plain_input(text)

    def _copy_last_output(self) -> None:
        """Copy the last AI-generated output to the system clipboard.

        No-op when no generation has completed yet (_last_output is None).
        """
        if self._last_output is not None:
            QApplication.clipboard().setText(self._last_output)

    def _clear_chat(self) -> None:
        """Clear the chat thread (default Ctrl+L shortcut).

        No-op when a generation worker is currently running.
        """
        if self.worker and self.worker.isRunning():
            return
        self.chat_widget.clear_history()

    def _select_next_template(self) -> None:
        """Select the next template in list order, wrapping around to the first.

        No-op when the template list is empty.
        """
        templates = self.template_manager.list_all()
        if not templates:
            return
        if self.current_template is None:
            self.current_template = templates[0]
            return
        try:
            idx = next(i for i, t in enumerate(templates) if t is self.current_template)
        except StopIteration:
            self.current_template = templates[0]
            return
        self.current_template = templates[(idx + 1) % len(templates)]

    def _select_prev_template(self) -> None:
        """Select the previous template in list order, wrapping around to the last.

        No-op when the template list is empty.
        """
        templates = self.template_manager.list_all()
        if not templates:
            return
        if self.current_template is None:
            self.current_template = templates[-1]
            return
        try:
            idx = next(i for i, t in enumerate(templates) if t is self.current_template)
        except StopIteration:
            self.current_template = templates[-1]
            return
        self.current_template = templates[(idx - 1) % len(templates)]

    def keyPressEvent(self, event) -> None:  # noqa: N802
        """Dispatch shortcut actions from key events sent directly to the window.

        QShortcut only fires when the window is the application's active window.
        This override handles the same key combinations so that test code sending
        events directly (qtbot.keyPress) also triggers the shortcut handlers.
        In a running app the QShortcut intercepts first and this path is skipped.
        """
        key = event.key()
        mods = event.modifiers()
        ctrl = bool(mods & Qt.KeyboardModifier.ControlModifier)
        shift = bool(mods & Qt.KeyboardModifier.ShiftModifier)
        alt = bool(mods & Qt.KeyboardModifier.AltModifier)
        meta = bool(mods & Qt.KeyboardModifier.MetaModifier)

        if ctrl and not shift and not alt and not meta and key == Qt.Key.Key_Return:
            self._on_generate_shortcut()
            event.accept()
            return
        if ctrl and shift and not alt and not meta and key == Qt.Key.Key_C:
            self._copy_last_output()
            event.accept()
            return
        if ctrl and not shift and not alt and not meta and key == Qt.Key.Key_L:
            self._clear_chat()
            event.accept()
            return
        if ctrl and not shift and not alt and not meta and key == Qt.Key.Key_BracketRight:
            if hasattr(self, "_select_next_template"):
                self._select_next_template()
            event.accept()
            return
        if ctrl and not shift and not alt and not meta and key == Qt.Key.Key_BracketLeft:
            if hasattr(self, "_select_prev_template"):
                self._select_prev_template()
            event.accept()
            return
        super().keyPressEvent(event)

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
            if label.text() in ("Templates",):
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

    def _open_log_directory(self):
        """Open the log directory in the system file manager."""
        log_dir = get_log_dir()
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(log_dir)))

    def _show_about(self):
        """Show the about dialog."""
        QMessageBox.about(
            self,
            "About Templatr",
            f"<h2>Templatr v{__version__}</h2>"
            "<p>Local prompt optimizer with reusable templates.</p>"
            "<p><b>Features:</b></p><ul>"
            "<li>Template-driven prompts via / command</li>"
            "<li>Local llama.cpp integration</li></ul>"
            "<p><a href='https://github.com/josiahH-cf/templatr'>GitHub</a></p>",
        )

    def _setup_ui(self):
        """Set up the main UI: 2-pane layout with chat thread and slash input."""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 2-pane splitter: collapsible template tree | chat column
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.splitterMoved.connect(self._on_splitter_moved)

        # Left: template tree (hidden by default)
        self.template_tree_widget = TemplateTreeWidget()
        self.template_tree = (
            self.template_tree_widget.tree
        )  # alias for state save/restore
        self.template_tree_widget.setVisible(False)
        self.splitter.addWidget(self.template_tree_widget)

        # Right: chat thread + slash input bar stacked vertically
        right_col = QWidget()
        right_layout = QVBoxLayout(right_col)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.chat_widget = ChatWidget()
        right_layout.addWidget(self.chat_widget, stretch=1)

        self.slash_input = SlashInputWidget()
        self.slash_input.template_submitted.connect(self._generate)
        self.slash_input.plain_submitted.connect(self._handle_plain_input)
        self.slash_input.system_command.connect(self._on_system_command)
        right_layout.addWidget(self.slash_input)

        self.splitter.addWidget(right_col)
        # Start with tree collapsed
        self.splitter.setSizes([0, 1])

        main_layout.addWidget(self.splitter)

        # Populate slash palette with all known templates
        templates = self.template_manager.list_all()
        self.slash_input.set_templates(templates)

    def _on_splitter_moved(self, pos: int, index: int):
        """Sync sidebar button state when user drags the splitter.

        Args:
            pos: New splitter position.
            index: Handle index that was moved.
        """
        visible = self.splitter.sizes()[0] > 10
        if hasattr(self, "_sidebar_btn"):
            self._sidebar_btn.setChecked(visible)

    def _setup_status_bar(self):
        """Set up the status bar with the LLM toolbar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.llm_toolbar = LLMToolbar()
        self.llm_toolbar.status_message.connect(
            lambda msg, ms: self.status_bar.showMessage(msg, ms)
        )
        self.llm_toolbar.server_running_changed.connect(self._on_server_running_changed)
        self.status_bar.addWidget(self.llm_toolbar)
        self.llm_toolbar.set_model_menu(self.model_menu)

        # Wire deferred menu actions to toolbar
        actions = self._llm_menu_actions
        actions["start"].triggered.connect(self.llm_toolbar.start_server)
        actions["stop"].triggered.connect(self.llm_toolbar.stop_server)
        actions["download"].triggered.connect(self.llm_toolbar.open_hugging_face)
        actions["refresh"].triggered.connect(self.llm_toolbar.check_status)

    def _show_llm_settings(self):
        """Show the LLM settings dialog."""
        LLMSettingsDialog(self).exec()

    def _on_system_command(self, command_id: str) -> None:
        """Handle a system command from the slash input bar.

        Args:
            command_id: The command identifier (e.g., "help", "settings").
        """
        if command_id == "help":
            help_text = (
                "**Available commands:**\n\n"
                "- `/help` — Show this help message\n"
                "- `/new` — Create a new template\n"
                "- `/import` — Import a template\n"
                "- `/export` — Export a template\n"
                "- `/settings` — Open LLM settings\n\n"
                "Type `/` followed by a template name to search templates.\n"
                "Type `:trigger` to invoke a template by its trigger shortcut."
            )
            bubble = self.chat_widget.add_ai_bubble()
            bubble.set_text(help_text)
        elif command_id == "settings":
            self._show_llm_settings()
        elif command_id == "new":
            if hasattr(self, "_new_template"):
                self._new_template()
        elif command_id == "import":
            if hasattr(self, "_import_template"):
                self._import_template()
        elif command_id == "export":
            if hasattr(self, "_export_template"):
                self._export_template()

    def _handle_plain_input(self, text: str) -> None:
        """Route plain text input, delegating to an active flow or generation.

        If a conversational flow (e.g., /new quick-create) is active, the
        input is routed there. Otherwise it falls through to _generate.

        Args:
            text: Plain text from the slash input bar.
        """
        if self._handle_flow_input(text):
            return
        self._generate(text)

    # ------------------------------------------------------------------
    # Drag-and-drop import
    # ------------------------------------------------------------------

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        """Accept drag events that contain at least one ``.json`` file URL.

        Args:
            event: The drag-enter event.
        """
        if event.mimeData() and event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().endswith(".json"):
                    event.acceptProposedAction()
                    return
        super().dragEnterEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802
        """Import each dropped ``.json`` file as a template.

        Args:
            event: The drop event.
        """
        if event.mimeData() and event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                local = url.toLocalFile()
                if local.endswith(".json"):
                    self._handle_import_file(Path(local))
            event.acceptProposedAction()
            return
        super().dropEvent(event)


def run_gui() -> int:
    """Run the GUI application.

    Returns:
        Exit code.
    """
    app = QApplication(sys.argv)
    app.setApplicationName("Templatr")
    app.setApplicationVersion(__version__)

    # Apply theme with font size
    config = get_config()
    stylesheet = get_theme_stylesheet(config.ui.theme, config.ui.font_size)
    app.setStyleSheet(stylesheet)
    app.setFont(QFont(app.font().family(), config.ui.font_size))

    window = MainWindow()
    window.show()

    return app.exec()
