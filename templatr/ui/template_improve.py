"""Template improvement dialog for Templatr."""

from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from templatr.core.feedback import build_improvement_prompt
from templatr.core.templates import Template
from templatr.integrations.llm import get_llm_server
from templatr.ui.template_ai_workers import ImprovementWorker


class TemplateImproveDialog(QDialog):
    """Dialog for reviewing and applying template improvements."""

    changes_applied = pyqtSignal(str)

    def __init__(self, template: Template, initial_feedback: str = "", parent=None):
        super().__init__(parent)
        self.template = template
        self.original_content = template.content
        self.initial_feedback = initial_feedback
        self.improved_content: Optional[str] = None
        self.worker: Optional[ImprovementWorker] = None

        self.setWindowTitle(f"Improve Template: {template.name}")
        self.setMinimumSize(800, 600)
        self._setup_ui()

        self._generate_improvement(additional_notes=initial_feedback)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        if self.initial_feedback:
            feedback_label = QLabel(
                f"Improving based on: \"{self.initial_feedback[:100]}{'...' if len(self.initial_feedback) > 100 else ''}\""
            )
            feedback_label.setStyleSheet("color: #888; font-style: italic;")
            feedback_label.setWordWrap(True)
            layout.addWidget(feedback_label)
        elif self.template.refinements:
            refinements_label = QLabel(
                f"Improving based on {len(self.template.refinements)} accumulated feedback item(s)"
            )
            refinements_label.setStyleSheet("color: #888; font-style: italic;")
            layout.addWidget(refinements_label)
        else:
            no_refinements_label = QLabel(
                "No feedback provided. AI will suggest general improvements."
            )
            no_refinements_label.setStyleSheet("color: #888; font-style: italic;")
            layout.addWidget(no_refinements_label)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 5, 0)

        left_label = QLabel("Original Template")
        left_label.setStyleSheet("font-weight: bold;")
        left_layout.addWidget(left_label)

        self.original_text = QPlainTextEdit()
        self.original_text.setPlainText(self.original_content)
        self.original_text.setReadOnly(True)
        left_layout.addWidget(self.original_text)
        splitter.addWidget(left_widget)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(5, 0, 0, 0)

        right_header = QHBoxLayout()
        right_label = QLabel("Improved Template (Editable)")
        right_label.setStyleSheet("font-weight: bold;")
        right_header.addWidget(right_label)
        right_header.addStretch()

        edit_hint = QLabel("You can edit this before saving")
        edit_hint.setStyleSheet("color: #888; font-size: 11px;")
        right_header.addWidget(edit_hint)
        right_layout.addLayout(right_header)

        self.improved_text = QPlainTextEdit()
        self.improved_text.setPlaceholderText("Generating improvements...")
        self.improved_text.setReadOnly(False)
        right_layout.addWidget(self.improved_text)
        splitter.addWidget(right_widget)

        splitter.setSizes([400, 400])
        layout.addWidget(splitter)

        self.status_label = QLabel("Generating improvements...")
        self.status_label.setStyleSheet("color: #888;")
        layout.addWidget(self.status_label)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.discard_btn = QPushButton("Discard")
        self.discard_btn.setObjectName("secondary")
        self.discard_btn.clicked.connect(self._on_discard_clicked)
        button_layout.addWidget(self.discard_btn)

        self.regenerate_btn = QPushButton("Regenerate with Notes")
        self.regenerate_btn.setObjectName("secondary")
        self.regenerate_btn.setEnabled(False)
        self.regenerate_btn.setToolTip("Re-run AI improvement with additional guidance")
        self.regenerate_btn.clicked.connect(self._regenerate_with_notes)
        button_layout.addWidget(self.regenerate_btn)

        self.apply_btn = QPushButton("Save Changes")
        self.apply_btn.setEnabled(False)
        self.apply_btn.setToolTip("Save your edits as the new template version")
        self.apply_btn.clicked.connect(self._apply_changes)
        button_layout.addWidget(self.apply_btn)

        layout.addLayout(button_layout)

    def _generate_improvement(self, additional_notes: str = "") -> None:
        """Generate improved template content via the LLM server."""
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
                    self.regenerate_btn.setEnabled(True)
                    return
            else:
                self.status_label.setText("Server not started")
                self.regenerate_btn.setEnabled(True)
                return

        self.status_label.setText("Generating improvements...")
        self.improved_text.setPlainText("")
        self.apply_btn.setEnabled(False)
        self.regenerate_btn.setEnabled(False)
        self.discard_btn.setText("Cancel")

        prompt = build_improvement_prompt(
            template_content=self.original_content,
            refinements=self.template.refinements,
            additional_notes=additional_notes,
        )

        self.worker = ImprovementWorker(prompt)
        self.worker.finished.connect(self._on_improvement_finished)
        self.worker.error.connect(self._on_improvement_error)
        self.worker.waiting_for_server.connect(self._on_waiting_for_server)
        self.worker.start()

    def _on_improvement_finished(self, result: str) -> None:
        """Handle successful generation of improved content."""
        self.improved_content = result
        self.improved_text.setPlainText(result)
        self.status_label.setText("Review and edit the improvements, then save")
        self.apply_btn.setEnabled(True)
        self.regenerate_btn.setEnabled(True)
        self.discard_btn.setText("Discard")

    def _on_improvement_error(self, error: str) -> None:
        """Handle improvement-generation errors."""
        self.status_label.setText(f"Error: {error}")
        self.regenerate_btn.setEnabled(True)
        self.discard_btn.setText("Discard")
        QMessageBox.critical(self, "Generation Error", error)

    def _on_waiting_for_server(self, attempt: int, max_attempts: int) -> None:
        """Update status while waiting for model/server startup."""
        self.status_label.setText(
            f"Model starting... (attempt {attempt}/{max_attempts})"
        )

    def _on_discard_clicked(self) -> None:
        """Discard current dialog changes or cancel active generation."""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.status_label.setText("Canceled")
        self.reject()

    def _regenerate_with_notes(self) -> None:
        """Request additional notes and regenerate improvements."""
        notes, ok = QInputDialog.getMultiLineText(
            self,
            "Additional Notes",
            "What else should be changed?",
            "",
        )

        if ok and notes.strip():
            self._generate_improvement(additional_notes=notes.strip())

    def _apply_changes(self) -> None:
        """Apply user-edited improved template content."""
        edited_content = self.improved_text.toPlainText().strip()
        if edited_content:
            self.changes_applied.emit(edited_content)
            self.accept()
