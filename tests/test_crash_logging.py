"""Tests for crash logging & diagnostics (spec: /specs/crash-logging.md).

Covers:
- Criterion 1: Rotating log file at <config_dir>/logs/<appname>.log
- Criterion 2: Global sys.excepthook logs CRITICAL unhandled exceptions
- Criterion 3: Worker errors logged at ERROR with full traceback
- Criterion 4: Help menu "View Log File" action exists
- Criterion 5: Rotation config (5 MB, 3 backups)
- Criterion 6: No prompt content in log format
"""

import logging
import logging.handlers
import sys
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _clean_logging_handlers():
    """Remove file handlers added by setup_logging after each test."""
    yield
    logger = logging.getLogger("templatr")
    for handler in logger.handlers[:]:
        if isinstance(handler, logging.handlers.RotatingFileHandler):
            handler.close()
            logger.removeHandler(handler)


# ---------------------------------------------------------------------------
# Task 1: Logging module setup and configuration
# ---------------------------------------------------------------------------


class TestSetupLogging:
    """Verify setup_logging creates the expected logger configuration."""

    def test_log_file_created(self, tmp_path):
        """Criterion 1: A log file is written under the log directory."""
        from templatr.core.logging_setup import setup_logging

        setup_logging(log_dir=tmp_path)

        log_file = tmp_path / "templatr.log"
        # Write a log entry to flush handler
        logger = logging.getLogger("templatr")
        logger.info("test message")
        # Force flush
        for handler in logger.handlers:
            handler.flush()

        assert log_file.exists(), "Log file was not created"

    def test_log_format_iso8601(self, tmp_path):
        """Criterion 1: Log entries contain ISO-8601 timestamp, level, module."""
        from templatr.core.logging_setup import setup_logging

        setup_logging(log_dir=tmp_path)

        logger = logging.getLogger("templatr.test_format")
        logger.warning("format check")

        log_file = tmp_path / "templatr.log"
        for handler in logging.getLogger("templatr").handlers:
            handler.flush()

        content = log_file.read_text()
        # ISO-8601 date pattern YYYY-MM-DD HH:MM:SS
        assert "format check" in content
        assert "[WARNING]" in content
        assert "templatr.test_format" in content

    def test_rotating_handler_config(self, tmp_path):
        """Criterion 5: RotatingFileHandler uses 5 MB / 3 backups."""
        from templatr.core.logging_setup import setup_logging

        setup_logging(log_dir=tmp_path)

        root_logger = logging.getLogger("templatr")
        rotating_handlers = [
            h
            for h in root_logger.handlers
            if isinstance(h, logging.handlers.RotatingFileHandler)
        ]
        assert len(rotating_handlers) >= 1, "No RotatingFileHandler found"

        handler = rotating_handlers[0]
        assert handler.maxBytes == 5 * 1024 * 1024, "maxBytes should be 5 MB"
        assert handler.backupCount == 3, "backupCount should be 3"

    def test_no_prompt_content_in_format(self, tmp_path):
        """Criterion 6: Log format does not include prompt content fields."""
        from templatr.core.logging_setup import setup_logging

        setup_logging(log_dir=tmp_path)

        root_logger = logging.getLogger("templatr")
        rotating_handlers = [
            h
            for h in root_logger.handlers
            if isinstance(h, logging.handlers.RotatingFileHandler)
        ]
        fmt = rotating_handlers[0].formatter._fmt
        # Format should NOT contain anything that could leak user content
        assert "prompt" not in fmt.lower()
        assert "output" not in fmt.lower()
        assert "content" not in fmt.lower()

    def test_idempotent_setup(self, tmp_path):
        """Calling setup_logging twice should not duplicate handlers."""
        from templatr.core.logging_setup import setup_logging

        setup_logging(log_dir=tmp_path)
        setup_logging(log_dir=tmp_path)

        root_logger = logging.getLogger("templatr")
        rotating_handlers = [
            h
            for h in root_logger.handlers
            if isinstance(h, logging.handlers.RotatingFileHandler)
        ]
        assert len(rotating_handlers) == 1, "Duplicate handlers after double setup"


# ---------------------------------------------------------------------------
# Task 2: Global exception hook and worker error logging
# ---------------------------------------------------------------------------


class TestGlobalExceptionHook:
    """Verify the global exception hook writes CRITICAL log entries."""

    def test_exception_hook_logs_critical(self, tmp_path):
        """Criterion 2: Unhandled exceptions logged at CRITICAL level."""
        from templatr.core.logging_setup import setup_logging, unhandled_exception_hook

        setup_logging(log_dir=tmp_path)

        # Simulate an unhandled exception
        try:
            raise RuntimeError("boom")
        except RuntimeError:
            exc_type, exc_value, exc_tb = sys.exc_info()
            unhandled_exception_hook(exc_type, exc_value, exc_tb)

        log_file = tmp_path / "templatr.log"
        for handler in logging.getLogger("templatr").handlers:
            handler.flush()

        content = log_file.read_text()
        assert "[CRITICAL]" in content
        assert "boom" in content

    def test_exception_hook_includes_traceback(self, tmp_path):
        """Criterion 2: The CRITICAL entry includes the traceback."""
        from templatr.core.logging_setup import setup_logging, unhandled_exception_hook

        setup_logging(log_dir=tmp_path)

        try:
            raise ValueError("detailed error")
        except ValueError:
            exc_type, exc_value, exc_tb = sys.exc_info()
            unhandled_exception_hook(exc_type, exc_value, exc_tb)

        log_file = tmp_path / "templatr.log"
        for handler in logging.getLogger("templatr").handlers:
            handler.flush()

        content = log_file.read_text()
        assert "Traceback" in content
        assert "detailed error" in content


class TestWorkerErrorLogging:
    """Verify GenerationWorker errors are logged at ERROR level."""

    def test_generation_worker_logs_error(self, tmp_path):
        """Criterion 3: Worker errors logged at ERROR with full exception chain."""
        from templatr.core.logging_setup import setup_logging

        setup_logging(log_dir=tmp_path)

        # Patch get_llm_client so the worker's generate call raises
        mock_client = MagicMock()
        mock_client.generate_stream.side_effect = ConnectionError("server down")

        with patch("templatr.ui.workers.get_llm_client", return_value=mock_client):
            from templatr.ui.workers import GenerationWorker

            worker = GenerationWorker("test prompt", stream=True)
            worker.run()  # run synchronously for testing

        log_file = tmp_path / "templatr.log"
        for handler in logging.getLogger("templatr").handlers:
            handler.flush()

        content = log_file.read_text()
        assert "[ERROR]" in content
        assert "server down" in content


# ---------------------------------------------------------------------------
# Task 3: Help menu "View Log File" action
# ---------------------------------------------------------------------------


class TestViewLogFileAction:
    """Verify the Help menu has a View Log File action."""

    def test_help_menu_has_view_log_action(self, qtbot):
        """Criterion 4: Help menu includes 'View Log File' action."""
        from templatr.ui.main_window import MainWindow

        window = MainWindow()
        qtbot.addWidget(window)

        menubar = window.menuBar()
        help_menu = None
        for action in menubar.actions():
            if action.text() == "&Help":
                help_menu = action.menu()
                break

        assert help_menu is not None, "Help menu not found"

        action_texts = [a.text() for a in help_menu.actions()]
        assert any(
            "Log" in t for t in action_texts
        ), f"No log action found in Help menu. Actions: {action_texts}"

    def test_view_log_opens_file_manager(self, qtbot):
        """Criterion 4: The action opens the log directory via QDesktopServices."""
        from templatr.ui.main_window import MainWindow

        window = MainWindow()
        qtbot.addWidget(window)

        with patch("templatr.ui.main_window.QDesktopServices.openUrl") as mock_open:
            window._view_log_file()
            mock_open.assert_called_once()
            url = mock_open.call_args[0][0]
            assert "logs" in url.toLocalFile()
