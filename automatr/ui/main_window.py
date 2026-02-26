"""Main window for Automatr GUI."""

import base64
import sys
from typing import Optional

from PyQt6.QtCore import Qt, QByteArray
from PyQt6.QtGui import (
    QAction, QKeySequence, QShortcut,
    QWheelEvent, QFont, QCloseEvent, QGuiApplication,
)
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStatusBar,
    QWidget,
)

from automatr import __version__
from automatr.core.config import get_config, save_config
from automatr.core.feedback import get_feedback_manager
from automatr.core.templates import Template, get_template_manager
from automatr.integrations.llm import get_llm_server
from automatr.ui.theme import get_theme_stylesheet
from automatr.ui.template_editor import TemplateEditor
from automatr.ui.llm_settings import LLMSettingsDialog
from automatr.ui.template_improve import TemplateImproveDialog
from automatr.ui.template_generate import GenerationPromptEditor, ImprovementPromptEditor
from automatr.ui.template_tree import TemplateTreeWidget
from automatr.ui.variable_form import VariableFormWidget
from automatr.ui.output_pane import OutputPaneWidget
from automatr.ui.llm_toolbar import LLMToolbar
from automatr.ui.workers import GenerationWorker


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Automatr v{__version__}")
        self.setMinimumSize(600, 400)  # Allow proper window snapping on all screen sizes
        
        config = get_config()
        self.resize(config.ui.window_width, config.ui.window_height)
        
        self.current_template: Optional[Template] = None
        self.worker: Optional[GenerationWorker] = None
        
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
        
        # AI Instructions menu (submenu under File)
        ai_instructions_menu = file_menu.addMenu("AI &Instructions")
        
        edit_generate_action = QAction("Edit &Generate Template Instructions...", self)
        edit_generate_action.triggered.connect(self._edit_generate_instructions)
        ai_instructions_menu.addAction(edit_generate_action)
        
        edit_improve_action = QAction("Edit &Improve Template Instructions...", self)
        edit_improve_action.triggered.connect(self._edit_improve_instructions)
        ai_instructions_menu.addAction(edit_improve_action)
        
        file_menu.addSeparator()
        
        # LLM menu
        llm_menu = menubar.addMenu("&LLM")
        
        self.start_server_action = QAction("&Start Server", self)
        llm_menu.addAction(self.start_server_action)
        
        self.stop_server_action = QAction("S&top Server", self)
        llm_menu.addAction(self.stop_server_action)
        
        llm_menu.addSeparator()
        
        # Model selector submenu (populated by LLMToolbar)
        self.model_menu = llm_menu.addMenu("Select &Model")
        
        download_models_action = QAction("&Download Models (Hugging Face)...", self)
        llm_menu.addAction(download_models_action)
        
        llm_menu.addSeparator()
        
        refresh_action = QAction("&Check Status", self)
        llm_menu.addAction(refresh_action)
        
        llm_menu.addSeparator()
        
        settings_action = QAction("S&ettings...", self)
        settings_action.triggered.connect(self._show_llm_settings)
        llm_menu.addAction(settings_action)
        
        # Store menu actions for deferred wiring (connected in _setup_status_bar)
        self._llm_menu_actions = {
            "start": self.start_server_action,
            "stop": self.stop_server_action,
            "download": download_models_action,
            "refresh": refresh_action,
        }
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About Automatr", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _setup_shortcuts(self):
        """Set up additional keyboard shortcuts."""
        # Font scaling shortcuts
        QShortcut(QKeySequence("Ctrl++"), self).activated.connect(self._increase_font)
        QShortcut(QKeySequence("Ctrl+="), self).activated.connect(self._increase_font)
        QShortcut(QKeySequence("Ctrl+-"), self).activated.connect(self._decrease_font)
        QShortcut(QKeySequence("Ctrl+0"), self).activated.connect(self._reset_font)
    
    def wheelEvent(self, event: QWheelEvent):
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
        # Clamp to reasonable bounds
        size = max(8, min(24, size))
        
        config = get_config()
        config.ui.font_size = size
        save_config(config)
        
        # Apply new stylesheet
        stylesheet = get_theme_stylesheet(config.ui.theme, size)
        app = QApplication.instance()
        if app:
            app.setStyleSheet(stylesheet)
            # Keep widget fonts in sync with the base size to avoid mixed font scaling
            base_font = QFont(app.font().family(), size)
            app.setFont(base_font)
        
        # Update section labels (they have hardcoded sizes)
        label_size = size + 1
        label_style = f"font-weight: bold; font-size: {label_size}pt;"
        for label in self.findChildren(QLabel):
            if label.text() in ("Templates", "Variables", "Output"):
                label.setStyleSheet(label_style)
        
        self.status_bar.showMessage(f"Font size: {size}pt", 2000)
    
    def _increase_font(self):
        """Increase font size by 1pt."""
        config = get_config()
        self._apply_font_size(config.ui.font_size + 1)
    
    def _decrease_font(self):
        """Decrease font size by 1pt."""
        config = get_config()
        self._apply_font_size(config.ui.font_size - 1)
    
    def _reset_font(self):
        """Reset font size to default (13pt)."""
        self._apply_font_size(13)
    
    def _show_about(self):
        """Show the about dialog."""
        QMessageBox.about(
            self,
            "About Automatr",
            f"<h2>Automatr v{__version__}</h2>"
            "<p>Minimal prompt automation with local LLM.</p>"
            "<p><b>Features:</b></p>"
            "<ul>"
            "<li>Template-driven prompts</li>"
            "<li>Local llama.cpp integration</li>"
            "<li>Espanso text expansion</li>"
            "</ul>"
            "<p><a href='https://github.com/yourname/automatr'>GitHub</a></p>",
        )
    
    def _setup_ui(self):
        """Set up the main UI."""
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel: Template tree widget
        self.template_tree_widget = TemplateTreeWidget()
        # Alias for backwards compat with state save/restore
        self.template_tree = self.template_tree_widget.tree
        self.splitter.addWidget(self.template_tree_widget)
        
        # Middle panel: Variable form widget
        self.variable_form = VariableFormWidget()
        self.variable_form.generate_requested.connect(self._generate)
        self.variable_form.render_template_requested.connect(
            self._render_template_only
        )
        self.splitter.addWidget(self.variable_form)

        # Right panel: Output pane widget
        self.output_pane = OutputPaneWidget()
        self.output_pane.stop_requested.connect(self._stop_generation)
        self.output_pane.status_message.connect(
            lambda msg, ms: self.status_bar.showMessage(msg, ms)
        )
        self.splitter.addWidget(self.output_pane)
        
        # Set initial splitter sizes from config
        config = get_config()
        self.splitter.setSizes(config.ui.splitter_sizes)
        
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
    
    def _is_geometry_visible(self, geometry_data: QByteArray) -> bool:
        """Check if restored geometry would be visible on any connected screen.
        
        Uses a 50% overlap threshold - the window must have at least 50% of its
        area visible on some screen to be considered valid.
        """
        # Temporarily restore to get the rect, then we'll validate
        # Save current geometry first
        current_geo = self.saveGeometry()
        self.restoreGeometry(geometry_data)
        window_rect = self.frameGeometry()
        # Restore original
        self.restoreGeometry(current_geo)
        
        # Check overlap with each screen
        for screen in QGuiApplication.screens():
            screen_rect = screen.availableGeometry()
            intersection = window_rect.intersected(screen_rect)
            
            if not intersection.isEmpty():
                # Calculate overlap percentage
                window_area = window_rect.width() * window_rect.height()
                if window_area > 0:
                    overlap_area = intersection.width() * intersection.height()
                    overlap_ratio = overlap_area / window_area
                    if overlap_ratio >= 0.5:  # At least 50% visible
                        return True
        
        return False
    
    def _restore_state(self):
        """Restore window and app state from config."""
        config = get_config()
        geometry_valid = False
        
        # Restore window geometry with screen validation
        if config.ui.window_geometry:
            try:
                geometry_bytes = base64.b64decode(config.ui.window_geometry)
                geometry_data = QByteArray(geometry_bytes)
                
                # Validate geometry is on a visible screen
                if self._is_geometry_visible(geometry_data):
                    self.restoreGeometry(geometry_data)
                    geometry_valid = True
                else:
                    # Clear invalid geometry from config
                    config.ui.window_geometry = ""
                    config.ui.window_maximized = False
                    save_config(config)
            except Exception:
                # Clear corrupted geometry
                config.ui.window_geometry = ""
                save_config(config)
        
        # Only restore maximized state if geometry was valid
        if geometry_valid and config.ui.window_maximized:
            self.setWindowState(Qt.WindowState.WindowMaximized)
        
        # Restore expanded folders in template tree
        if config.ui.expanded_folders:
            for i in range(self.template_tree.topLevelItemCount()):
                item = self.template_tree.topLevelItem(i)
                data = item.data(0, Qt.ItemDataRole.UserRole)
                if data and data[0] == "folder" and data[1] in config.ui.expanded_folders:
                    item.setExpanded(True)
        
        # Restore last selected template
        if config.ui.last_template:
            self._select_template_in_tree(config.ui.last_template)
    
    def closeEvent(self, event: QCloseEvent):
        """Save window and app state when closing."""
        config = get_config()
        
        # Save window geometry (handles position and size)
        geometry_bytes = bytes(self.saveGeometry())
        config.ui.window_geometry = base64.b64encode(geometry_bytes).decode('ascii')
        
        # Save maximized state
        config.ui.window_maximized = self.isMaximized()
        
        # Save window size (for backwards compatibility)
        if not self.isMaximized():
            config.ui.window_width = self.width()
            config.ui.window_height = self.height()
        
        # Save splitter sizes
        config.ui.splitter_sizes = self.splitter.sizes()
        
        # Save current template
        if self.current_template:
            config.ui.last_template = self.current_template.name
        
        # Save expanded folders
        expanded = []
        for i in range(self.template_tree.topLevelItemCount()):
            item = self.template_tree.topLevelItem(i)
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if data and data[0] == "folder" and item.isExpanded():
                expanded.append(data[1])
        config.ui.expanded_folders = expanded
        
        save_config(config)
        event.accept()
    
    def _show_llm_settings(self):
        """Show the LLM settings dialog."""
        dialog = LLMSettingsDialog(self)
        dialog.exec()
    
    def _edit_generate_instructions(self):
        """Edit the AI instructions for template generation."""
        reply = QMessageBox.question(
            self,
            "Edit Generation Instructions?",
            "Editing these instructions will affect how all future template generation works.\n\nAre you sure you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            dialog = GenerationPromptEditor(self)
            dialog.exec()
    
    def _edit_improve_instructions(self):
        """Edit the AI instructions for template improvement."""
        reply = QMessageBox.question(
            self,
            "Edit Improvement Instructions?",
            "Editing these instructions will affect how all future template improvements are generated.\n\nAre you sure you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            dialog = ImprovementPromptEditor(self)
            dialog.exec()
    
    def _new_template(self):
        """Create a new template."""
        config = get_config()
        dialog = TemplateEditor(parent=self, last_folder=config.ui.last_editor_folder)
        dialog.template_saved.connect(self._on_template_saved)
        dialog.exec()
        # Save the last used folder
        config.ui.last_editor_folder = dialog.folder_combo.currentData() or ""
        save_config(config)
    
    def _edit_template(self, template: Optional[Template] = None):
        """Edit the given or currently selected template."""
        target = template or self.current_template
        if not target:
            return

        dialog = TemplateEditor(target, parent=self)
        dialog.template_saved.connect(self._on_template_saved)
        dialog.exec()
    
    def _improve_template(self, template: Optional[Template] = None):
        """Improve the selected template using AI based on user feedback.

        Prompts user for feedback first, then generates improvements.
        """
        target = template or self.current_template
        if not target:
            return
        
        # Prompt for feedback first
        feedback, ok = QInputDialog.getMultiLineText(
            self,
            "Improve Template",
            "How could this template be better?\n(What isn't working or should be different?)",
            "",
        )
        
        if not ok:
            return  # User cancelled
        
        # Check LLM status
        server = get_llm_server()
        if not server.is_running():
            reply = QMessageBox.question(
                self,
                "LLM Not Running",
                "The LLM server is not running. Would you like to start it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                success, message = server.start()
                if not success:
                    QMessageBox.critical(self, "Error", message)
                    return
                self.llm_toolbar.check_status()
            else:
                return
        
        # Show improvement dialog with feedback
        dialog = TemplateImproveDialog(
            target,
            initial_feedback=feedback.strip() if feedback else "",
            parent=self
        )
        dialog.changes_applied.connect(self._on_improvement_applied)
        dialog.exec()
    
    def _on_improvement_applied(self, new_content: str):
        """Handle when user applies improved template content.
        
        Creates a version snapshot of the current template before saving changes.
        """
        if not self.current_template:
            return
        
        # Create a version snapshot before modifying
        manager = get_template_manager()
        manager.create_version(self.current_template, note="Before AI improvement")
        
        # Update template with improved content
        self.current_template.content = new_content
        self.current_template.refinements = []  # Clear refinements since they've been addressed
        
        # Save the updated template
        folder = manager.get_template_folder(self.current_template)
        if manager.save_to_folder(self.current_template, folder):
            self.status_bar.showMessage("Template improved and saved", 3000)
            self.template_tree_widget.refresh()
            self.variable_form.set_template(self.current_template)
        else:
            QMessageBox.critical(self, "Error", "Failed to save improved template")

    def _show_version_history(self, template: Optional[Template] = None):
        """Show version history dialog for the given or current template."""
        target = template or self.current_template
        if not target:
            return

        manager = get_template_manager()
        versions = manager.list_versions(target)
        
        if not versions:
            QMessageBox.information(
                self,
                "No Version History",
                "This template has no version history to revert to."
            )
            return
        
        # Build list of version options
        items = []
        for v in reversed(versions):  # Most recent first
            timestamp = v.timestamp[:19].replace("T", " ") if v.timestamp else "Unknown"
            label = f"v{v.version}"
            if v.version == 1:
                label += " (Original)"
            if v.note:
                label += f" - {v.note}"
            label += f" [{timestamp}]"
            items.append(label)
        
        item, ok = QInputDialog.getItem(
            self,
            "Revert Template",
            f"Select a version to revert '{target.name}' to:",
            items,
            0,  # Default to most recent
            False,  # Not editable
        )
        
        if not ok or not item:
            return
        
        # Extract version number from selected item
        selected_idx = items.index(item)
        selected_version = versions[-(selected_idx + 1)]  # Reverse index since list is reversed
        
        # Confirm revert
        reply = QMessageBox.question(
            self,
            "Confirm Revert",
            f"Revert to version {selected_version.version}?\n\n"
            f"This will replace the current template content with the selected version.\n"
            f"A backup of the current state will be saved.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Perform revert
        restored = manager.restore_version(
            target,
            selected_version.version,
            create_backup=True
        )

        if restored:
            self.current_template = restored
            self.template_tree_widget.refresh()
            self.variable_form.set_template(self.current_template)
            self.status_bar.showMessage(
                f"Reverted to version {selected_version.version}", 3000
            )
        else:
            QMessageBox.critical(self, "Error", "Failed to revert template")

    def _on_template_saved(self, template: Template):
        """Handle template saved signal."""
        self.template_tree_widget.load_templates()
        self.template_tree_widget.select_template_by_name(template.name)

    def _generate(self):
        """Generate output using the LLM."""
        if not self.current_template:
            return
        
        # Get variable values
        values = self.variable_form.get_values()
        
        # Render the prompt
        prompt = self.current_template.render(values)
        
        # Check LLM status
        server = get_llm_server()
        if not server.is_running():
            reply = QMessageBox.question(
                self,
                "LLM Not Running",
                "The LLM server is not running. Would you like to start it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                success, message = server.start()
                if not success:
                    QMessageBox.critical(self, "Error", message)
                    return
                self.llm_toolbar.check_status()
            else:
                return
        
        # Disable generate button during generation
        self.variable_form.generate_btn.setEnabled(False)
        self.variable_form.generate_btn.setText("Generating...")
        self.output_pane.clear()
        self.output_pane.set_streaming(True)
        
        # Store prompt for reference
        self._last_prompt = prompt
        self._last_output = None
        
        # Start generation in background
        self.worker = GenerationWorker(prompt, stream=True)
        self.worker.token_received.connect(self.output_pane.append_text)
        self.worker.finished.connect(self._on_generation_finished)
        self.worker.error.connect(self._on_generation_error)
        self.worker.waiting_for_server.connect(self.output_pane.set_waiting_message)
        self.worker.waiting_for_server.connect(self._on_waiting_for_server_status)
        self.worker.start()
    
    def _render_template_only(self):
        """Render template with variable substitution only (no AI)."""
        if not self.current_template:
            return
        
        values = self.variable_form.get_values()
        rendered = self.current_template.render(values)
        self.output_pane.set_text(rendered)
        
        QApplication.clipboard().setText(rendered)
        self.status_bar.showMessage("Template copied to clipboard", 3000)
    
    def _on_generation_finished(self, result: str):
        """Handle generation complete."""
        self.variable_form.generate_btn.setEnabled(True)
        self.variable_form.generate_btn.setText("Render with AI (Ctrl+G)")
        self.output_pane.set_streaming(False)
        self.status_bar.showMessage("Generation complete", 3000)
        self._last_output = result
    
    def _on_generation_error(self, error: str):
        """Handle generation error."""
        self.variable_form.generate_btn.setEnabled(True)
        self.variable_form.generate_btn.setText("Render with AI (Ctrl+G)")
        self.output_pane.set_streaming(False)
        QMessageBox.critical(self, "Generation Error", error)
    
    def _on_waiting_for_server_status(self, attempt: int, max_attempts: int):
        """Update status bar when waiting for server."""
        self.status_bar.showMessage(
            f"Waiting for model to start (attempt {attempt}/{max_attempts})...", 
            5000
        )
    
    def _stop_generation(self):
        """Stop the current generation."""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.status_bar.showMessage("Generation stopped", 3000)


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
