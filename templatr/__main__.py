"""Templatr CLI entry point."""

import argparse
import logging
import sys
import threading

from templatr import __version__

logger = logging.getLogger(__name__)


def _exception_hook(exc_type, exc_value, exc_tb):
    """Global handler for unhandled exceptions.

    Logs at CRITICAL level with full traceback, then falls through to the
    default hook so the interpreter still prints to stderr.
    """
    logger.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_tb))


def _threading_exception_hook(args):
    """Handler for unhandled exceptions in non-main threads."""
    logger.critical(
        "Unhandled exception in thread %s",
        args.thread.name if args.thread else "unknown",
        exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
    )


def main() -> int:
    """Main entry point for templatr CLI."""
    # Initialise logging first — before anything else.
    from templatr.core.logging_setup import setup_logging

    setup_logging()

    # Install global exception hooks.
    sys.excepthook = _exception_hook
    threading.excepthook = _threading_exception_hook

    parser = argparse.ArgumentParser(
        prog="templatr",
        description="Local prompt optimizer with reusable templates and llama.cpp integration",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"templatr {__version__}",
    )

    parser.parse_args()

    from templatr.ui.main_window import run_gui

    return run_gui()


if __name__ == "__main__":
    sys.exit(main())
