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
    parser.add_argument(
        "--doctor",
        action="store_true",
        help="Run diagnostic checks and report platform, paths, and status",
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command")

    # templatr status --json
    status_parser = subparsers.add_parser("status", help="Show app status")
    status_parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output status as JSON",
    )

    # templatr gui (explicit, optional)
    subparsers.add_parser("gui", help="Launch the GUI")

    args = parser.parse_args()

    if args.doctor:
        from templatr.doctor import run_doctor

        return run_doctor()

    if args.command == "status":
        return _cmd_status(args)

    # Default: launch GUI (no args or explicit 'gui' subcommand)
    from templatr.ui.main_window import run_gui

    return run_gui()


def _cmd_status(args) -> int:
    """Handle the ``templatr status`` subcommand.

    Args:
        args: Parsed argparse namespace with ``json_output`` flag.

    Returns:
        Exit code (0 on success).
    """
    from templatr.integrations.orchestratr import get_status_json

    if args.json_output:
        print(get_status_json())
        return 0

    # Plain text fallback — just print the JSON pretty for now
    print(get_status_json())
    return 0


if __name__ == "__main__":
    sys.exit(main())
