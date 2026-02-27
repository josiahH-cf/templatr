"""Mixin providing LLM generation orchestration for MainWindow."""


from PyQt6.QtWidgets import QApplication, QMessageBox

from templatr.integrations.llm import get_llm_server
from templatr.ui.workers import GenerationWorker


class GenerationMixin:
    """Generation orchestration: run LLM, render-only, handle results.

    Mixed into MainWindow (must inherit QMainWindow).

    Expects self to provide:
        current_template (Optional[Template]): Currently selected template (read).
        variable_form (VariableFormWidget): Variable input form with
            .get_values() and .generate_btn (QAbstractButton) for enable/text.
        output_pane (OutputPaneWidget): Output display (.clear(), .set_text(),
            .set_streaming(), .append_text(), .set_waiting_message()).
        status_bar (QStatusBar): Status bar for messages (.showMessage()).
        llm_toolbar (LLMToolbar): Server controls (.check_status()).
        worker (Optional[GenerationWorker]): Background worker (read/write).
        _last_prompt (Optional[str]): Last rendered prompt (write).
        _last_output (Optional[str]): Last generated output (write).
    """

    def _generate(self):
        """Generate output using the LLM."""
        if not self.current_template:
            return

        values = self.variable_form.get_values()
        prompt = self.current_template.render(values)

        server = get_llm_server()
        if not server.is_running():
            reply = QMessageBox.question(
                self, "LLM Not Running",
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

        self.variable_form.generate_btn.setEnabled(False)
        self.variable_form.generate_btn.setText("Generating...")
        self.output_pane.clear()
        self.output_pane.set_streaming(True)

        self._last_prompt = prompt
        self._last_output = None

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
            5000,
        )

    def _stop_generation(self):
        """Stop the current generation."""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.status_bar.showMessage("Generation stopped", 3000)
