"""Tests for keyboard-shortcuts feature.

Covers all seven acceptance criteria from /specs/keyboard-shortcuts.md:
- AC-1: Ctrl+Return fires plain_submitted (generate shortcut)
- AC-2: Generate shortcut is suppressed when palette or form is active
- AC-3: Ctrl+Shift+C copies last AI output to clipboard
- AC-4: Ctrl+] / Ctrl+[ navigate between templates with wrap-around
- AC-5: Ctrl+L clears the chat thread; ignored during generation
- AC-6: UIConfig.shortcuts field holds default bindings and loads overrides
- AC-7: /help lists all five keyboard shortcut actions

These tests were written before implementation (TDD). All tests
assert behavior that does not yet exist and will fail until the
feature is implemented.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from templatr.core.config import ConfigManager, UIConfig
from templatr.core.templates import Template, Variable
from templatr.ui.slash_input import SlashInputWidget


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_template(name: str = "Quick Note", with_vars: bool = False) -> Template:
    """Build a minimal template for navigation and palette tests."""
    if with_vars:
        return Template(
            name=name,
            content="Review: {{topic}}",
            description=f"{name} template",
            variables=[Variable(name="topic", label="Topic")],
        )
    return Template(
        name=name,
        content=f"This is the {name} template.",
        description=f"{name} template",
        variables=[],
    )


def _make_three_templates():
    """Three templates in alphabetical order for navigation tests."""
    return [
        _make_template("Alpha"),
        _make_template("Beta"),
        _make_template("Gamma"),
    ]


def _make_window(qtbot, templates=None):
    """Create a MainWindow with mocked dependencies.

    Passes templates, llm_client, and llm_server directly to the
    MainWindow constructor so no real singletons are used.
    Patches template_tree and llm_toolbar singletons needed during init.
    """
    if templates is None:
        templates = []

    mock_template_mgr = MagicMock()
    mock_template_mgr.list_all.return_value = templates
    mock_template_mgr.list_folders.return_value = []
    mock_template_mgr.get_template_folder.return_value = ""

    mock_llm_server = MagicMock()
    mock_llm_server.is_running.return_value = False
    mock_llm_client = MagicMock()

    with patch(
        "templatr.ui.template_tree.get_template_manager",
        return_value=mock_template_mgr,
    ), patch(
        "templatr.ui.llm_toolbar.get_llm_server",
        return_value=mock_llm_server,
    ):
        from templatr.ui.main_window import MainWindow

        win = MainWindow(
            templates=mock_template_mgr,
            llm_client=mock_llm_client,
            llm_server=mock_llm_server,
        )
        qtbot.addWidget(win)
        win.show()
        return win


# ---------------------------------------------------------------------------
# AC-6: UIConfig.shortcuts field
# ---------------------------------------------------------------------------


def test_shortcuts_defaults_in_config():
    """UIConfig has a 'shortcuts' dict field with all five default bindings."""
    cfg = UIConfig()
    # Fails before implementation: UIConfig has no 'shortcuts' attribute
    assert hasattr(cfg, "shortcuts"), "UIConfig should have a 'shortcuts' field"
    assert isinstance(cfg.shortcuts, dict)
    for key in ("generate", "copy_output", "clear_chat", "next_template", "prev_template"):
        assert key in cfg.shortcuts, f"shortcuts should contain '{key}'"


def test_shortcut_override_loaded_from_config(tmp_path: Path):
    """Config.from_dict applies a custom shortcut binding from config.json."""
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps({"ui": {"shortcuts": {"generate": "Ctrl+G"}}}),
        encoding="utf-8",
    )
    mgr = ConfigManager(config_path=config_path)
    cfg = mgr.load()

    # Fails before implementation: 'shortcuts' key is ignored by from_dict
    assert hasattr(cfg.ui, "shortcuts"), "UIConfig loaded from JSON should have 'shortcuts'"
    assert cfg.ui.shortcuts.get("generate") == "Ctrl+G"


def test_shortcut_defaults_applied_when_key_absent(tmp_path: Path):
    """When 'shortcuts' is absent from config.json, default bindings are used."""
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"ui": {}}), encoding="utf-8")
    mgr = ConfigManager(config_path=config_path)
    cfg = mgr.load()

    # Fails before implementation: no 'shortcuts' field at all
    assert hasattr(cfg.ui, "shortcuts")
    assert "generate" in cfg.ui.shortcuts
    assert cfg.ui.shortcuts["generate"]  # non-empty default binding


# ---------------------------------------------------------------------------
# AC-2: SlashInputWidget.is_palette_visible() guard method
# ---------------------------------------------------------------------------


def test_is_palette_visible_returns_true_when_palette_open(qtbot):
    """is_palette_visible() returns True when the command palette is visible."""
    widget = SlashInputWidget()
    qtbot.addWidget(widget)
    widget.show()
    widget.set_templates([_make_template()])

    qtbot.keyClicks(widget._text_input, "/")

    # Fails before implementation: is_palette_visible() method does not exist
    assert widget.is_palette_visible()


def test_is_palette_visible_returns_false_initially(qtbot):
    """is_palette_visible() returns False when palette has not been opened."""
    widget = SlashInputWidget()
    qtbot.addWidget(widget)

    # Fails before implementation: is_palette_visible() method does not exist
    assert not widget.is_palette_visible()


def test_is_palette_visible_returns_false_when_form_active(qtbot):
    """is_palette_visible() returns False when the inline variable form is shown."""
    widget = SlashInputWidget()
    qtbot.addWidget(widget)
    widget.show()
    tpl = _make_template("Review", with_vars=True)
    widget.set_templates([tpl])

    # Show the inline variable form
    widget._on_template_chosen(tpl)
    assert widget._inline_form.isVisible()

    # Fails before implementation: is_palette_visible() method does not exist
    assert not widget.is_palette_visible()


# ---------------------------------------------------------------------------
# AC-1: Generate shortcut (Ctrl+Return) fires plain_submitted
# ---------------------------------------------------------------------------


def test_generate_shortcut_submits_text(qtbot, monkeypatch):
    """Pressing Ctrl+Return with plain text in the input calls _handle_plain_input."""
    win = _make_window(qtbot)
    win.slash_input.set_llm_ready(True)
    win.slash_input._text_input.setPlainText("Hello shortcut world")

    # Intercept _handle_plain_input to avoid triggering the LLM chain
    received = []
    monkeypatch.setattr(win, "_handle_plain_input", lambda text: received.append(text))

    # Fire Ctrl+Return on the window — before implementation, no QShortcut registered
    qtbot.keyPress(win, Qt.Key.Key_Return, Qt.KeyboardModifier.ControlModifier)

    # Fails before implementation: no shortcut exists, received stays empty
    assert len(received) == 1
    assert received[0] == "Hello shortcut world"


def test_generate_shortcut_no_op_when_palette_visible(qtbot, monkeypatch):
    """Ctrl+Return does not submit when the slash-command palette is open."""
    win = _make_window(qtbot)
    win.slash_input.set_llm_ready(True)
    win.slash_input.set_templates([_make_template()])
    win.slash_input._text_input.setPlainText("irrelevant")

    # Open the palette
    qtbot.keyClicks(win.slash_input._text_input, "/")
    # Verify palette is visible (this also checks is_palette_visible() exists)
    # Fails before implementation: is_palette_visible() doesn't exist
    assert win.slash_input.is_palette_visible()

    received = []
    monkeypatch.setattr(win, "_handle_plain_input", lambda text: received.append(text))

    qtbot.keyPress(win, Qt.Key.Key_Return, Qt.KeyboardModifier.ControlModifier)

    # Shortcut must be suppressed when palette is open
    assert len(received) == 0


def test_generate_shortcut_no_op_when_form_active(qtbot, monkeypatch):
    """Ctrl+Return is suppressed when the inline variable form is active.

    The generate shortcut slot guards using is_palette_visible() and the
    inline form visibility. This test verifies is_palette_visible() exists
    (the guard precondition) and that the shortcut does not fire.
    """
    win = _make_window(qtbot)
    win.slash_input.set_llm_ready(True)
    tpl = _make_template("Review", with_vars=True)
    win.slash_input.set_templates([tpl])

    # Activate the inline form
    win.slash_input._on_template_chosen(tpl)
    assert win.slash_input._inline_form.isVisible()

    # Guard precondition: is_palette_visible() must exist and return False here.
    # Fails before implementation: is_palette_visible() does not exist.
    assert not win.slash_input.is_palette_visible()

    received = []
    monkeypatch.setattr(win, "_handle_plain_input", lambda text: received.append(text))

    qtbot.keyPress(win, Qt.Key.Key_Return, Qt.KeyboardModifier.ControlModifier)

    assert len(received) == 0


# ---------------------------------------------------------------------------
# AC-3: Copy-output shortcut (_copy_last_output)
# ---------------------------------------------------------------------------


def test_copy_output_shortcut_copies_last_output(qtbot):
    """_copy_last_output() puts the last AI-generated text on the clipboard."""
    win = _make_window(qtbot)
    win._last_output = "This is the generated result."
    QApplication.clipboard().clear()

    # Fails before implementation: _copy_last_output() method does not exist
    win._copy_last_output()

    assert QApplication.clipboard().text() == "This is the generated result."


def test_copy_output_shortcut_no_op_when_no_output(qtbot):
    """_copy_last_output() does not modify the clipboard when _last_output is None."""
    win = _make_window(qtbot)
    win._last_output = None
    QApplication.clipboard().setText("pre-existing content")

    # Fails before implementation: _copy_last_output() method does not exist
    win._copy_last_output()

    assert QApplication.clipboard().text() == "pre-existing content"


# ---------------------------------------------------------------------------
# AC-5: Clear-chat shortcut (_clear_chat)
# ---------------------------------------------------------------------------


def test_clear_chat_shortcut_clears_thread(qtbot):
    """_clear_chat() removes all message bubbles from the chat widget."""
    from templatr.ui.message_bubble import MessageBubble

    win = _make_window(qtbot)
    win.chat_widget.add_user_message("Hello")
    win.chat_widget.add_ai_bubble()

    assert len(win.chat_widget.findChildren(MessageBubble)) > 0

    # Fails before implementation: _clear_chat() method does not exist
    win._clear_chat()

    assert len(win.chat_widget.findChildren(MessageBubble)) == 0


def test_clear_chat_shortcut_no_op_during_generation(qtbot):
    """_clear_chat() does nothing when a generation worker is running."""
    from templatr.ui.message_bubble import MessageBubble

    win = _make_window(qtbot)
    win.chat_widget.add_user_message("In progress")

    # Simulate a running worker
    win.worker = MagicMock()
    win.worker.isRunning.return_value = True

    # Fails before implementation: _clear_chat() method does not exist
    win._clear_chat()

    # Bubbles must remain — clear was blocked by running generation
    assert len(win.chat_widget.findChildren(MessageBubble)) > 0


# ---------------------------------------------------------------------------
# AC-4: Next/previous template navigation (_select_next_template / _select_prev_template)
# ---------------------------------------------------------------------------


def test_next_template_shortcut_advances_selection(qtbot):
    """_select_next_template() moves current_template to the next in list order."""
    templates = _make_three_templates()
    win = _make_window(qtbot, templates=templates)
    win.current_template = templates[0]  # Alpha

    # Fails before implementation: _select_next_template() method does not exist
    win._select_next_template()

    assert win.current_template is not None
    assert win.current_template.name == "Beta"


def test_prev_template_shortcut_reverses_selection(qtbot):
    """_select_prev_template() moves current_template to the previous in list order."""
    templates = _make_three_templates()
    win = _make_window(qtbot, templates=templates)
    win.current_template = templates[1]  # Beta

    # Fails before implementation: _select_prev_template() method does not exist
    win._select_prev_template()

    assert win.current_template is not None
    assert win.current_template.name == "Alpha"


def test_template_navigation_wraps_around(qtbot):
    """_select_next_template() wraps from the last template back to the first."""
    templates = _make_three_templates()
    win = _make_window(qtbot, templates=templates)
    win.current_template = templates[-1]  # Gamma (last)

    # Fails before implementation: _select_next_template() method does not exist
    win._select_next_template()

    assert win.current_template is not None
    assert win.current_template.name == "Alpha"


def test_template_navigation_prev_wraps_around(qtbot):
    """_select_prev_template() wraps from the first template back to the last."""
    templates = _make_three_templates()
    win = _make_window(qtbot, templates=templates)
    win.current_template = templates[0]  # Alpha (first)

    # Fails before implementation: _select_prev_template() method does not exist
    win._select_prev_template()

    assert win.current_template is not None
    assert win.current_template.name == "Gamma"


def test_template_navigation_no_op_when_no_templates(qtbot):
    """_select_next_template() does nothing gracefully when template list is empty."""
    win = _make_window(qtbot, templates=[])
    win.current_template = None

    # Fails before implementation: _select_next_template() method does not exist
    win._select_next_template()  # Must not raise

    assert win.current_template is None


# ---------------------------------------------------------------------------
# AC-7: /help lists all five keyboard shortcut actions
# ---------------------------------------------------------------------------


def test_help_command_lists_shortcuts(qtbot):
    """The /help system command output includes all five keyboard shortcut key strings."""
    from templatr.ui.message_bubble import MessageBubble

    win = _make_window(qtbot)
    win._on_system_command("help")

    bubbles = win.chat_widget.findChildren(MessageBubble)
    assert len(bubbles) > 0, "A help bubble should have been added to the chat"

    help_text = bubbles[-1].get_raw_text()

    # Fails before implementation: current help text has no shortcut key strings
    assert "Ctrl+Return" in help_text, "Help text should list the generate shortcut"
    assert "Ctrl+Shift+C" in help_text, "Help text should list the copy-output shortcut"
    assert "Ctrl+L" in help_text, "Help text should list the clear-chat shortcut"
    assert "Ctrl+]" in help_text, "Help text should list the next-template shortcut"
    assert "Ctrl+[" in help_text, "Help text should list the prev-template shortcut"
