"""Template generation dialog for Templatr."""

from typing import List, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from templatr.core.feedback import build_generation_prompt
from templatr.integrations.llm import get_llm_server
from templatr.ui.template_ai_workers import GenerationWorker
from templatr.ui.template_dialog_utils import (
    extract_variables_from_content,
    format_variable_warning,
    sanitize_variable_name,
)


class TemplateGenerateDialog(QDialog):
    """Dialog for generating new templates using AI."""

    content_generated = pyqtSignal(str, list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker: Optional[GenerationWorker] = None
        self.expected_variables: List[str] = []

        self.setWindowTitle("Generate Template with AI")
        self.setMinimumSize(700, 550)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        instructions = QLabel(
            "Describe what your template should do. Optionally add variables that should be included."
        )
        instructions.setStyleSheet("color: #888; margin-bottom: 5px;")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        splitter = QSplitter(Qt.Orientation.Vertical)

        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)

        desc_label = QLabel("Template Description:")
        desc_label.setStyleSheet("font-weight: bold;")
        top_layout.addWidget(desc_label)

        self.description_edit = QPlainTextEdit()
        self.description_edit.setPlaceholderText(
            "Example: A code review template that analyzes code for bugs, "
            "performance issues, and style problems. Should output findings "
            "in a structured format with severity levels."
        )
        self.description_edit.setMaximumHeight(100)
        top_layout.addWidget(self.description_edit)

        var_layout = QHBoxLayout()

        var_left = QVBoxLayout()
        var_label = QLabel("Expected Variables (optional):")
        var_label.setStyleSheet("font-weight: bold;")
        var_left.addWidget(var_label)

        var_hint = QLabel("These will appear as {{variable_name}} in the template")
        var_hint.setStyleSheet("color: #888; font-size: 11px;")
        var_left.addWidget(var_hint)

        self.var_list = QListWidget()
        self.var_list.setMaximumHeight(80)
        var_left.addWidget(self.var_list)
        var_layout.addLayout(var_left)

        var_buttons = QVBoxLayout()
        var_input_layout = QHBoxLayout()

        self.var_input = QLineEdit()
        self.var_input.setPlaceholderText("variable_name")
        self.var_input.returnPressed.connect(self._add_variable)
        var_input_layout.addWidget(self.var_input)

        add_var_btn = QPushButton("Add")
        add_var_btn.clicked.connect(self._add_variable)
        var_input_layout.addWidget(add_var_btn)
        var_buttons.addLayout(var_input_layout)

        remove_var_btn = QPushButton("Remove Selected")
        remove_var_btn.setObjectName("secondary")
        remove_var_btn.clicked.connect(self._remove_variable)
        var_buttons.addWidget(remove_var_btn)

        var_buttons.addStretch()
        var_layout.addLayout(var_buttons)

        top_layout.addLayout(var_layout)

        self.generate_btn = QPushButton("Generate Template")
        self.generate_btn.clicked.connect(self._generate)
        top_layout.addWidget(self.generate_btn)

        splitter.addWidget(top_widget)

        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)

        preview_header = QHBoxLayout()
        preview_label = QLabel("Generated Template (Editable):")
        preview_label.setStyleSheet("font-weight: bold;")
        preview_header.addWidget(preview_label)
        preview_header.addStretch()

        self.warning_label = QLabel("")
        self.warning_label.setStyleSheet("color: #ff9800;")
        self.warning_label.setVisible(False)
        preview_header.addWidget(self.warning_label)

        bottom_layout.addLayout(preview_header)

        self.preview_edit = QPlainTextEdit()
        self.preview_edit.setPlaceholderText("Generated template will appear here...")
        self.preview_edit.textChanged.connect(self._on_preview_changed)
        bottom_layout.addWidget(self.preview_edit)

        splitter.addWidget(bottom_widget)
        splitter.setSizes([250, 300])
        layout.addWidget(splitter)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #888;")
        layout.addWidget(self.status_label)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("secondary")
        self.cancel_btn.clicked.connect(self._on_cancel)
        button_layout.addWidget(self.cancel_btn)

        self.apply_btn = QPushButton("Apply to Template")
        self.apply_btn.setEnabled(False)
        self.apply_btn.setToolTip("Use this generated content in your template")
        self.apply_btn.clicked.connect(self._apply)
        button_layout.addWidget(self.apply_btn)

        layout.addLayout(button_layout)

    def _add_variable(self) -> None:
        """Add a sanitized variable name to the expected-variable list."""
        var_name = sanitize_variable_name(self.var_input.text().strip())
        if var_name and var_name not in self.expected_variables:
            self.expected_variables.append(var_name)
            self.var_list.addItem(f"{{{{{var_name}}}}}")
        self.var_input.clear()

    def _remove_variable(self) -> None:
        """Remove the selected expected variable."""
        row = self.var_list.currentRow()
        if 0 <= row < len(self.expected_variables):
            del self.expected_variables[row]
            self.var_list.takeItem(row)

    def _generate(self) -> None:
        """Generate template content using the configured LLM server."""
        description = self.description_edit.toPlainText().strip()
        if not description:
            QMessageBox.warning(
                self,
                "Missing Description",
                "Please describe what the template should do.",
            )
            return

        server = get_llm_server()
        if not server.is_running():
            reply = QMessageBox.question(
                self,
                "LLM Not Running",
                "The LLM server is not running. Would you like to start it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.status_label.setText("Starting LLM server...")
                success, message = server.start()
                if not success:
                    QMessageBox.critical(self, "Error", message)
                    self.status_label.setText("Server failed to start")
                    return
            else:
                self.status_label.setText("Server not started")
                return

        self.status_label.setText("Generating template...")
        self.preview_edit.setPlainText("")
        self.apply_btn.setEnabled(False)
        self.generate_btn.setEnabled(False)
        self.cancel_btn.setText("Cancel")
        self.warning_label.setVisible(False)

        prompt = build_generation_prompt(
            description=description,
            expected_variables=self.expected_variables,
        )

        self.worker = GenerationWorker(prompt)
        self.worker.finished.connect(self._on_generation_finished)
        self.worker.error.connect(self._on_generation_error)
        self.worker.waiting_for_server.connect(self._on_waiting_for_server)
        self.worker.start()

    def _on_generation_finished(self, result: str) -> None:
        """Handle successful generation."""
        self.preview_edit.setPlainText(result)
        self.status_label.setText("Review and edit the generated template, then apply")
        self.apply_btn.setEnabled(True)
        self.generate_btn.setEnabled(True)
        self.cancel_btn.setText("Cancel")
        self._update_warning(result)

    def _on_generation_error(self, error: str) -> None:
        """Handle generation error."""
        self.status_label.setText(f"Error: {error}")
        self.generate_btn.setEnabled(True)
        self.cancel_btn.setText("Cancel")
        QMessageBox.critical(self, "Generation Error", error)

    def _on_waiting_for_server(self, attempt: int, max_attempts: int) -> None:
        """Handle waiting for server startup."""
        self.status_label.setText(
            f"Model starting... (attempt {attempt}/{max_attempts})"
        )

    def _on_preview_changed(self) -> None:
        """Enable apply and refresh warnings after preview edits."""
        content = self.preview_edit.toPlainText().strip()
        self.apply_btn.setEnabled(bool(content))
        if content:
            self._update_warning(content)
        else:
            self.warning_label.setVisible(False)

    def _update_warning(self, content: str) -> None:
        """Refresh missing/extra variable warning text."""
        warning = format_variable_warning(self.expected_variables, content)
        if warning:
            self.warning_label.setText(f"Warning: {warning}")
            self.warning_label.setVisible(True)
        else:
            self.warning_label.setVisible(False)

    def _on_cancel(self) -> None:
        """Handle cancel button."""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.status_label.setText("Canceled")
        self.reject()

    def _apply(self) -> None:
        """Emit generated content and variables back to the editor workflow."""
        content = self.preview_edit.toPlainText().strip()
        if not content:
            return

        found_vars = list(extract_variables_from_content(content))
        self.content_generated.emit(content, found_vars)
        self.accept()
