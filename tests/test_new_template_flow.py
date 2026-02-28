"""Tests for Task 1: /new quick-create flow with auto-detect variables.

Covers:
- auto_detect_variables: regex extraction, deduplication, edge cases
- NewTemplateFlow: conversational state machine, conflict detection, cancellation
- Integration: created template appears in TemplateManager.list_all()
"""

import json
from pathlib import Path

import pytest

from templatr.core.templates import (
    Template,
    TemplateManager,
    Variable,
    auto_detect_variables,
)
from templatr.ui.new_template_flow import NewTemplateFlow


# ---------------------------------------------------------------------------
# auto_detect_variables unit tests
# ---------------------------------------------------------------------------


class TestAutoDetectVariables:
    """Tests for the auto_detect_variables() utility function."""

    def test_basic_detection(self):
        """Detects simple {{word}} placeholders and returns Variable objects."""
        content = "Hello {{name}}, your {{topic}} is ready"
        result = auto_detect_variables(content)
        assert len(result) == 2
        assert result[0].name == "name"
        assert result[1].name == "topic"
        for v in result:
            assert isinstance(v, Variable)
            assert v.default == ""
            assert v.multiline is False

    def test_deduplication(self):
        """Duplicate placeholder names produce only one Variable."""
        content = "{{a}} and {{b}} and {{a}}"
        result = auto_detect_variables(content)
        names = [v.name for v in result]
        assert names == ["a", "b"]

    def test_empty_content(self):
        """Content with no placeholders returns an empty list."""
        assert auto_detect_variables("no placeholders here") == []

    def test_empty_string(self):
        """Empty string returns an empty list."""
        assert auto_detect_variables("") == []

    def test_preserves_first_seen_order(self):
        """Variables appear in first-seen order, not alphabetical."""
        content = "{{zebra}} then {{apple}} then {{mango}}"
        result = auto_detect_variables(content)
        names = [v.name for v in result]
        assert names == ["zebra", "apple", "mango"]

    def test_label_generated_from_name(self):
        """Variable labels are title-cased from the name."""
        content = "{{user_name}}"
        result = auto_detect_variables(content)
        assert result[0].label == "User Name"

    def test_underscores_in_name(self):
        """Underscored names are valid placeholders."""
        content = "{{first_name}} {{last_name}}"
        result = auto_detect_variables(content)
        assert len(result) == 2
        assert result[0].name == "first_name"

    def test_ignores_nested_braces(self):
        """Non-word content inside braces is ignored (e.g., spaces, nested)."""
        content = "{{ spaced }} and {{{nested}}} and {{valid}}"
        result = auto_detect_variables(content)
        # Only {{valid}} matches \w+ pattern (no spaces)
        names = [v.name for v in result]
        assert "valid" in names
        # {{ spaced }} should NOT match because of spaces
        assert "spaced" not in names

    def test_numeric_names(self):
        """Numeric-only names are valid \\w+ matches."""
        content = "Item {{123}}"
        result = auto_detect_variables(content)
        assert len(result) == 1
        assert result[0].name == "123"


# ---------------------------------------------------------------------------
# NewTemplateFlow unit tests
# ---------------------------------------------------------------------------


class TestNewTemplateFlow:
    """Tests for the conversational /new template creation flow."""

    @pytest.fixture
    def manager(self, tmp_path: Path) -> TemplateManager:
        """TemplateManager with an isolated temporary directory."""
        return TemplateManager(tmp_path)

    @pytest.fixture
    def flow(self, manager: TemplateManager) -> NewTemplateFlow:
        """A fresh NewTemplateFlow instance."""
        return NewTemplateFlow(manager)

    def test_initial_prompt(self, flow: NewTemplateFlow):
        """Starting the flow returns the name prompt message."""
        messages = flow.start()
        assert len(messages) >= 1
        assert "name" in messages[0].lower() or "called" in messages[0].lower()

    def test_happy_path(self, flow: NewTemplateFlow, manager: TemplateManager):
        """Full flow: name → content → template saved and signal data returned."""
        flow.start()

        # Step 1: provide a name
        result = flow.handle_input("My Test Template")
        assert result.done is False
        assert "content" in result.message.lower() or "paste" in result.message.lower()

        # Step 2: provide content with variables
        result = flow.handle_input(
            "Summarize {{topic}} in {{num_sentences}} sentences"
        )
        assert result.done is True
        assert result.template is not None
        assert result.template.name == "My Test Template"
        assert len(result.template.variables) == 2

        # Verify template was actually saved
        saved = manager.get("My Test Template")
        assert saved is not None
        assert saved.name == "My Test Template"

    def test_content_without_variables(
        self, flow: NewTemplateFlow, manager: TemplateManager
    ):
        """Content with no placeholders still creates a template (0 variables)."""
        flow.start()
        flow.handle_input("Plain Template")
        result = flow.handle_input("Just a plain prompt with no variables")
        assert result.done is True
        assert result.template is not None
        assert len(result.template.variables) == 0

    def test_name_conflict(self, flow: NewTemplateFlow, manager: TemplateManager):
        """Providing a name that already exists shows an error, stays in name state."""
        # Pre-create a template
        manager.create("Existing", "some content")

        flow.start()
        result = flow.handle_input("Existing")
        assert result.done is False
        assert "already exists" in result.message.lower() or "taken" in result.message.lower()

        # Should still accept a different name
        result = flow.handle_input("Unique Name")
        assert result.done is False  # now asking for content

    def test_cancel_command(self, flow: NewTemplateFlow):
        """Typing /cancel during the flow cancels it."""
        flow.start()
        result = flow.handle_input("/cancel")
        assert result.done is True
        assert result.template is None
        assert result.cancelled is True

    def test_cancel_during_content(self, flow: NewTemplateFlow):
        """Cancellation works at the content step too."""
        flow.start()
        flow.handle_input("Some Name")
        result = flow.handle_input("/cancel")
        assert result.done is True
        assert result.template is None
        assert result.cancelled is True

    def test_empty_name_rejected(self, flow: NewTemplateFlow):
        """Empty or whitespace-only name is rejected."""
        flow.start()
        result = flow.handle_input("   ")
        assert result.done is False
        assert "name" in result.message.lower()

    def test_template_available_as_command(
        self, flow: NewTemplateFlow, manager: TemplateManager
    ):
        """After creation, the template appears in list_all()."""
        flow.start()
        flow.handle_input("New Command")
        flow.handle_input("Do {{action}} on {{target}}")

        templates = manager.list_all()
        names = [t.name for t in templates]
        assert "New Command" in names

    def test_variables_in_result_message(self, flow: NewTemplateFlow):
        """The confirmation message mentions discovered variables."""
        flow.start()
        flow.handle_input("Var Test")
        result = flow.handle_input("Please {{summarize}} the {{document}}")
        assert "summarize" in result.message
        assert "document" in result.message

    def test_no_variables_in_result_message(self, flow: NewTemplateFlow):
        """When no variables found, confirmation message says so."""
        flow.start()
        flow.handle_input("No Vars")
        result = flow.handle_input("Just a plain prompt")
        assert result.done is True
        # Should confirm save without mentioning variables
        assert "saved" in result.message.lower() or "created" in result.message.lower()
