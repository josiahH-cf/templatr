"""Template generation dialog for Automatr.

Workflow for AI-powered template generation:
1. User provides description of what the template should do
2. User optionally defines expected variables
3. AI generates a draft template
4. User reviews/edits the draft before applying
5. Generated content populates the template editor
"""

import re
from typing import List, Optional, Set

from PyQt6.QtCore import Qt, QThread, pyqtSignal
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

from automatr.core.feedback import build_generation_prompt
from automatr.integrations.llm import get_llm_client, get_llm_server


class GenerationWorker(QThread):
    """Background worker for LLM-based template generation with retry on server startup."""

    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    waiting_for_server = pyqtSignal(int, int)

    MAX_RETRY_ATTEMPTS = 3
    RETRY_DELAY_SECONDS = 3.0

    def __init__(self, prompt: str):
        super().__init__()
        self.prompt = prompt
        self._stopped = False

    def stop(self):
        """Request generation to stop."""
        self._stopped = True

    def _is_connection_error(self, error: Exception) -> bool:
        """Check if error is a connection issue (server not ready)."""
        error_str = str(error).lower()
        return (
            isinstance(error, ConnectionError)
            or "cannot connect" in error_str
            or "connection refused" in error_str
            or "connection error" in error_str
        )

    def _extract_template_content(self, text: str) -> str:
        """Extract template content from LLM response.

        Looks for content within <generated_template> tags first,
        falls back to full text with markdown cleanup.

        Args:
            text: Raw LLM response text.

        Returns:
            Extracted template content.
        """
        import re

        # Try to extract from <generated_template> tags
        match = re.search(r"<generated_template>(.*?)</generated_template>", text, re.DOTALL)
        if match:
            return match.group(1).strip()

        # Fallback: clean up markdown and return
        result = text.strip()
        if result.startswith("```"):
            lines = result.split("\n")
            lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            result = "\n".join(lines)

        return result

    def run(self):
        import time
        client = get_llm_client()
        last_error = None

        for attempt in range(1, self.MAX_RETRY_ATTEMPTS + 1):
            if self._stopped:
                return

            try:
                result = client.generate(self.prompt)
                # Extract template content from response
                result = self._extract_template_content(result)
                self.finished.emit(result)
                return

            except Exception as e:
                if self._stopped:
                    return

                last_error = e

                if self._is_connection_error(e) and attempt < self.MAX_RETRY_ATTEMPTS:
                    self.waiting_for_server.emit(attempt, self.MAX_RETRY_ATTEMPTS)
                    time.sleep(self.RETRY_DELAY_SECONDS)
                else:
                    break

        if last_error and not self._stopped:
            self.error.emit(str(last_error))


def extract_variables_from_content(content: str) -> Set[str]:
    """Extract variable names from template content.

    Finds all {{variable_name}} patterns and returns the variable names.
    """
    pattern = r"\{\{\s*(\w+)\s*\}\}"
    matches = re.findall(pattern, content)
    return set(matches)


class TemplateGenerateDialog(QDialog):
    """Dialog for generating new templates using AI.

    Workflow:
    1. User describes what the template should do
    2. User optionally adds expected variables
    3. AI generates a draft template
    4. User can edit the draft
    5. User applies to populate the template editor
    """

    # Emitted when user wants to apply the generated content
    content_generated = pyqtSignal(str, list)  # (content, variables)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker: Optional[GenerationWorker] = None
        self.expected_variables: List[str] = []

        self.setWindowTitle("Generate Template with AI")
        self.setMinimumSize(700, 550)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Instructions
        instructions = QLabel(
            "Describe what your template should do. Optionally add variables that should be included."
        )
        instructions.setStyleSheet("color: #888; margin-bottom: 5px;")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Main splitter
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Top section: Description + Variables
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)

        # Description input
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

        # Variables section
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

        # Generate button
        self.generate_btn = QPushButton("Generate Template")
        self.generate_btn.clicked.connect(self._generate)
        top_layout.addWidget(self.generate_btn)

        splitter.addWidget(top_widget)

        # Bottom section: Preview
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

        # Set splitter sizes
        splitter.setSizes([250, 300])
        layout.addWidget(splitter)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #888;")
        layout.addWidget(self.status_label)

        # Buttons
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

    def _add_variable(self):
        """Add a variable to the list."""
        var_name = self.var_input.text().strip()
        if not var_name:
            return

        # Sanitize: remove special chars, lowercase
        var_name = re.sub(r"[^a-zA-Z0-9_]", "", var_name).lower()
        if not var_name:
            return

        if var_name not in self.expected_variables:
            self.expected_variables.append(var_name)
            self.var_list.addItem(f"{{{{{var_name}}}}}")

        self.var_input.clear()

    def _remove_variable(self):
        """Remove selected variable from the list."""
        row = self.var_list.currentRow()
        if row >= 0 and row < len(self.expected_variables):
            del self.expected_variables[row]
            self.var_list.takeItem(row)

    def _generate(self):
        """Generate template using AI."""
        description = self.description_edit.toPlainText().strip()
        if not description:
            QMessageBox.warning(self, "Missing Description", "Please describe what the template should do.")
            return

        # Check LLM status first
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

    def _on_generation_finished(self, result: str):
        """Handle successful generation."""
        self.preview_edit.setPlainText(result)
        self.status_label.setText("Review and edit the generated template, then apply")
        self.apply_btn.setEnabled(True)
        self.generate_btn.setEnabled(True)
        self.cancel_btn.setText("Cancel")
        self._check_variable_warnings(result)

    def _on_generation_error(self, error: str):
        """Handle generation error."""
        self.status_label.setText(f"Error: {error}")
        self.generate_btn.setEnabled(True)
        self.cancel_btn.setText("Cancel")
        QMessageBox.critical(self, "Generation Error", error)

    def _on_waiting_for_server(self, attempt: int, max_attempts: int):
        """Handle waiting for server to become ready."""
        self.status_label.setText(f"Model starting... (attempt {attempt}/{max_attempts})")

    def _on_preview_changed(self):
        """Handle changes to the preview text."""
        content = self.preview_edit.toPlainText().strip()
        self.apply_btn.setEnabled(bool(content))
        if content:
            self._check_variable_warnings(content)

    def _check_variable_warnings(self, content: str):
        """Check if expected variables are present and warn if not."""
        if not self.expected_variables:
            self.warning_label.setVisible(False)
            return

        found_vars = extract_variables_from_content(content)
        expected_set = set(self.expected_variables)

        missing = expected_set - found_vars
        extra = found_vars - expected_set

        warnings = []
        if missing:
            warnings.append(f"Missing: {', '.join(sorted(missing))}")
        if extra and self.expected_variables:  # Only warn about extras if user defined some
            warnings.append(f"Extra: {', '.join(sorted(extra))}")

        if warnings:
            self.warning_label.setText("⚠️ " + "; ".join(warnings))
            self.warning_label.setVisible(True)
        else:
            self.warning_label.setVisible(False)

    def _on_cancel(self):
        """Handle cancel button."""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.status_label.setText("Canceled")
        self.reject()

    def _apply(self):
        """Apply the generated content."""
        content = self.preview_edit.toPlainText().strip()
        if not content:
            return

        # Extract variables from the final content
        found_vars = list(extract_variables_from_content(content))

        self.content_generated.emit(content, found_vars)
        self.accept()


class GenerationPromptEditor(QDialog):
    """Dialog for editing the system prompt used for template generation."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Template Generation Instructions")
        self.setMinimumSize(700, 500)
        self._setup_ui()

    def _setup_ui(self):
        from automatr.core.templates import (
            get_bundled_meta_template_content,
            load_meta_template,
        )

        layout = QVBoxLayout(self)

        # Instructions
        instructions = QLabel(
            "Customize the instructions used when generating new templates.\n"
            "Available placeholders: {{description}}, {{variables}}"
        )
        instructions.setStyleSheet("color: #888; margin-bottom: 10px;")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Text editor
        self.prompt_edit = QPlainTextEdit()
        template = load_meta_template("template_generator")
        self.prompt_edit.setPlainText(template.content if template else "")
        self.prompt_edit.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self.prompt_edit)

        # Validation warning
        self.warning_label = QLabel("")
        self.warning_label.setStyleSheet("color: #ff6b6b;")
        self.warning_label.setVisible(False)
        layout.addWidget(self.warning_label)

        # Buttons
        button_layout = QHBoxLayout()

        reset_btn = QPushButton("Reset to Default")
        reset_btn.setObjectName("secondary")
        reset_btn.setToolTip("Restore the default generation instructions")
        default_content = get_bundled_meta_template_content("template_generator") or ""
        reset_btn.clicked.connect(lambda: self.prompt_edit.setPlainText(default_content))
        button_layout.addWidget(reset_btn)

        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondary")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._save)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

    def _save(self):
        """Save the prompt and close dialog."""
        from automatr.core.templates import save_meta_template

        prompt = self.prompt_edit.toPlainText()

        # Validate required placeholder
        if "{{description}}" not in prompt:
            self.warning_label.setText("Warning: Prompt must contain {{description}} placeholder")
            self.warning_label.setVisible(True)
            reply = QMessageBox.warning(
                self,
                "Missing Placeholder",
                "The prompt is missing the {{description}} placeholder.\n\n"
                "Without this, the AI won't receive the user's description.\n\n"
                "Save anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        if save_meta_template("template_generator", prompt):
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "Failed to save prompt")


class ImprovementPromptEditor(QDialog):
    """Dialog for editing the system prompt used for template improvements.

    This is a standalone version that can be opened from the File menu.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Template Improvement Instructions")
        self.setMinimumSize(700, 500)
        self._setup_ui()

    def _setup_ui(self):
        from automatr.core.templates import (
            get_bundled_meta_template_content,
            load_meta_template,
        )

        layout = QVBoxLayout(self)

        # Instructions
        instructions = QLabel(
            "Customize the instructions used when improving existing templates.\n"
            "Available placeholders: {{template_content}}, {{refinements}}, {{additional_notes}}"
        )
        instructions.setStyleSheet("color: #888; margin-bottom: 10px;")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Text editor
        self.prompt_edit = QPlainTextEdit()
        template = load_meta_template("template_improver")
        self.prompt_edit.setPlainText(template.content if template else "")
        self.prompt_edit.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self.prompt_edit)

        # Validation warning
        self.warning_label = QLabel("")
        self.warning_label.setStyleSheet("color: #ff6b6b;")
        self.warning_label.setVisible(False)
        layout.addWidget(self.warning_label)

        # Buttons
        button_layout = QHBoxLayout()

        reset_btn = QPushButton("Reset to Default")
        reset_btn.setObjectName("secondary")
        reset_btn.setToolTip("Restore the default improvement instructions")
        default_content = get_bundled_meta_template_content("template_improver") or ""
        reset_btn.clicked.connect(lambda: self.prompt_edit.setPlainText(default_content))
        button_layout.addWidget(reset_btn)

        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondary")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._save)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

    def _save(self):
        """Save the prompt and close dialog."""
        from automatr.core.templates import save_meta_template

        prompt = self.prompt_edit.toPlainText()

        # Validate required placeholder
        if "{{template_content}}" not in prompt:
            self.warning_label.setText("Warning: Prompt must contain {{template_content}} placeholder")
            self.warning_label.setVisible(True)
            reply = QMessageBox.warning(
                self,
                "Missing Placeholder",
                "The prompt is missing the {{template_content}} placeholder.\n\n"
                "Without this, the AI won't receive the template to improve.\n\n"
                "Save anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        if save_meta_template("template_improver", prompt):
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "Failed to save prompt")
