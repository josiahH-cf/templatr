"""Background worker threads for long-running operations."""

import json
import logging
import shutil
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QThread, pyqtSignal

from templatr.integrations.llm import get_llm_client, validate_gguf

logger = logging.getLogger(__name__)

# Required fields for a catalog entry to be accepted.
_CATALOG_REQUIRED_FIELDS = {
    "name",
    "description",
    "author",
    "tags",
    "download_url",
    "version",
}

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
    return f"An unexpected error occurred: {type(error).__name__}\n\n" f"{error}"


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


class ABTestWorker(QThread):
    """Background worker that runs a prompt N times against the active model.

    Iterations execute sequentially.  Each iteration records output, latency,
    and estimated token counts.
    """

    #: Emitted after each iteration: (current_iteration, total_iterations).
    progress = pyqtSignal(int, int)
    #: Emitted on completion with a list of per-iteration result dicts.
    finished = pyqtSignal(object)  # list[dict]
    #: Emitted with a human-readable message if any iteration fails.
    error = pyqtSignal(str)

    def __init__(self, prompt: str, iterations: int) -> None:
        """Initialise the A/B test worker.

        Args:
            prompt: The fully-rendered prompt to submit each iteration.
            iterations: Number of times to run the prompt (must be >= 2).
        """
        super().__init__()
        self.prompt = prompt
        self.iterations = iterations
        self._stopped = False

    def stop(self) -> None:
        """Request early cancellation — remaining iterations will not run."""
        self._stopped = True

    def run(self) -> None:
        """Run the prompt N times and emit results when done."""
        client = get_llm_client()
        results: list[dict] = []

        for i in range(1, self.iterations + 1):
            if self._stopped:
                return

            self.progress.emit(i, self.iterations)

            try:
                started_at = time.perf_counter()
                output = client.generate(self.prompt, stream=False)
                elapsed = time.perf_counter() - started_at
            except Exception as exc:  # noqa: BLE001
                logger.error("AB test iteration %d failed", i, exc_info=True)
                self.error.emit(format_error_message(exc))
                return

            results.append(
                {
                    "iteration": i,
                    "output": output,
                    "latency_seconds": elapsed,
                    "prompt_tokens_est": len(self.prompt.split()),
                    "output_tokens_est": len(output.split()),
                }
            )

        if not self._stopped:
            self.finished.emit(results)


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
            logger.error("Model copy failed: permission denied", exc_info=True)
            if self.dest.exists():
                self.dest.unlink()
            self.finished.emit(
                False, f"Permission denied writing to:\n{self.dest.parent}"
            )
        except OSError as e:
            logger.error("Model copy failed", exc_info=True)
            if self.dest.exists():
                self.dest.unlink()
            self.finished.emit(False, f"Failed to copy file: {e}")


class MultiModelCompareWorker(QThread):
    """Background worker that compares one prompt across multiple models."""

    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, prompt: str, model_paths: list[Path]):
        """Initialize a multi-model comparison run.

        Args:
            prompt: Prompt text to send to each model.
            model_paths: Ordered list of model file paths to compare.
        """
        super().__init__()
        self.prompt = prompt
        self.model_paths = model_paths
        self._stopped = False

    def stop(self) -> None:
        """Request cancellation of the comparison run."""
        self._stopped = True

    def run(self) -> None:
        """Run each model sequentially and emit collected comparison results."""
        from templatr.core.config import get_config
        from templatr.integrations.llm import get_llm_server

        if len(self.model_paths) < 2:
            self.error.emit("At least two models are required for comparison.")
            return

        server = get_llm_server()
        client = get_llm_client()
        original_model = get_config().llm.model_path
        was_running = server.is_running()
        results = []

        try:
            for idx, model_path in enumerate(self.model_paths, start=1):
                if self._stopped:
                    return

                self.progress.emit(
                    f"Comparing model {idx}/{len(self.model_paths)}: {model_path.stem}"
                )

                if server.is_running():
                    server.stop()

                started, start_msg = server.start(model_path=str(model_path))
                if not started:
                    raise RuntimeError(
                        f"Could not start server for {model_path.name}: {start_msg}"
                    )

                started_at = time.perf_counter()
                output = client.generate(self.prompt, stream=False)
                elapsed = time.perf_counter() - started_at

                prompt_tokens_est = len(self.prompt.split())
                output_tokens_est = len(output.split())

                results.append(
                    {
                        "model_name": model_path.stem,
                        "model_path": str(model_path),
                        "output": output,
                        "latency_seconds": elapsed,
                        "prompt_tokens_est": prompt_tokens_est,
                        "output_tokens_est": output_tokens_est,
                    }
                )
        except Exception as e:
            logger.error("Multi-model comparison failed", exc_info=True)
            self.error.emit(str(e))
            return
        finally:
            if server.is_running():
                server.stop()

            if was_running:
                restore_model: Optional[str] = original_model or None
                ok, msg = server.start(model_path=restore_model)
                if not ok:
                    logger.warning("Failed restoring original model after compare: %s", msg)

        if not self._stopped:
            self.finished.emit(results)


class CatalogFetchWorker(QThread):
    """Background worker that fetches and parses the catalog index from a URL.

    Emits ``catalog_ready`` with the list of valid entries on success, or
    ``error`` with a human-readable message on any failure.  Entries that are
    missing required fields are skipped with a logged warning rather than
    causing the whole catalog fetch to fail.
    """

    catalog_ready = pyqtSignal(object)  # list[dict]
    error = pyqtSignal(str)

    _TIMEOUT_SECONDS = 15

    def __init__(self, url: str):
        """Initialise the worker.

        Args:
            url: Raw URL of the catalog JSON index file.
        """
        super().__init__()
        self.url = url

    def run(self) -> None:
        """Fetch, parse, and validate the catalog index."""
        try:
            req = urllib.request.Request(
                self.url,
                headers={"User-Agent": "templatr-catalog-browser/1.0"},
            )
            with urllib.request.urlopen(req, timeout=self._TIMEOUT_SECONDS) as resp:
                if resp.status != 200:
                    self.error.emit(
                        f"Catalog server returned status {resp.status}.\n"
                        "Check the catalog URL in Settings."
                    )
                    return
                raw = resp.read()
        except urllib.error.HTTPError as exc:
            self.error.emit(
                f"Could not reach the catalog (HTTP {exc.code}).\n"
                "Check your internet connection or the catalog URL in Settings."
            )
            return
        except urllib.error.URLError as exc:
            self.error.emit(
                f"Could not reach the catalog.\n\n"
                f"Reason: {exc.reason}\n\n"
                "Check your internet connection or the catalog URL in Settings."
            )
            return
        except TimeoutError:
            self.error.emit(
                "The catalog request timed out.\n"
                "Check your internet connection and try again."
            )
            return
        except Exception as exc:  # noqa: BLE001
            self.error.emit(f"Unexpected error fetching catalog: {exc}")
            return

        if not raw:
            self.error.emit(
                "The catalog response was empty.\n"
                "The catalog URL may not be set up yet — see the README for setup instructions."
            )
            return

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            self.error.emit(f"Catalog data is not valid JSON: {exc}")
            return

        if not isinstance(data, list):
            self.error.emit(
                "Unexpected catalog format: expected a JSON array of template entries."
            )
            return

        entries: list[dict] = []
        for i, entry in enumerate(data):
            if not isinstance(entry, dict):
                logger.warning("Catalog entry %d is not an object — skipping", i)
                continue
            missing = _CATALOG_REQUIRED_FIELDS - entry.keys()
            if missing:
                logger.warning(
                    "Catalog entry %d (%r) missing required fields %s — skipping",
                    i,
                    entry.get("name", "?"),
                    missing,
                )
                continue
            entries.append(entry)

        self.catalog_ready.emit(entries)


class CatalogInstallWorker(QThread):
    """Background worker that downloads and installs a template from the catalog.

    Downloads the template JSON from ``download_url``, validates it via
    ``TemplateManager.import_template``, and either saves it directly (no
    conflict) or emits ``conflict`` with the parsed :class:`Template` so the
    caller can display a resolution UI.
    """

    #: Emitted when the template was saved successfully.  Carries the template name.
    installed = pyqtSignal(str)
    #: Emitted when a name conflict is detected.  Carries the Template object
    #: so the caller can resolve the conflict and call manager.save() itself.
    conflict = pyqtSignal(object)  # Template
    #: Emitted on any download or validation error.
    error = pyqtSignal(str)

    _TIMEOUT_SECONDS = 15

    def __init__(self, download_url: str, manager) -> None:
        """Initialise the worker.

        Args:
            download_url: Raw URL of the template ``.json`` file.
            manager: The application :class:`~templatr.core.templates.TemplateManager`.
        """
        super().__init__()
        self.download_url = download_url
        self.manager = manager

    def run(self) -> None:
        """Download, validate, and install the template."""
        try:
            req = urllib.request.Request(
                self.download_url,
                headers={"User-Agent": "templatr-catalog-browser/1.0"},
            )
            with urllib.request.urlopen(req, timeout=self._TIMEOUT_SECONDS) as resp:
                if resp.status != 200:
                    self.error.emit(
                        f"Download failed: server returned status {resp.status}."
                    )
                    return
                raw = resp.read()
        except urllib.error.HTTPError as exc:
            self.error.emit(f"Download failed (HTTP {exc.code}).")
            return
        except urllib.error.URLError as exc:
            self.error.emit(
                f"Download failed.\n\nReason: {exc.reason}\n\n"
                "Check your internet connection."
            )
            return
        except TimeoutError:
            self.error.emit("Download timed out. Check your internet connection.")
            return
        except Exception as exc:  # noqa: BLE001
            self.error.emit(f"Unexpected error during download: {exc}")
            return

        # Write to a temporary Path so we can reuse import_template's validation.
        import tempfile

        try:
            with tempfile.NamedTemporaryFile(
                suffix=".json", delete=False
            ) as tmp:
                tmp.write(raw)
                tmp_path = Path(tmp.name)
        except OSError as exc:
            self.error.emit(f"Could not write temporary file: {exc}")
            return

        try:
            template, has_conflict = self.manager.import_template(tmp_path)
        except ValueError as exc:
            tmp_path.unlink(missing_ok=True)
            self.error.emit(f"Template validation failed: {exc}")
            return
        finally:
            tmp_path.unlink(missing_ok=True)

        if has_conflict:
            self.conflict.emit(template)
            return

        if self.manager.save(template):
            self.installed.emit(template.name)
        else:
            self.error.emit(f"Could not save template '{template.name}' to disk.")

