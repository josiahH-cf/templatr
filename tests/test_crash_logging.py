"""Tests for crash logging and diagnostics (spec: /specs/crash-logging.md).

Covers:
- Task 1: logging module setup, rotation config, log format
- Task 2: global exception hook, worker error logging, privacy
- Task 3: Help menu "View Log File" action
"""

import logging
import re
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def log_dir(tmp_path, monkeypatch):
    """Provide an isolated log directory via a temp config dir."""
    monkeypatch.setattr(
        "templatr.core.config.get_config_dir", lambda: tmp_path
    )
    return tmp_path / "logs"


@pytest.fixture(autouse=True)
def _clean_root_logger():
    """Remove handlers added by setup_logging() after each test."""
    yield
    root = logging.getLogger()
    for handler in root.handlers[:]:
        handler.close()
        root.removeHandler(handler)
    root.setLevel(logging.WARNING)  # restore default


# ---------------------------------------------------------------------------
# Task 1: Logging module setup and configuration
# ---------------------------------------------------------------------------


class TestGetLogDir:
    """Tests for get_log_dir() in config.py."""

    def test_creates_log_directory(self, log_dir):
        """get_log_dir() creates the logs/ subdirectory."""
        from templatr.core.config import get_log_dir

        result = get_log_dir()
        assert result == log_dir
        assert result.is_dir()

    def test_returns_same_path_on_repeated_calls(self, log_dir):
        """get_log_dir() is idempotent."""
        from templatr.core.config import get_log_dir

        assert get_log_dir() == get_log_dir()


class TestSetupLogging:
    """Tests for setup_logging() in logging_setup.py."""

    def test_creates_log_file(self, log_dir):
        """setup_logging() creates the templatr.log file."""
        from templatr.core.logging_setup import setup_logging

        log_path = setup_logging()
        assert log_path.exists()
        assert log_path.name == "templatr.log"
        assert log_path.parent == log_dir

    def test_returns_log_file_path(self, log_dir):
        """setup_logging() returns a Path to the log file."""
        from templatr.core.logging_setup import setup_logging

        result = setup_logging()
        assert isinstance(result, Path)

    def test_rotating_handler_max_bytes(self, log_dir):
        """RotatingFileHandler is configured with 5 MB max size."""
        from templatr.core.logging_setup import setup_logging

        setup_logging()
        root = logging.getLogger()
        rotating = [
            h for h in root.handlers if isinstance(h, RotatingFileHandler)
        ]
        assert len(rotating) == 1
        assert rotating[0].maxBytes == 5 * 1024 * 1024

    def test_rotating_handler_backup_count(self, log_dir):
        """RotatingFileHandler keeps 3 backup files."""
        from templatr.core.logging_setup import setup_logging

        setup_logging()
        root = logging.getLogger()
        rotating = [
            h for h in root.handlers if isinstance(h, RotatingFileHandler)
        ]
        assert rotating[0].backupCount == 3

    def test_root_logger_level_info(self, log_dir):
        """Root logger is set to INFO level."""
        from templatr.core.logging_setup import setup_logging

        setup_logging()
        assert logging.getLogger().level == logging.INFO

    def test_log_format_iso8601_timestamp(self, log_dir):
        """Log entries contain ISO-8601 timestamps."""
        from templatr.core.logging_setup import setup_logging

        log_path = setup_logging()
        logger = logging.getLogger("test.format")
        logger.info("format check")

        content = log_path.read_text(encoding="utf-8")
        # ISO-8601 pattern: YYYY-MM-DDTHH:MM:SS
        assert re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", content)

    def test_log_format_contains_level_and_module(self, log_dir):
        """Log entries include level name and logger name."""
        from templatr.core.logging_setup import setup_logging

        log_path = setup_logging()
        logger = logging.getLogger("test.module_check")
        logger.warning("level check")

        content = log_path.read_text(encoding="utf-8")
        assert "[WARNING]" in content
        assert "test.module_check" in content

    def test_idempotent_setup(self, log_dir):
        """Calling setup_logging() twice does not duplicate handlers."""
        from templatr.core.logging_setup import setup_logging

        setup_logging()
        setup_logging()
        root = logging.getLogger()
        rotating = [
            h for h in root.handlers if isinstance(h, RotatingFileHandler)
        ]
        assert len(rotating) == 1


# ---------------------------------------------------------------------------
# Task 2: Global exception hook and worker error logging
# ---------------------------------------------------------------------------


class TestExceptionHook:
    """Tests for the global sys.excepthook handler."""

    def test_exception_hook_logs_critical(self, log_dir):
        """Unhandled exception hook writes a CRITICAL log entry."""
        from templatr.core.logging_setup import setup_logging

        log_path = setup_logging()

        from templatr.__main__ import _exception_hook

        try:
            raise RuntimeError("boom")
        except RuntimeError:
            exc_type, exc_value, exc_tb = sys.exc_info()
            _exception_hook(exc_type, exc_value, exc_tb)

        content = log_path.read_text(encoding="utf-8")
        assert "[CRITICAL]" in content
        assert "boom" in content

    def test_exception_hook_includes_traceback(self, log_dir):
        """Hook output includes traceback detail."""
        from templatr.core.logging_setup import setup_logging

        log_path = setup_logging()

        from templatr.__main__ import _exception_hook

        try:
            raise ValueError("trace test")
        except ValueError:
            exc_type, exc_value, exc_tb = sys.exc_info()
            _exception_hook(exc_type, exc_value, exc_tb)

        content = log_path.read_text(encoding="utf-8")
        assert "Traceback" in content
        assert "ValueError" in content


class TestWorkerErrorLogging:
    """Tests for error logging in GenerationWorker."""

    def test_generation_worker_logs_error(self, log_dir):
        """GenerationWorker logs errors at ERROR level with traceback."""
        from templatr.core.logging_setup import setup_logging

        log_path = setup_logging()

        mock_client = MagicMock()
        mock_client.generate_stream.side_effect = RuntimeError("LLM down")

        with patch("templatr.ui.workers.get_llm_client", return_value=mock_client):
            from templatr.ui.workers import GenerationWorker

            worker = GenerationWorker("test prompt")
            worker.run()

        content = log_path.read_text(encoding="utf-8")
        assert "[ERROR]" in content
        assert "LLM down" in content

    def test_worker_error_does_not_log_prompt(self, log_dir):
        """Prompt text must not appear in log output (privacy)."""
        from templatr.core.logging_setup import setup_logging

        log_path = setup_logging()

        secret_prompt = "SUPER_SECRET_PROMPT_CONTENT_xyz123"
        mock_client = MagicMock()
        mock_client.generate_stream.side_effect = RuntimeError("fail")

        with patch("templatr.ui.workers.get_llm_client", return_value=mock_client):
            from templatr.ui.workers import GenerationWorker

            worker = GenerationWorker(secret_prompt)
            worker.run()

        content = log_path.read_text(encoding="utf-8")
        assert secret_prompt not in content

    def test_model_copy_worker_logs_error(self, log_dir, tmp_path):
        """ModelCopyWorker logs errors at ERROR level."""
        from templatr.core.logging_setup import setup_logging

        log_path = setup_logging()

        from templatr.ui.workers import ModelCopyWorker

        source = tmp_path / "missing.gguf"
        dest = tmp_path / "dest.gguf"
        worker = ModelCopyWorker(source, dest)
        worker.run()

        content = log_path.read_text(encoding="utf-8")
        assert "[ERROR]" in content


class TestLLMServerLogging:
    """Tests for logging in LLM server manager."""

    def test_server_start_failure_logged(self, log_dir):
        """Failed server start is logged at ERROR level."""
        from templatr.core.logging_setup import setup_logging

        log_path = setup_logging()

        from templatr.integrations.llm import LLMServerManager

        manager = LLMServerManager()
        # No binary configured — start will fail
        manager.start()

        content = log_path.read_text(encoding="utf-8")
        assert "[ERROR]" in content or "[WARNING]" in content

    def test_server_stop_logged(self, log_dir):
        """Server stop is logged at INFO level."""
        from templatr.core.logging_setup import setup_logging

        log_path = setup_logging()

        from templatr.integrations.llm import LLMServerManager

        manager = LLMServerManager()
        manager.stop()

        content = log_path.read_text(encoding="utf-8")
        assert "[INFO]" in content


# ---------------------------------------------------------------------------
# Task 3: Help menu "View Log File" action
# ---------------------------------------------------------------------------


class TestViewLogAction:
    """Tests for the Help menu 'View Log File' action."""

    def test_help_menu_has_view_log_action(self, qtbot, log_dir):
        """Help menu contains a 'View Log File' action."""
        from templatr.core.logging_setup import setup_logging

        setup_logging()

        from templatr.ui.main_window import MainWindow

        window = MainWindow()
        qtbot.addWidget(window)

        menubar = window.menuBar()
        help_menu = None
        for action in menubar.actions():
            if action.text().replace("&", "") == "Help":
                help_menu = action.menu()
                break

        assert help_menu is not None, "Help menu not found"
        action_texts = [a.text().replace("&", "") for a in help_menu.actions()]
        assert "View Log File" in action_texts

    def test_view_log_opens_directory(self, qtbot, log_dir):
        """Triggering 'View Log File' calls QDesktopServices.openUrl."""
        from templatr.core.logging_setup import setup_logging

        setup_logging()

        from templatr.ui.main_window import MainWindow

        window = MainWindow()
        qtbot.addWidget(window)

        with patch("templatr.ui.main_window.QDesktopServices") as mock_desktop:
            mock_desktop.openUrl.return_value = True
            window._open_log_directory()
            mock_desktop.openUrl.assert_called_once()

            url = mock_desktop.openUrl.call_args[0][0]
            url_str = url.toLocalFile()
            assert "logs" in url_str
