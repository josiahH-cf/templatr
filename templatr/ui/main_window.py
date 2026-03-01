"""Main window for Templatr GUI."""

import re
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
from templatr.core.conversation import ConversationMemory
from templatr.core.prompt_history import PromptHistoryStore, get_prompt_history_store
from templatr.core.templates import Template, get_template_manager
from templatr.integrations.llm import ModelInfo, get_llm_client, get_llm_server
from templatr.ui._generation import GenerationMixin
from templatr.ui._template_actions import TemplateActionsMixin
from templatr.ui._window_state import WindowStateMixin
from templatr.ui.chat_widget import ChatWidget
from templatr.ui.history_browser import HistoryBrowserDialog
from templatr.ui.llm_settings import LLMSettingsDialog
from templatr.ui.llm_toolbar import LLMToolbar
from templatr.ui.slash_input import SlashInputWidget
from templatr.ui.template_tree import TemplateTreeWidget
from templatr.ui.theme import get_theme_stylesheet
from templatr.ui.workers import ABTestWorker, GenerationWorker, MultiModelCompareWorker


class MainWindow(TemplateActionsMixin, GenerationMixin, WindowStateMixin, QMainWindow):
    """Main application window."""

    def __init__(
        self,
        config=None,
        templates=None,
        llm_client=None,
        llm_server=None,
        prompt_history: Optional[PromptHistoryStore] = None,
    ):
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
        self.prompt_history = prompt_history or get_prompt_history_store()
        self.setWindowTitle(f"Templatr v{__version__}")
        self.setMinimumSize(600, 400)

        cfg = self.config_manager.config
        self.resize(cfg.ui.window_width, cfg.ui.window_height)

        self.current_template: Optional[Template] = None
        self.worker: Optional[GenerationWorker] = None
        self.compare_worker: Optional[MultiModelCompareWorker] = None
        self.ab_test_worker: Optional[ABTestWorker] = None
        self._last_test_results: Optional[list] = None
        self._last_test_history_ids: Optional[list] = None

        # Active streaming bubble (set by GenerationMixin)
        self._active_ai_bubble = None

        # Feedback tracking - stores last AI generation for feedback
        self._last_prompt: Optional[str] = None
        self._last_original_prompt: Optional[str] = None
        self._last_output: Optional[str] = None

        # Multi-turn conversation memory (session-only)
        cfg_llm = self.config_manager.config.llm
        self.conversation_memory = ConversationMemory(
            max_turns=cfg_llm.max_turns,
            context_char_limit=cfg_llm.context_char_limit,
        )

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
        if self.current_template is not template:
            self.conversation_memory.reset()
        self.current_template = template

    def _on_palette_template_chosen(self, template_name: str) -> None:
        """Reset conversation memory when a different template is chosen via the palette.

        Args:
            template_name: Name of the template the user just selected.
        """
        current_name = self.current_template.name if self.current_template else None
        if template_name != current_name:
            self.conversation_memory.reset()

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
        history_action = QAction("View &History…", self)
        history_action.setShortcut(QKeySequence("Ctrl+H"))
        history_action.triggered.connect(self._show_history_browser)
        help_menu.addAction(history_action)
        help_menu.addSeparator()
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
        QShortcut(QKeySequence("Ctrl+H"), self).activated.connect(self._show_history_browser)

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

        Also resets conversation memory so the next message starts a fresh
        context.  No-op when a generation worker is currently running.
        """
        if self.worker and self.worker.isRunning():
            return
        self.chat_widget.clear_history()
        self.conversation_memory.reset()

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
        self.slash_input.template_chosen.connect(self._on_palette_template_chosen)
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

    def _show_history_browser(self) -> None:
        """Open the prompt history browser dialog.

        Connects the output_reused signal so re-used text is sent to the
        chat input for further generation.
        """
        dialog = HistoryBrowserDialog(store=self.prompt_history, parent=self)
        dialog.output_reused.connect(self._handle_plain_input)
        dialog.exec()

    def _on_system_command(self, command_id: str) -> None:
        """Handle a system command from the slash input bar.

        Args:
            command_id: The command identifier (e.g., "help", "settings").
        """
        if command_id == "help":
            help_text = (
                "**Available commands:**\n\n"
                "- `/help` — Show this help message\n"
                "- `/history` — Show recent outputs for current template\n"
                "- `/favorites` — Show favorite outputs\n"
                "- `/favorite` — Favorite the last output\n"
                "- `/compare` — Compare output across multiple models\n"
                "- `/test [N] [| prompt]` — Run prompt N times and compare outputs\n"
                "- `/performance` — Show generation performance metrics\n"
                "- `/new` — Create a new template\n"
                "- `/import` — Import a template\n"
                "- `/export` — Export a template\n"
                "- `/settings` — Open LLM settings\n"
                "- `/browse` — Browse and install community templates\n\n"
                "Type `/` followed by a template name to search templates.\n"
                "Type `:trigger` to invoke a template by its trigger shortcut.\n\n"
                "**Multi-turn conversation:**\n\n"
                "Messages in the same chat thread build on each other automatically — "
                "the model sees prior exchanges as context. Use `Ctrl+L` or `/clear` "
                "to start fresh. Switching templates also resets the context.\n"
                "Configure _Conversation Turns_ and _Context Char Limit_ in `/settings`.\n\n"
                "**Keyboard shortcuts:**\n\n"
                "- `Ctrl+Return` — Generate (submit plain text)\n"
                "- `Ctrl+Shift+C` — Copy last AI output to clipboard\n"
                "- `Ctrl+L` — Clear chat thread and reset conversation memory\n"
                "- `Ctrl+]` — Next template\n"
                "- `Ctrl+[` — Previous template"
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
        elif command_id == "history":
            self._handle_history_command("/history")
        elif command_id == "favorites":
            self._handle_history_command("/favorites")
        elif command_id == "favorite":
            self._handle_history_command("/favorite")
        elif command_id == "compare":
            self._handle_compare_command("/compare")
        elif command_id == "test":
            self._handle_test_command("/test")
        elif command_id == "browse":
            if hasattr(self, "_open_catalog_browser"):
                self._open_catalog_browser()
        elif command_id == "performance":
            self._open_performance_dashboard()

    def _handle_plain_input(self, text: str) -> None:
        """Route plain text input, delegating to an active flow or generation.

        If a conversational flow (e.g., /new quick-create) is active, the
        input is routed there. Otherwise it falls through to _generate.

        Args:
            text: Plain text from the slash input bar.
        """
        if self._handle_flow_input(text):
            return
        if self._handle_compare_command(text):
            return
        if self._handle_test_command(text):
            return
        if self._handle_performance_command(text):
            return
        if self._handle_history_command(text):
            return
        self._generate(text)

    def _handle_compare_command(self, text: str) -> bool:
        """Handle `/compare` command for side-by-side model output comparison.

        Syntax:
            /compare
            /compare modelA,modelB
            /compare modelA,modelB | custom prompt text

        Without a prompt after `|`, the last generated prompt is used.

        Args:
            text: Raw input text.

        Returns:
            True if handled as compare command, else False.
        """
        stripped = text.strip()
        if not stripped.startswith("/compare"):
            return False

        if self.worker and self.worker.isRunning():
            self.chat_widget.add_system_message(
                "Generation is in progress. Wait for it to finish before comparing."
            )
            return True

        if self.compare_worker and self.compare_worker.isRunning():
            self.chat_widget.add_system_message("A model comparison is already running.")
            return True

        parts = stripped.split(maxsplit=1)
        arg = parts[1].strip() if len(parts) > 1 else ""

        explicit_prompt = ""
        model_query = arg
        if "|" in arg:
            model_query, explicit_prompt = [piece.strip() for piece in arg.split("|", 1)]

        if explicit_prompt:
            # AC-6: wrap the explicit prompt in conversation context so the
            # comparison reflects the current multi-turn conversation state.
            memory = getattr(self, "conversation_memory", None)
            if memory is not None:
                prompt, _ = memory.assemble_prompt(explicit_prompt)
            else:
                prompt = explicit_prompt
        else:
            # Reuse the last assembled prompt as-is — do NOT strip, because
            # the ChatML tail may end with a significant trailing newline.
            prompt = self._last_prompt or ""

        if not prompt:
            self.chat_widget.add_system_message(
                "No prompt available. Generate once first, or use `/compare modelA,modelB | your prompt`."
            )
            return True

        available_models = get_llm_server().find_models()
        if len(available_models) < 2:
            self.chat_widget.add_system_message(
                "Need at least two local .gguf models to compare outputs."
            )
            return True

        selected_models = self._select_compare_models(model_query, available_models)
        if isinstance(selected_models, str):
            self.chat_widget.add_system_message(selected_models)
            return True

        selected_paths = [m.path for m in selected_models]
        self._last_prompt = prompt
        self._last_output = None

        names = ", ".join(model.stem for model in selected_paths)
        self.chat_widget.add_system_message(f"Comparing models: {names}")
        self.slash_input.set_generating(True)

        self.compare_worker = MultiModelCompareWorker(prompt, selected_paths)
        self.compare_worker.progress.connect(
            lambda msg: self.status_bar.showMessage(msg, 3000)
        )
        self.compare_worker.error.connect(self._on_compare_error)
        self.compare_worker.finished.connect(
            lambda results, used_prompt=prompt: self._on_compare_finished(
                used_prompt, results
            )
        )
        self.compare_worker.start()
        return True

    def _select_compare_models(
        self, model_query: str, available_models: list[ModelInfo]
    ) -> list[ModelInfo] | str:
        """Select models for comparison from available local models.

        Args:
            model_query: Comma-separated model names from command input.
            available_models: Models discovered on disk.

        Returns:
            Selected models, or an error message string.
        """
        if not model_query:
            return available_models[:2]

        wanted = [chunk.strip() for chunk in model_query.split(",") if chunk.strip()]
        if len(wanted) < 2:
            return "Specify at least two models: `/compare modelA,modelB`"

        def _match_one(token: str) -> Optional[ModelInfo]:
            lowered = token.lower()
            for model in available_models:
                if lowered in {
                    model.name.lower(),
                    model.path.name.lower(),
                    model.path.stem.lower(),
                }:
                    return model
            return None

        selected: list[ModelInfo] = []
        seen_paths: set[Path] = set()
        missing: list[str] = []

        for token in wanted:
            matched = _match_one(token)
            if not matched:
                missing.append(token)
                continue
            if matched.path in seen_paths:
                continue
            selected.append(matched)
            seen_paths.add(matched.path)

        if missing:
            return f"Unknown model(s): {', '.join(missing)}"
        if len(selected) < 2:
            return "Need at least two distinct models for `/compare`."
        return selected

    def _on_compare_finished(self, prompt: str, results: list[dict]) -> None:
        """Handle completion of multi-model comparison run."""
        self.slash_input.set_generating(False)
        self.compare_worker = None

        if not results:
            self.chat_widget.add_system_message("Comparison completed with no results.")
            self.status_bar.showMessage("Comparison complete", 3000)
            return

        for result in results:
            self._record_generation_history(prompt, result.get("output", ""))

        self._last_output = str(results[-1].get("output", ""))
        self.chat_widget.add_system_message(self._render_compare_results(prompt, results))
        self.status_bar.showMessage("Comparison complete", 3000)

    def _on_compare_error(self, error: str) -> None:
        """Handle comparison worker failure."""
        self.slash_input.set_generating(False)
        self.compare_worker = None
        self.chat_widget.show_error_bubble(error)
        self.status_bar.showMessage("Comparison failed", 5000)

    def _render_compare_results(self, prompt: str, results: list[dict]) -> str:
        """Render side-by-side comparison summary and per-model outputs."""
        prompt_preview = prompt.strip().replace("\n", " ")
        if len(prompt_preview) > 90:
            prompt_preview = f"{prompt_preview[:87]}..."

        lines = [
            "**Multi-model comparison**",
            "",
            f"Prompt: {prompt_preview}",
            "",
            "| Model | Speed (s) | Prompt Tokens (est.) | Output Tokens (est.) |",
            "|---|---:|---:|---:|",
        ]
        for result in results:
            lines.append(
                "| "
                f"{result['model_name']} | "
                f"{result['latency_seconds']:.2f} | "
                f"{result['prompt_tokens_est']} | "
                f"{result['output_tokens_est']} |"
            )

        lines.append("")
        lines.append("Quality comparison: review full outputs below.")
        lines.append("")

        for result in results:
            lines.append(f"### {result['model_name']}")
            lines.append("")
            lines.append(result["output"] or "_No output generated._")
            lines.append("")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Performance dashboard (/performance)
    # ------------------------------------------------------------------

    def _handle_performance_command(self, text: str) -> bool:
        """Handle `/performance` command to open the performance dashboard.

        Args:
            text: Raw input text.

        Returns:
            True if handled, else False.
        """
        if not text.strip().startswith("/performance"):
            return False
        self._open_performance_dashboard()
        return True

    def _open_performance_dashboard(self) -> None:
        """Open the performance dashboard dialog with current history data."""
        from templatr.ui.performance_dashboard import PerformanceDashboard

        entries = self.prompt_history.list_entries(limit=None)
        entry_dicts = [e.to_dict() for e in entries]
        dialog = PerformanceDashboard(entry_dicts, parent=self)
        dialog.exec()

    # ------------------------------------------------------------------
    # Prompt A/B testing (/test)
    # ------------------------------------------------------------------

    def _handle_test_command(self, text: str) -> bool:
        """Handle the `/test` slash command for A/B iteration testing.

        Syntax::

            /test                     → 3 iterations, last prompt
            /test 5                   → 5 iterations, last prompt
            /test 5 | custom prompt   → 5 iterations, custom prompt
            /test | custom prompt     → 3 iterations, custom prompt
            /test view                → open detail dialog

        Args:
            text: Raw input text.

        Returns:
            True if handled as a /test command, else False.
        """
        stripped = text.strip()
        if not stripped.startswith("/test"):
            return False

        # Must be /test (not /testfoo)
        remainder = stripped[len("/test"):]
        if remainder and not remainder[0].isspace():
            return False

        remainder = remainder.strip()

        # "/test view" — open detail dialog
        if remainder.lower() == "view":
            self._open_ab_test_detail()
            return True

        # Parse optional N and optional | prompt
        iterations = 3
        explicit_prompt = ""

        if "|" in remainder:
            n_part, explicit_prompt = [p.strip() for p in remainder.split("|", 1)]
            if n_part:
                try:
                    iterations = int(n_part)
                except ValueError:
                    self.chat_widget.add_system_message(
                        "Invalid iteration count. Usage: `/test [N] [| prompt]`"
                    )
                    return True
        elif remainder:
            try:
                iterations = int(remainder)
            except ValueError:
                self.chat_widget.add_system_message(
                    "Invalid argument. Usage: `/test [N] [| prompt]`"
                )
                return True

        if iterations < 2:
            self.chat_widget.add_system_message(
                "Iteration count must be at least 2. Usage: `/test [N] [| prompt]`"
            )
            return True

        # Resolve prompt
        if explicit_prompt:
            memory = getattr(self, "conversation_memory", None)
            if memory is not None:
                prompt, _ = memory.assemble_prompt(explicit_prompt)
            else:
                prompt = explicit_prompt
        else:
            prompt = self._last_prompt or ""

        if not prompt:
            self.chat_widget.add_system_message(
                "No prompt available. Generate once first, or use `/test [N] | your prompt`."
            )
            return True

        server = get_llm_server()
        if not server.is_running():
            self.chat_widget.add_system_message(
                "The LLM server is not running. Start it from the toolbar first."
            )
            return True

        if self.worker and self.worker.isRunning():
            self.chat_widget.add_system_message(
                "Generation is in progress. Wait for it to finish before running a test."
            )
            return True

        if self.ab_test_worker and self.ab_test_worker.isRunning():
            self.chat_widget.add_system_message("An A/B test is already running.")
            return True

        self._last_test_results = None
        self._last_test_history_ids = None

        self.chat_widget.add_system_message(
            f"Running {iterations} iterations\u2026"
        )
        self.slash_input.set_generating(True)

        self.ab_test_worker = ABTestWorker(prompt, iterations)
        self.ab_test_worker.progress.connect(self._on_ab_test_progress)
        self.ab_test_worker.error.connect(self._on_ab_test_error)
        self.ab_test_worker.finished.connect(
            lambda results, p=prompt: self._on_ab_test_finished(p, results)
        )
        self.ab_test_worker.start()
        return True

    def _on_ab_test_progress(self, current: int, total: int) -> None:
        """Update status bar with iteration progress.

        Args:
            current: The iteration number just starting (1-based).
            total: Total number of iterations planned.
        """
        self.status_bar.showMessage(
            f"A/B test: running iteration {current}/{total}\u2026", 5000
        )

    def _on_ab_test_finished(self, prompt: str, results: list[dict]) -> None:
        """Handle A/B test completion: record history, render summary, store results.

        Args:
            prompt: The prompt that was tested.
            results: List of per-iteration result dicts from ABTestWorker.
        """
        self.slash_input.set_generating(False)
        self.ab_test_worker = None

        if not results:
            self.chat_widget.add_system_message("Test completed with no results.")
            self.status_bar.showMessage("A/B test complete", 3000)
            return

        # Record each output individually in history (AC-6)
        history_ids: list[str] = []
        for r in results:
            entry = self._record_generation_history_with_id(prompt, r.get("output", ""))
            history_ids.append(entry.id if entry else "")

        self._last_test_results = results
        self._last_test_history_ids = history_ids
        self._last_output = results[-1].get("output", "")

        self.chat_widget.add_system_message(self._render_ab_test_summary(prompt, results))
        self.status_bar.showMessage("A/B test complete", 3000)

    def _on_ab_test_error(self, error: str) -> None:
        """Handle A/B test worker error.

        Args:
            error: Human-readable error message from the worker.
        """
        self.slash_input.set_generating(False)
        self.ab_test_worker = None
        self.chat_widget.show_error_bubble(error)
        self.status_bar.showMessage("A/B test failed", 5000)

    def _open_ab_test_detail(self) -> None:
        """Open the ABTestResultsDialog if test results are available (AC-4)."""
        if not self._last_test_results:
            self.chat_widget.add_system_message(
                "No test results available. Run `/test [N]` first."
            )
            return

        from templatr.ui.ab_test_dialog import ABTestResultsDialog

        dlg = ABTestResultsDialog(
            results=self._last_test_results,
            history_ids=self._last_test_history_ids or [],
            parent=self,
        )
        dlg.winner_selected.connect(self._on_ab_test_winner_selected)
        dlg.exec()

    def _on_ab_test_winner_selected(self, index: int) -> None:
        """Mark the chosen iteration output as a favourite in history (AC-5).

        Args:
            index: 0-based index into the last test results list.
        """
        if not self._last_test_history_ids or index >= len(self._last_test_history_ids):
            return

        history_id = self._last_test_history_ids[index]
        if history_id:
            marked = self.prompt_history.mark_favorite(history_id, favorite=True)
            if marked:
                iteration = (
                    self._last_test_results[index]["iteration"]
                    if self._last_test_results
                    else index + 1
                )
                self.chat_widget.add_system_message(
                    f"Marked Iteration {iteration} as a favourite."
                )
                return

        self.chat_widget.add_system_message("Could not mark output as favourite.")

    def _render_ab_test_summary(self, prompt: str, results: list[dict]) -> str:
        """Render a markdown summary of A/B test results for the chat thread (AC-3).

        Args:
            prompt: The prompt that was tested.
            results: List of per-iteration result dicts.

        Returns:
            Markdown string ready for display in a MessageBubble.
        """
        prompt_preview = prompt.strip().replace("\n", " ")
        if len(prompt_preview) > 90:
            prompt_preview = f"{prompt_preview[:87]}..."

        lines = [
            "**A/B Test Results**",
            "",
            f"Prompt: {prompt_preview}",
            "",
            "| Iteration | Speed (s) | Prompt Tokens (est.) | Output Tokens (est.) |",
            "|---:|---:|---:|---:|",
        ]
        for r in results:
            lines.append(
                f"| {r['iteration']} "
                f"| {r['latency_seconds']:.2f} "
                f"| {r['prompt_tokens_est']} "
                f"| {r['output_tokens_est']} |"
            )

        lines.append("")
        lines.append("**Output previews:**")
        lines.append("")
        for r in results:
            preview = (r.get("output") or "").strip().replace("\n", " ")
            if len(preview) > 120:
                preview = f"{preview[:117]}..."
            lines.append(f"**Iteration {r['iteration']}:** {preview or '_No output._'}")
            lines.append("")

        lines.append("_Type `/test view` to open the full detail view and pick a winner._")
        return "\n".join(lines)

    def _stop_generation(self) -> None:
        """Stop the current generation or A/B test worker (AC-8).

        Overrides GenerationMixin._stop_generation to also cancel any running
        ABTestWorker in addition to the standard GenerationWorker.
        """
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.slash_input.set_generating(False)
            self.status_bar.showMessage("Generation stopped", 3000)

        if self.ab_test_worker and self.ab_test_worker.isRunning():
            self.ab_test_worker.stop()
            self.slash_input.set_generating(False)
            self.status_bar.showMessage("A/B test stopped", 3000)

    def _record_generation_history_with_id(
        self,
        prompt: str,
        output: str,
        latency_seconds: float | None = None,
        output_tokens_est: int | None = None,
        model_name: str | None = None,
    ):
        """Persist a history entry and return it (so the ID can be stored).

        Args:
            prompt: Rendered prompt sent to the model.
            output: Completed model output.
            latency_seconds: Optional generation latency in seconds.
            output_tokens_est: Optional estimated output token count.
            model_name: Optional model name that produced the output.

        Returns:
            The persisted PromptHistoryEntry, or None if not recorded.
        """
        if not prompt or not output:
            return None
        template_name = self.current_template.name if self.current_template else None
        return self.prompt_history.add_entry(
            template_name,
            prompt,
            output,
            latency_seconds=latency_seconds,
            output_tokens_est=output_tokens_est,
            model_name=model_name,
        )

    def _record_generation_history(
        self,
        prompt: str,
        output: str,
        latency_seconds: float | None = None,
        output_tokens_est: int | None = None,
        model_name: str | None = None,
    ) -> None:
        """Persist a prompt/output pair in history storage.

        Args:
            prompt: Rendered prompt text sent to the model.
            output: Completed model output text.
            latency_seconds: Optional generation latency in seconds.
            output_tokens_est: Optional estimated output token count.
            model_name: Optional model name that produced the output.
        """
        self._record_generation_history_with_id(
            prompt,
            output,
            latency_seconds=latency_seconds,
            output_tokens_est=output_tokens_est,
            model_name=model_name,
        )

    def _handle_history_command(self, text: str) -> bool:
        """Handle history-related slash commands from plain input.

        Supported commands:
            /history [query|YYYY-MM-DD]
            /favorites [query]
            /favorite

        Args:
            text: Raw input text.

        Returns:
            True if the command was handled.
        """
        stripped = text.strip()
        if not stripped.startswith("/"):
            return False

        parts = stripped.split(maxsplit=1)
        command = parts[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else ""

        template_name = self.current_template.name if self.current_template else None

        if command == "/favorite":
            if not self._last_output:
                self.chat_widget.add_system_message("No output available to favorite yet.")
                return True
            marked = self.prompt_history.mark_latest_favorite(
                template_name,
                self._last_output,
                favorite=True,
            )
            if marked:
                self.chat_widget.add_system_message("Marked last output as favorite.")
            else:
                self.chat_widget.add_system_message(
                    "Could not find a matching history entry for the last output."
                )
            return True

        if command not in ("/history", "/favorites"):
            return False

        favorites_only = command == "/favorites"
        date_prefix = None
        query = arg or None
        if arg:
            if arg.startswith("date:"):
                date_prefix = arg[5:].strip() or None
                query = None
            elif re.fullmatch(r"\d{4}-\d{2}-\d{2}", arg):
                date_prefix = arg
                query = None

        entries = self.prompt_history.list_entries(
            template_name=template_name,
            query=query,
            date_prefix=date_prefix,
            favorites_only=favorites_only,
            limit=20,
        )

        scope = template_name or "plain prompts"
        if favorites_only:
            title = f"Favorite outputs ({scope})"
        else:
            title = f"History ({scope})"

        self.chat_widget.add_system_message(self._render_history_entries(title, entries))
        return True

    def _render_history_entries(self, title: str, entries: list) -> str:
        """Render history entries into a compact Markdown message."""
        if not entries:
            return f"**{title}:**\n\n_No matching entries found._"

        lines = [f"**{title}:**", ""]
        for entry in entries:
            star = "★" if entry.favorite else ""
            prompt_preview = entry.prompt.strip().replace("\n", " ")
            if len(prompt_preview) > 60:
                prompt_preview = f"{prompt_preview[:57]}..."
            preview = entry.output.strip().replace("\n", " ")
            if len(preview) > 90:
                preview = f"{preview[:87]}..."
            lines.append(
                f"- `{entry.created_at}` {star} Prompt: {prompt_preview} → Output: {preview}"
            )
        return "\n".join(lines)

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
