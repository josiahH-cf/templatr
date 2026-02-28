"""Prompt editor dialogs for template generation and improvement."""

from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)

from templatr.core.meta_templates import (
    get_bundled_meta_template_content,
    load_meta_template,
    save_meta_template,
)


class _BasePromptEditor(QDialog):
    """Reusable editor for meta-template prompt instructions."""

    def __init__(
        self,
        *,
        window_title: str,
        instructions_text: str,
        template_name: str,
        reset_tooltip: str,
        required_placeholder: str,
        missing_placeholder_message: str,
        parent=None,
    ):
        super().__init__(parent)
        self.template_name = template_name
        self.required_placeholder = required_placeholder
        self.missing_placeholder_message = missing_placeholder_message

        self.setWindowTitle(window_title)
        self.setMinimumSize(700, 500)

        self._setup_ui(instructions_text, reset_tooltip)

    def _setup_ui(self, instructions_text: str, reset_tooltip: str) -> None:
        layout = QVBoxLayout(self)

        instructions = QLabel(instructions_text)
        instructions.setStyleSheet("color: #888; margin-bottom: 10px;")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        self.prompt_edit = QPlainTextEdit()
        template = load_meta_template(self.template_name)
        self.prompt_edit.setPlainText(template.content if template else "")
        self.prompt_edit.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self.prompt_edit)

        self.warning_label = QLabel("")
        self.warning_label.setStyleSheet("color: #ff6b6b;")
        self.warning_label.setVisible(False)
        layout.addWidget(self.warning_label)

        button_layout = QHBoxLayout()

        reset_btn = QPushButton("Reset to Default")
        reset_btn.setObjectName("secondary")
        reset_btn.setToolTip(reset_tooltip)
        default_content = get_bundled_meta_template_content(self.template_name) or ""
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

    def _save(self) -> None:
        """Save the prompt and close dialog."""
        prompt = self.prompt_edit.toPlainText()

        if self.required_placeholder not in prompt:
            self.warning_label.setText(
                f"Warning: Prompt must contain {self.required_placeholder} placeholder"
            )
            self.warning_label.setVisible(True)
            reply = QMessageBox.warning(
                self,
                "Missing Placeholder",
                self.missing_placeholder_message,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        if save_meta_template(self.template_name, prompt):
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "Failed to save prompt")


class GenerationPromptEditor(_BasePromptEditor):
    """Dialog for editing template-generation instructions."""

    def __init__(self, parent=None):
        super().__init__(
            window_title="Edit Template Generation Instructions",
            instructions_text=(
                "Customize the instructions used when generating new templates.\n"
                "Available placeholders: {{description}}, {{variables}}"
            ),
            template_name="template_generator",
            reset_tooltip="Restore the default generation instructions",
            required_placeholder="{{description}}",
            missing_placeholder_message=(
                "The prompt is missing the {{description}} placeholder.\n\n"
                "Without this, the AI won't receive the user's description.\n\n"
                "Save anyway?"
            ),
            parent=parent,
        )


class ImprovementPromptEditor(_BasePromptEditor):
    """Dialog for editing template-improvement instructions."""

    def __init__(self, parent=None):
        super().__init__(
            window_title="Edit Template Improvement Instructions",
            instructions_text=(
                "Customize the instructions used when improving existing templates.\n"
                "Available placeholders: {{template_content}}, {{refinements}}, {{additional_notes}}"
            ),
            template_name="template_improver",
            reset_tooltip="Restore the default improvement instructions",
            required_placeholder="{{template_content}}",
            missing_placeholder_message=(
                "The prompt is missing the {{template_content}} placeholder.\n\n"
                "Without this, the AI won't receive the template to improve.\n\n"
                "Save anyway?"
            ),
            parent=parent,
        )
