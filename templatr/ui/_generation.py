"""Mixin providing LLM generation orchestration for MainWindow."""

from PyQt6.QtWidgets import QApplication, QMessageBox

from templatr.integrations.llm import get_llm_server
from templatr.ui.workers import GenerationWorker


class GenerationMixin:
    """Generation orchestration: run LLM, stream tokens to chat, handle results.

    Mixed into MainWindow (must inherit QMainWindow).

    Expects self to provide:
        current_template (Optional[Template]): Currently selected template (read).
        chat_widget (ChatWidget): Chat display (.add_user_message(), .add_ai_bubble(),
            .append_token_to_last_ai(), .finalize_last_ai(), .show_error_bubble(),
            .add_system_message()).
        slash_input (SlashInputWidget): Input bar (.set_generating(),
            .set_waiting_message()).
        status_bar (QStatusBar): Status bar for messages (.showMessage()).
        llm_toolbar (LLMToolbar): Server controls (.check_status()).
        worker (Optional[GenerationWorker]): Background worker (read/write).
        _last_prompt (Optional[str]): Full assembled prompt sent to the model (write).
        _last_original_prompt (Optional[str]): Unassembled user message (write).
        _last_output (Optional[str]): Last generated output (write).
        _active_ai_bubble (Optional[MessageBubble]): Current streaming bubble (write).
        conversation_memory (ConversationMemory): Optional session memory (read/write).
    """

    def _generate(self, prompt: str):
        """Generate output using the LLM for the given rendered prompt.

        Args:
            prompt: The fully-rendered prompt string to send to the LLM.
        """
        if not prompt:
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
                success, message = server.start()
                if not success:
                    QMessageBox.critical(self, "Error", message)
                    return
                self.llm_toolbar.check_status()
            else:
                return

        self.slash_input.set_generating(True)
        self.chat_widget.add_user_message(prompt)

        # Assemble multi-turn context if memory is available.
        memory = getattr(self, "conversation_memory", None)
        if memory is not None:
            assembled, truncated = memory.assemble_prompt(prompt)
            if truncated:
                self.chat_widget.add_system_message(
                    "_Some earlier turns were dropped to fit the context limit._"
                )
        else:
            assembled = prompt

        self._active_ai_bubble = self.chat_widget.add_ai_bubble()
        self._last_original_prompt = prompt
        self._last_prompt = assembled  # full context recorded in history and used by /compare
        self._last_output = None

        self.worker = GenerationWorker(assembled, stream=True)
        self.worker.token_received.connect(self._on_token_received)
        self.worker.finished.connect(self._on_generation_finished)
        self.worker.error.connect(self._on_generation_error)
        self.worker.waiting_for_server.connect(self.slash_input.set_waiting_message)
        self.worker.waiting_for_server.connect(self._on_waiting_for_server_status)
        self.worker.start()

    def _on_token_received(self, token: str):
        """Append a streaming token to the active AI bubble.

        Args:
            token: A single token from the LLM stream.
        """
        self.chat_widget.append_token_to_last_ai(token)

    def _render_template_only(self):
        """Render template with variable substitution only (no AI) and copy."""
        if not self.current_template:
            return
        rendered = self.current_template.render({})
        QApplication.clipboard().setText(rendered)
        self.status_bar.showMessage("Template copied to clipboard", 3000)

    def _on_generation_finished(self, result: str):
        """Handle generation complete by finalizing the AI bubble.

        Args:
            result: The complete generated text.
        """
        self.slash_input.set_generating(False)
        self.chat_widget.finalize_last_ai(result)
        self._active_ai_bubble = None
        self._last_output = result
        if hasattr(self, "_record_generation_history"):
            self._record_generation_history(self._last_prompt or "", result)
        # Record the completed turn so subsequent messages include this exchange.
        memory = getattr(self, "conversation_memory", None)
        if memory is not None:
            original = getattr(self, "_last_original_prompt", None) or (self._last_prompt or "")
            memory.add_turn(original, result)
        self.status_bar.showMessage("Generation complete", 3000)

    def _on_generation_error(self, error: str):
        """Handle generation error by showing an error bubble in the chat.

        Args:
            error: Human-readable error message.
        """
        self.slash_input.set_generating(False)
        self.chat_widget.show_error_bubble(error)
        self._active_ai_bubble = None
        self.status_bar.showMessage("Generation failed", 5000)

    def _on_waiting_for_server_status(self, attempt: int, max_attempts: int):
        """Update status bar when waiting for server.

        Args:
            attempt: Current retry attempt (1-based).
            max_attempts: Total retries planned.
        """
        self.status_bar.showMessage(
            f"Waiting for model to start (attempt {attempt}/{max_attempts})...",
            5000,
        )

    def _retry_generation(self):
        """Re-submit the last generation request.

        Uses the original user message so that conversation memory is
        re-assembled correctly instead of re-sending the already-assembled
        multi-turn context.
        """
        original = getattr(self, "_last_original_prompt", None) or self._last_prompt
        if original:
            self._generate(original)

    def _stop_generation(self):
        """Stop the current generation."""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.slash_input.set_generating(False)
            self.status_bar.showMessage("Generation stopped", 3000)
