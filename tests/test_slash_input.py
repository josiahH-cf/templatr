"""Tests for SlashInputWidget (chat-ui-core / slash-commands pulled forward).

Tests the compound input bar that handles:
- '/' command to show a filterable template palette
- Inline variable form for templates with variables
- Plain text submission
- LLM readiness and generating state control

These tests were written before the implementation (TDD).
"""

from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from templatr.ui.slash_input import SlashInputWidget

from templatr.core.templates import Template, Variable


def _make_template_no_vars():
    """Template with no variables — direct submission."""
    return Template(
        name="Quick Note",
        content="Write a quick note about productivity.",
        description="A no-variable template",
        variables=[],
    )


def _make_template_with_vars():
    """Template with two variables — inline form required."""
    return Template(
        name="Code Review",
        content="Review this code:\n\n{{code}}\n\nFocus on: {{focus}}",
        description="Code review template",
        variables=[
            Variable(name="code", label="Code", multiline=True),
            Variable(name="focus", label="Focus Area", default="correctness"),
        ],
    )


def _make_template_list():
    """List of templates for palette population."""
    return [_make_template_no_vars(), _make_template_with_vars()]


# -- Palette visibility tests ------------------------------------------------


def test_typing_slash_shows_palette(qtbot):
    """Typing '/' in the input bar makes the template palette visible."""
    widget = SlashInputWidget()
    qtbot.addWidget(widget)
    widget.set_templates(_make_template_list())

    qtbot.keyClicks(widget._text_input, "/")

    assert widget._palette.isVisible()


def test_palette_hidden_initially(qtbot):
    """Template palette is hidden when no '/' has been typed."""
    widget = SlashInputWidget()
    qtbot.addWidget(widget)
    widget.set_templates(_make_template_list())
    assert not widget._palette.isVisible()


def test_filter_narrows_results(qtbot):
    """Typing '/code' shows only templates containing 'code' in their name."""
    widget = SlashInputWidget()
    qtbot.addWidget(widget)
    widget.set_templates(_make_template_list())

    qtbot.keyClicks(widget._text_input, "/code")

    # Palette should be visible and filtered
    assert widget._palette.isVisible()
    visible_names = [
        widget._palette._list.item(i).text()
        for i in range(widget._palette._list.count())
        if widget._palette._list.item(i).isHidden() is False
    ]
    assert any("code" in name.lower() for name in visible_names)
    assert not any("quick note" in name.lower() for name in visible_names)


def test_escape_dismisses_palette(qtbot):
    """Pressing Escape hides the palette and clears the input."""
    widget = SlashInputWidget()
    qtbot.addWidget(widget)
    widget.set_templates(_make_template_list())

    qtbot.keyClicks(widget._text_input, "/")
    assert widget._palette.isVisible()

    QTest.keyClick(widget._text_input, Qt.Key.Key_Escape)

    assert not widget._palette.isVisible()
    assert widget._text_input.toPlainText() == ""


# -- Template selection tests ------------------------------------------------


def test_selecting_template_without_vars_emits_template_submitted(qtbot):
    """Selecting a no-variable template immediately emits template_submitted."""
    widget = SlashInputWidget()
    qtbot.addWidget(widget)
    no_vars = _make_template_no_vars()
    widget.set_templates([no_vars])

    with qtbot.waitSignal(widget.template_submitted, timeout=1000) as sig:
        widget._on_template_chosen(no_vars)

    assert sig.args[0] == no_vars.render({})


def test_selecting_template_with_vars_shows_inline_form(qtbot):
    """Selecting a template with variables shows the inline variable form."""
    widget = SlashInputWidget()
    qtbot.addWidget(widget)
    with_vars = _make_template_with_vars()
    widget.set_templates([with_vars])

    widget._on_template_chosen(with_vars)

    assert widget._inline_form.isVisible()


def test_inline_form_hidden_initially(qtbot):
    """Inline variable form is hidden when no template is active."""
    widget = SlashInputWidget()
    qtbot.addWidget(widget)
    assert not widget._inline_form.isVisible()


def test_filling_form_and_submitting_emits_template_submitted(qtbot):
    """Filling in the inline variable form and submitting emits template_submitted
    with the rendered prompt (variables substituted)."""
    widget = SlashInputWidget()
    qtbot.addWidget(widget)
    with_vars = _make_template_with_vars()
    widget.set_templates([with_vars])

    widget._on_template_chosen(with_vars)
    assert widget._inline_form.isVisible()

    with qtbot.waitSignal(widget.template_submitted, timeout=1000) as sig:
        widget._on_form_submitted({"code": "x = 1", "focus": "readability"})

    rendered = with_vars.render({"code": "x = 1", "focus": "readability"})
    assert sig.args[0] == rendered


def test_form_hides_after_submission(qtbot):
    """Inline variable form hides itself after a successful submission."""
    widget = SlashInputWidget()
    qtbot.addWidget(widget)
    with_vars = _make_template_with_vars()
    widget.set_templates([with_vars])
    widget._on_template_chosen(with_vars)

    widget._on_form_submitted({"code": "x = 1", "focus": "correctness"})

    assert not widget._inline_form.isVisible()


# -- Plain text submission tests ---------------------------------------------


def test_plain_submit_emits_plain_submitted(qtbot):
    """Clicking Send with plain text (no template) emits plain_submitted."""
    widget = SlashInputWidget()
    qtbot.addWidget(widget)
    widget.set_templates([])
    widget.set_llm_ready(True)

    widget._text_input.setPlainText("Tell me a joke")

    with qtbot.waitSignal(widget.plain_submitted, timeout=1000) as sig:
        widget._on_send_clicked()

    assert sig.args[0] == "Tell me a joke"


def test_plain_submit_clears_input(qtbot):
    """After plain text submission the input field is cleared."""
    widget = SlashInputWidget()
    qtbot.addWidget(widget)
    widget.set_templates([])
    widget.set_llm_ready(True)
    widget._text_input.setPlainText("Some text")
    widget._on_send_clicked()
    assert widget._text_input.toPlainText() == ""


# -- LLM readiness / generating state tests ---------------------------------


def test_set_llm_ready_enables_send_button(qtbot):
    """set_llm_ready(True) enables the Send button."""
    widget = SlashInputWidget()
    qtbot.addWidget(widget)
    widget.set_llm_ready(False)
    widget.set_llm_ready(True)
    assert widget._send_btn.isEnabled()


def test_set_llm_not_ready_disables_send_button(qtbot):
    """set_llm_ready(False) disables the Send button."""
    widget = SlashInputWidget()
    qtbot.addWidget(widget)
    widget.set_llm_ready(False)
    assert not widget._send_btn.isEnabled()


def test_set_generating_disables_input(qtbot):
    """set_generating(True) disables the text input and Send button."""
    widget = SlashInputWidget()
    qtbot.addWidget(widget)
    widget.set_llm_ready(True)
    widget.set_generating(True)
    assert not widget._text_input.isEnabled()


def test_set_generating_false_re_enables_input(qtbot):
    """set_generating(False) re-enables the text input and Send button."""
    widget = SlashInputWidget()
    qtbot.addWidget(widget)
    widget.set_llm_ready(True)
    widget.set_generating(True)
    widget.set_generating(False)
    assert widget._text_input.isEnabled()


def test_set_waiting_message_updates_status(qtbot):
    """set_waiting_message shows a status message while server is starting."""
    widget = SlashInputWidget()
    qtbot.addWidget(widget)
    widget.set_waiting_message(1, 3)
    # Status label should contain attempt info — not empty
    assert widget._status_label.text() != ""
