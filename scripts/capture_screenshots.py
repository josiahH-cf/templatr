#!/usr/bin/env python3
"""Capture screenshots of Templatr for documentation.

Usage:
    .venv/bin/python scripts/capture_screenshots.py

Produces:
    docs/images/main-chat-view.png
    docs/images/slash-command-palette.png
    docs/images/template-editor.png
    docs/images/new-template-flow.png
"""

import os
import sys

# Force offscreen rendering for headless capture
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from pathlib import Path

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication

# Ensure package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from templatr import __version__
from templatr.core.config import get_config
from templatr.ui.main_window import MainWindow
from templatr.ui.theme import get_theme_stylesheet

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "docs" / "images"


def capture(widget, name: str):
    """Grab a screenshot of a widget and save it."""
    pixmap = widget.grab()
    path = OUTPUT_DIR / name
    pixmap.save(str(path), "PNG")
    print(f"  Saved {path}")


def main():
    """Capture all documentation screenshots."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    app = QApplication(sys.argv)
    app.setApplicationName("Templatr")
    app.setApplicationVersion(__version__)

    config = get_config()
    stylesheet = get_theme_stylesheet(config.ui.theme, config.ui.font_size)
    app.setStyleSheet(stylesheet)
    app.setFont(QFont(app.font().family(), config.ui.font_size))

    window = MainWindow()
    window.resize(1200, 800)
    window.show()

    # Process events so the layout settles
    app.processEvents()
    app.processEvents()

    # 1. Main chat view
    capture(window, "main-chat-view.png")

    # 2. Slash command palette — simulate typing "/"
    window.slash_input._text_input.setFocus()
    window.slash_input._text_input.setPlainText("/")
    app.processEvents()
    app.processEvents()
    capture(window, "slash-command-palette.png")

    # Clear the input
    window.slash_input._text_input.clear()
    app.processEvents()

    # 3. Template editor — open advanced edit on a template if one exists
    templates = window.template_manager.list_all()
    if templates:
        window.template_tree_widget.load_templates()
        app.processEvents()
        capture(window, "template-editor.png")
    else:
        # Fallback: capture the main view with sidebar visible
        capture(window, "template-editor.png")

    # 4. New template flow — type /new
    window.slash_input._text_input.setFocus()
    window.slash_input._text_input.setPlainText("/new")
    app.processEvents()
    app.processEvents()
    capture(window, "new-template-flow.png")

    print(f"\nDone — {len(list(OUTPUT_DIR.glob('*.png')))} screenshots in {OUTPUT_DIR}")
    app.quit()


if __name__ == "__main__":
    main()
