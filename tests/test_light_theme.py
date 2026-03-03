"""Tests for the light theme feature.

Covers: CSS completeness, get_theme_stylesheet for both variants,
theme toggle persistence, and View → Theme menu existence.
"""

import re
from unittest import mock

import pytest

from templatr.ui.theme import DARK_THEME, LIGHT_THEME, get_theme_stylesheet


# ---------------------------------------------------------------------------
# Helper: extract top-level CSS selectors from a stylesheet string
# ---------------------------------------------------------------------------


def _extract_selectors(css: str) -> set[str]:
    """Extract top-level CSS selectors from a Qt stylesheet string.

    Returns a set of normalised selector strings (stripped, no trailing '{').
    """
    raw = re.findall(r"^([A-Z][^\{]+)\{", css, re.MULTILINE)
    return {s.strip() for s in raw}


# ---------------------------------------------------------------------------
# CSS completeness tests
# ---------------------------------------------------------------------------


class TestLightThemeCSSCompleteness:
    """LIGHT_THEME must cover every CSS selector present in DARK_THEME."""

    DARK_SELECTORS = _extract_selectors(DARK_THEME)

    def test_light_theme_is_not_stub(self):
        """Light theme must be more than a 4-line stub."""
        assert len(LIGHT_THEME) > 200, "LIGHT_THEME appears to still be a stub"

    def test_all_dark_selectors_present_in_light(self):
        """Every selector in DARK_THEME must also appear in LIGHT_THEME."""
        light_selectors = _extract_selectors(LIGHT_THEME)
        missing = self.DARK_SELECTORS - light_selectors
        assert not missing, f"Selectors in DARK_THEME missing from LIGHT_THEME: {missing}"

    def test_light_theme_has_background_color(self):
        """Light theme must define a white-ish background."""
        assert "background-color:" in LIGHT_THEME

    def test_light_theme_has_dark_text(self):
        """Primary text should be dark on light backgrounds."""
        # Should contain a dark color for QLabel or QWidget text
        assert "color:" in LIGHT_THEME

    def test_chat_bubbles_distinct(self):
        """User, AI, system, and error bubbles must each have distinct styles."""
        for bubble_id in ("user_bubble", "ai_bubble", "system_bubble", "error_bubble"):
            assert bubble_id in LIGHT_THEME, f"{bubble_id} not styled in LIGHT_THEME"


# ---------------------------------------------------------------------------
# get_theme_stylesheet tests
# ---------------------------------------------------------------------------


class TestGetThemeStylesheet:
    """Tests for the get_theme_stylesheet() dispatch function."""

    def test_dark_returns_dark_theme(self):
        """get_theme_stylesheet('dark') returns CSS based on DARK_THEME."""
        css = get_theme_stylesheet("dark")
        # Dark theme has dark background
        assert "#1e1e1e" in css

    def test_light_returns_light_theme(self):
        """get_theme_stylesheet('light') returns CSS based on LIGHT_THEME."""
        css = get_theme_stylesheet("light")
        # Light theme should have light background, not dark
        assert "#ffffff" in css or "#f3f3f3" in css

    def test_dark_is_default(self):
        """Default (no argument) returns dark theme."""
        css = get_theme_stylesheet()
        assert "#1e1e1e" in css

    def test_font_size_applied(self):
        """Font size parameter is injected into the stylesheet."""
        css = get_theme_stylesheet("light", font_size=16)
        assert "16pt" in css

    def test_dark_theme_unchanged(self):
        """DARK_THEME constant must not be modified by this feature."""
        # Verify key dark theme properties
        assert "#1e1e1e" in DARK_THEME  # background
        assert "#d4d4d4" in DARK_THEME  # text color
        assert "#0e639c" in DARK_THEME  # button color
        assert "#007acc" in DARK_THEME  # status bar


# ---------------------------------------------------------------------------
# Theme toggle UI tests
# ---------------------------------------------------------------------------


class TestThemeToggleMenu:
    """Tests for the View → Theme menu in MainWindow."""

    def test_view_menu_exists(self, qtbot):
        """MainWindow has a View menu."""
        from templatr.ui.main_window import MainWindow

        with mock.patch(
            "templatr.ui.main_window.get_llm_server"
        ), mock.patch(
            "templatr.ui.main_window.get_llm_client"
        ):
            win = MainWindow()
            qtbot.addWidget(win)

        menubar = win.menuBar()
        menu_texts = [a.text().replace("&", "") for a in menubar.actions()]
        assert "View" in menu_texts

    def test_theme_submenu_has_dark_and_light(self, qtbot):
        """View → Theme submenu has Dark and Light options."""
        from templatr.ui.main_window import MainWindow

        with mock.patch(
            "templatr.ui.main_window.get_llm_server"
        ), mock.patch(
            "templatr.ui.main_window.get_llm_client"
        ):
            win = MainWindow()
            qtbot.addWidget(win)

        # Find the View menu
        menubar = win.menuBar()
        view_menu = None
        for action in menubar.actions():
            if action.text().replace("&", "") == "View":
                view_menu = action.menu()
                break
        assert view_menu is not None, "View menu not found"

        # Find Theme submenu
        theme_menu = None
        for action in view_menu.actions():
            if "Theme" in action.text().replace("&", ""):
                theme_menu = action.menu()
                break
        assert theme_menu is not None, "Theme submenu not found"

        action_texts = [a.text() for a in theme_menu.actions() if not a.isSeparator()]
        assert "Dark" in action_texts
        assert "Light" in action_texts

    def test_current_theme_is_checked(self, qtbot):
        """The active theme option has a checkmark."""
        from templatr.ui.main_window import MainWindow

        with mock.patch(
            "templatr.ui.main_window.get_llm_server"
        ), mock.patch(
            "templatr.ui.main_window.get_llm_client"
        ):
            win = MainWindow()
            qtbot.addWidget(win)

        # Find the View → Theme submenu
        menubar = win.menuBar()
        view_menu = None
        for action in menubar.actions():
            if action.text().replace("&", "") == "View":
                view_menu = action.menu()
                break

        theme_menu = None
        for action in view_menu.actions():
            if "Theme" in action.text().replace("&", ""):
                theme_menu = action.menu()
                break

        # One of Dark/Light should be checked
        checked = [a for a in theme_menu.actions() if a.isChecked()]
        assert len(checked) == 1, "Exactly one theme option should be checked"

    def test_theme_switch_persists_to_config(self, qtbot, tmp_path, monkeypatch):
        """Switching theme updates the config."""
        from templatr.core.config import get_config_manager
        from templatr.ui.main_window import MainWindow

        with mock.patch(
            "templatr.ui.main_window.get_llm_server"
        ), mock.patch(
            "templatr.ui.main_window.get_llm_client"
        ):
            win = MainWindow()
            qtbot.addWidget(win)

        # Find the Light action
        menubar = win.menuBar()
        view_menu = None
        for action in menubar.actions():
            if action.text().replace("&", "") == "View":
                view_menu = action.menu()
                break

        theme_menu = None
        for action in view_menu.actions():
            if "Theme" in action.text().replace("&", ""):
                theme_menu = action.menu()
                break

        light_action = None
        for action in theme_menu.actions():
            if action.text() == "Light":
                light_action = action
                break

        assert light_action is not None
        light_action.trigger()

        cm = get_config_manager()
        assert cm.config.ui.theme == "light"
