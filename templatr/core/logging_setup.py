"""Logging setup for Templatr.

Configures structured local crash logging with rotating file handlers.
All logging is local and privacy-respecting — no prompt content or model
output is ever written to the log.

Usage::

    from templatr.core.logging_setup import setup_logging
    setup_logging()  # call once at startup, before any other init
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_LOG_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"
_LOG_FILE_NAME = "templatr.log"
_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
_BACKUP_COUNT = 3


def setup_logging(log_dir: Optional[Path] = None) -> None:
    """Configure the ``templatr`` logger with a rotating file handler.

    Creates a :class:`~logging.handlers.RotatingFileHandler` at
    ``<log_dir>/templatr.log`` (5 MB rotation, 3 backups).  If *log_dir*
    is ``None``, the default ``get_log_dir()`` path is used.

    This function is idempotent — calling it more than once will not
    add duplicate handlers.

    Args:
        log_dir: Directory for log files.  Defaults to the platform
            config-dir ``logs/`` subdirectory.
    """
    if log_dir is None:
        from templatr.core.config import get_log_dir

        log_dir = get_log_dir()

    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("templatr")

    # Idempotency guard: don't add handlers if one already exists for this file
    log_path = log_dir / _LOG_FILE_NAME
    for handler in logger.handlers:
        if (
            isinstance(handler, logging.handlers.RotatingFileHandler)
            and Path(handler.baseFilename).resolve() == log_path.resolve()
        ):
            return  # already configured

    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_LOG_DATE_FORMAT)

    file_handler = logging.handlers.RotatingFileHandler(
        filename=str(log_path),
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)


def unhandled_exception_hook(
    exc_type: type,
    exc_value: BaseException,
    exc_tb: object,
) -> None:
    """Global ``sys.excepthook`` replacement that logs CRITICAL.

    Logs the full traceback at CRITICAL level before allowing the
    interpreter to exit.  Keyboard interrupts are passed through to
    the default handler to allow normal Ctrl-C behaviour.

    Args:
        exc_type: Exception class.
        exc_value: Exception instance.
        exc_tb: Traceback object.
    """
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_tb)
        return

    logger = logging.getLogger("templatr")
    logger.critical(
        "Unhandled exception",
        exc_info=(exc_type, exc_value, exc_tb),
    )
