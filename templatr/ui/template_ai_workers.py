"""Shared AI worker threads for template generation and improvement."""

import time

from PyQt6.QtCore import QThread, pyqtSignal

from templatr.integrations.llm import get_llm_client
from templatr.ui.template_dialog_utils import (
    extract_template_content,
    is_connection_error,
)


class _RetryingTemplateWorker(QThread):
    """Base worker that retries transient connection errors."""

    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    waiting_for_server = pyqtSignal(int, int)

    MAX_RETRY_ATTEMPTS = 3
    RETRY_DELAY_SECONDS = 3.0

    def __init__(self, prompt: str, *, tag_name: str):
        super().__init__()
        self.prompt = prompt
        self.tag_name = tag_name
        self._stopped = False

    def stop(self) -> None:
        """Request worker shutdown."""
        self._stopped = True

    def run(self) -> None:
        """Generate content with retry-on-startup semantics."""
        client = get_llm_client()
        last_error = None

        for attempt in range(1, self.MAX_RETRY_ATTEMPTS + 1):
            if self._stopped:
                return

            try:
                result = client.generate(self.prompt)
                result = extract_template_content(result, tag_name=self.tag_name)
                self.finished.emit(result)
                return
            except Exception as exc:
                if self._stopped:
                    return

                last_error = exc

                if is_connection_error(exc) and attempt < self.MAX_RETRY_ATTEMPTS:
                    self.waiting_for_server.emit(attempt, self.MAX_RETRY_ATTEMPTS)
                    time.sleep(self.RETRY_DELAY_SECONDS)
                else:
                    break

        if last_error and not self._stopped:
            self.error.emit(str(last_error))


class GenerationWorker(_RetryingTemplateWorker):
    """Background worker for LLM-based template generation."""

    def __init__(self, prompt: str):
        super().__init__(prompt, tag_name="generated_template")


class ImprovementWorker(_RetryingTemplateWorker):
    """Background worker for LLM-based template improvement."""

    def __init__(self, prompt: str):
        super().__init__(prompt, tag_name="improved_template")
