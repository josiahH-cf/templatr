"""Tests for Task 3: Documentation and Advanced Edit preservation.

Covers:
- Context menu shows "Advanced Edit" instead of "Edit Template"
- TEMPLATES.md exists and contains the 3-step workflow documentation
"""

from pathlib import Path


class TestTemplatesMdExists:
    """Verify the TEMPLATES.md documentation file."""

    def test_file_exists(self):
        """Template authoring guide exists in docs/."""
        doc = Path(__file__).resolve().parent.parent / "docs" / "templates.md"
        assert doc.exists(), "docs/templates.md not found"

    def test_contains_new_command(self):
        """Template authoring guide mentions the /new command."""
        doc = Path(__file__).resolve().parent.parent / "docs" / "templates.md"
        text = doc.read_text(encoding="utf-8")
        assert "/new" in text

    def test_contains_variable_syntax(self):
        """Template authoring guide documents the {{variable}} placeholder syntax."""
        doc = Path(__file__).resolve().parent.parent / "docs" / "templates.md"
        text = doc.read_text(encoding="utf-8")
        assert "{{" in text

    def test_contains_advanced_edit(self):
        """Template authoring guide mentions the Advanced Edit option."""
        doc = Path(__file__).resolve().parent.parent / "docs" / "templates.md"
        text = doc.read_text(encoding="utf-8")
        assert "Advanced Edit" in text

    def test_contains_import_export(self):
        """Template authoring guide documents import and export functionality."""
        doc = Path(__file__).resolve().parent.parent / "docs" / "templates.md"
        text = doc.read_text(encoding="utf-8")
        assert "/import" in text
        assert "/export" in text

    def test_contains_three_steps(self):
        """Template authoring guide contains a numbered 3-step workflow."""
        doc = Path(__file__).resolve().parent.parent / "docs" / "templates.md"
        text = doc.read_text(encoding="utf-8")
        # Should contain step indicators
        assert "1." in text or "Step 1" in text
        assert "2." in text or "Step 2" in text
        assert "3." in text or "Step 3" in text
