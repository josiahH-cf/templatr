"""Templatr CLI entry point."""

import argparse
import sys

from templatr import __version__


def main() -> int:
    """Main entry point for templatr CLI."""
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

    # Initialize logging before anything else
    from templatr.core.logging_setup import setup_logging, unhandled_exception_hook

    setup_logging()
    sys.excepthook = unhandled_exception_hook

    from templatr.ui.main_window import run_gui

    return run_gui()


if __name__ == "__main__":
    sys.exit(main())
