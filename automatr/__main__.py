"""Automatr CLI entry point."""

import argparse
import sys

from automatr import __version__


def main() -> int:
    """Main entry point for automatr CLI."""
    parser = argparse.ArgumentParser(
        prog="automatr",
        description="Minimal prompt automation tool with local LLM integration",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"automatr {__version__}",
    )

    parser.parse_args()

    from automatr.ui.main_window import run_gui

    return run_gui()


if __name__ == "__main__":
    sys.exit(main())
