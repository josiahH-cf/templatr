"""Logging setup for Templatr.

Configures a rotating file handler that writes to ``<config_dir>/logs/templatr.log``.
All log entries use ISO-8601 timestamps, level, and module name — no prompt content
or model output is ever logged (privacy-first design).
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from templatr.core.config import get_log_dir

#: Maximum size per log file (5 MB).
_MAX_BYTES = 5 * 1024 * 1024

#: Number of rotated backup files to keep.
_BACKUP_COUNT = 3

#: Structured log format — timestamp, level, module only.
_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

#: ISO-8601 date format for log timestamps.
_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"

_setup_done = False


def setup_logging() -> Path:
    """Configure the root logger with a rotating file handler.

    Safe to call more than once — duplicate handlers are prevented.

    Returns:
        Path to the active log file.
    """
    global _setup_done

    log_dir = get_log_dir()
    log_file = log_dir / "templatr.log"

    root_logger = logging.getLogger()

    if _setup_done:
        return log_file

    root_logger.setLevel(logging.INFO)

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    # Rotating file handler
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Console handler (stderr) for development visibility
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    _setup_done = True

    logging.getLogger(__name__).info("Logging initialised — %s", log_file)
    return log_file


def reset_logging() -> None:
    """Clear logging state so setup_logging() can run again.

    For testing only.
    """
    global _setup_done
    _setup_done = False
