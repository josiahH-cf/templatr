"""Background worker threads for long-running operations."""

import logging
import shutil
import time
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from templatr.integrations.llm import get_llm_client, validate_gguf

logger = logging.getLogger(__name__)


# Map common exception types to user-friendly messages
_ERROR_MESSAGES = {
    ConnectionRefusedError: (
        "The LLM server isn't running.\n\n"
        "Start it from the toolbar (LLM → Start Server)."
    ),
    ConnectionError: (
        "Cannot connect to the LLM server.\n\n"
        "Start it from the toolbar (LLM → Start Server)."
    ),
    TimeoutError: (
        "The request timed out.\n\n"
        "The model may still be loading, or the prompt is too long. "
        "Try again in a moment."
    ),
}


def format_error_message(error: Exception) -> str:
    """Convert an exception to a human-readable error message.

    Maps known exception types to helpful, actionable messages.
    Falls back to the exception's string representation for unknown types.

    Args:
        error: The exception to format.

    Returns:
        A user-facing error message string.
    """
    # Check exact type first, then base classes
    for exc_type, message in _ERROR_MESSAGES.items():
        if isinstance(error, exc_type):
            return message

    # RuntimeError often already has a user-facing message from LLMClient
    if isinstance(error, RuntimeError):
        return str(error)

    # Generic fallback
    return (
        f"An unexpected error occurred: {type(error).__name__}\n\n"
        f"{error}"
    )



class GenerationWorker(QThread):
    """Background worker for LLM generation with retry on server startup."""

    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    token_received = pyqtSignal(str)
    waiting_for_server = pyqtSignal(int, int)

    MAX_RETRY_ATTEMPTS = 3
    RETRY_DELAYS = [1.0, 2.0, 4.0]

    def __init__(self, prompt: str, stream: bool = True):
        super().__init__()
        self.prompt = prompt
        self.stream = stream
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

    def run(self):
        """Execute the generation with exponential backoff on connection errors.

        Retries up to MAX_RETRY_ATTEMPTS times with delays from RETRY_DELAYS
        (1s, 2s, 4s) on connection errors. Emits human-readable error messages.
        """
        client = get_llm_client()
        last_error = None

        for attempt in range(1, self.MAX_RETRY_ATTEMPTS + 1):
            if self._stopped:
                return
            try:
                if self.stream:
                    result = []
                    for token in client.generate_stream(self.prompt):
                        if self._stopped:
                            break
                        result.append(token)
                        self.token_received.emit(token)
                    self.finished.emit("".join(result))
                else:
                    result = client.generate(self.prompt)
                    self.finished.emit(result)
                return
            except Exception as e:
                if self._stopped:
                    return
                last_error = e
                if self._is_connection_error(e) and attempt < self.MAX_RETRY_ATTEMPTS:
                    self.waiting_for_server.emit(attempt, self.MAX_RETRY_ATTEMPTS)
                    delay = self.RETRY_DELAYS[attempt - 1]
                    time.sleep(delay)
                else:
                    break

        if last_error and not self._stopped:
            logger.error(
                "LLM generation failed after %d attempt(s)",
                self.MAX_RETRY_ATTEMPTS,
                exc_info=last_error,
            )
            self.error.emit(format_error_message(last_error))


class ModelCopyWorker(QThread):
    """Background worker for copying model files with progress."""

    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(int)

    def __init__(self, source: Path, dest: Path):
        super().__init__()
        self.source = source
        self.dest = dest
        self._canceled = False

    def cancel(self):
        """Request cancellation of the copy operation."""
        self._canceled = True

    def run(self):
        """Copy the model file with progress reporting."""
        try:
            total_size = self.source.stat().st_size
            copied = 0
            chunk_size = 1024 * 1024

            with open(self.source, "rb") as src:
                with open(self.dest, "wb") as dst:
                    while True:
                        if self._canceled:
                            dst.close()
                            if self.dest.exists():
                                self.dest.unlink()
                            self.finished.emit(False, "Copy canceled")
                            return
                        chunk = src.read(chunk_size)
                        if not chunk:
                            break
                        dst.write(chunk)
                        copied += len(chunk)
                        percent = int((copied / total_size) * 100)
                        self.progress.emit(percent)

            shutil.copystat(self.source, self.dest)

            # Validate GGUF magic bytes after copy
            valid, validation_msg = validate_gguf(self.dest)
            if not valid:
                if self.dest.exists():
                    self.dest.unlink()
                self.finished.emit(False, validation_msg)
                return

            self.finished.emit(True, str(self.dest))

        except PermissionError:
            if self.dest.exists():
                self.dest.unlink()
            self.finished.emit(
                False, f"Permission denied writing to:\n{self.dest.parent}"
            )
        except OSError as e:
            if self.dest.exists():
                self.dest.unlink()
            self.finished.emit(False, f"Failed to copy file: {e}")
