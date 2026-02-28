"""Tests for shared template dialog utility helpers."""

from templatr.ui.template_dialog_utils import (
    extract_template_content,
    is_connection_error,
)


def test_extract_template_content_prefers_tagged_block() -> None:
    """Tagged content is extracted when the expected tag is present."""
    text = "before <generated_template>Hello {{name}}</generated_template> after"

    result = extract_template_content(text, tag_name="generated_template")

    assert result == "Hello {{name}}"


def test_extract_template_content_cleans_markdown_fence() -> None:
    """Markdown fenced output is unwrapped when no tag is present."""
    text = """```markdown
Line 1
Line 2
```"""

    result = extract_template_content(text, tag_name="generated_template")

    assert result == "Line 1\nLine 2"


def test_extract_template_content_returns_plain_text_when_no_tag() -> None:
    """Plain text output is returned unchanged except outer whitespace."""
    text = "\n  plain output  \n"

    result = extract_template_content(text, tag_name="generated_template")

    assert result == "plain output"


def test_is_connection_error_true_for_connection_error_instance() -> None:
    """ConnectionError exceptions are treated as transient connection failures."""
    assert is_connection_error(ConnectionError("refused")) is True


def test_is_connection_error_true_for_connection_refused_message() -> None:
    """Message heuristics detect connection failures from wrapped exceptions."""
    assert is_connection_error(RuntimeError("Connection refused by server")) is True


def test_is_connection_error_false_for_non_connection_error() -> None:
    """Unrelated exceptions are not treated as connection errors."""
    assert is_connection_error(ValueError("bad input")) is False
