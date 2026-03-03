"""Tests for the version history browser dialog.

Covers: dialog creation, version list population, content preview
on selection, restore action, and empty history handling.
"""

from unittest import mock

from templatr.core.templates import Template, TemplateVersion


# ---------------------------------------------------------------------------
# Helper: create test versions
# ---------------------------------------------------------------------------


def _make_version(num: int, note: str = "", content: str = "content") -> TemplateVersion:
    """Create a TemplateVersion for testing."""
    return TemplateVersion(
        version=num,
        timestamp=f"2026-03-0{num}T12:00:00",
        note=note,
        template_data={
            "name": "Test Template",
            "content": f"{content} v{num}",
            "description": f"Version {num}",
        },
    )


def _make_template(name: str = "Test Template") -> Template:
    """Create a Template for testing."""
    return Template(name=name, content="current content", description="A test template")


# ---------------------------------------------------------------------------
# Dialog creation tests
# ---------------------------------------------------------------------------


class TestVersionHistoryDialogCreation:
    """Tests for VersionHistoryDialog instantiation."""

    def test_dialog_creates_without_error(self, qtbot):
        """Dialog can be instantiated with a template and versions."""
        from templatr.ui.version_history import VersionHistoryDialog

        template = _make_template()
        versions = [_make_version(1, "Original"), _make_version(2, "Improved")]

        dialog = VersionHistoryDialog(template=template, versions=versions)
        qtbot.addWidget(dialog)
        assert dialog.windowTitle() == "Version History — Test Template"

    def test_dialog_with_empty_versions(self, qtbot):
        """Dialog handles empty version list gracefully."""
        from templatr.ui.version_history import VersionHistoryDialog

        template = _make_template()

        dialog = VersionHistoryDialog(template=template, versions=[])
        qtbot.addWidget(dialog)
        # Should still create without error
        assert dialog.version_list.count() == 0

    def test_dialog_has_restore_button(self, qtbot):
        """Dialog has a Restore button."""
        from templatr.ui.version_history import VersionHistoryDialog

        template = _make_template()
        versions = [_make_version(1)]

        dialog = VersionHistoryDialog(template=template, versions=versions)
        qtbot.addWidget(dialog)
        assert dialog.restore_btn is not None
        assert "Restore" in dialog.restore_btn.text()


# ---------------------------------------------------------------------------
# Version list population tests
# ---------------------------------------------------------------------------


class TestVersionListPopulation:
    """Tests for the version list display."""

    def test_versions_listed_in_order(self, qtbot):
        """Versions appear in the list with most recent first."""
        from templatr.ui.version_history import VersionHistoryDialog

        template = _make_template()
        versions = [
            _make_version(1, "Original"),
            _make_version(2, "Improved"),
            _make_version(3, "Further refined"),
        ]

        dialog = VersionHistoryDialog(template=template, versions=versions)
        qtbot.addWidget(dialog)

        # Should have 3 items
        assert dialog.version_list.count() == 3

        # Most recent first
        first_item = dialog.version_list.item(0).text()
        assert "v3" in first_item

    def test_version_labels_include_note(self, qtbot):
        """Version labels include the note text."""
        from templatr.ui.version_history import VersionHistoryDialog

        template = _make_template()
        versions = [_make_version(1, "Original snapshot")]

        dialog = VersionHistoryDialog(template=template, versions=versions)
        qtbot.addWidget(dialog)

        item_text = dialog.version_list.item(0).text()
        assert "Original snapshot" in item_text

    def test_version_labels_include_timestamp(self, qtbot):
        """Version labels include the timestamp."""
        from templatr.ui.version_history import VersionHistoryDialog

        template = _make_template()
        versions = [_make_version(1)]

        dialog = VersionHistoryDialog(template=template, versions=versions)
        qtbot.addWidget(dialog)

        item_text = dialog.version_list.item(0).text()
        assert "2026-03-01" in item_text


# ---------------------------------------------------------------------------
# Content preview tests
# ---------------------------------------------------------------------------


class TestContentPreview:
    """Tests for the content preview pane."""

    def test_selecting_version_shows_content(self, qtbot):
        """Selecting a version displays its template content in the preview."""
        from templatr.ui.version_history import VersionHistoryDialog

        template = _make_template()
        versions = [_make_version(1, content="Hello world")]

        dialog = VersionHistoryDialog(template=template, versions=versions)
        qtbot.addWidget(dialog)

        # Select the first item
        dialog.version_list.setCurrentRow(0)

        preview_text = dialog.preview_pane.toPlainText()
        assert "Hello world v1" in preview_text

    def test_preview_is_read_only(self, qtbot):
        """Preview pane is read-only."""
        from templatr.ui.version_history import VersionHistoryDialog

        template = _make_template()
        versions = [_make_version(1)]

        dialog = VersionHistoryDialog(template=template, versions=versions)
        qtbot.addWidget(dialog)

        assert dialog.preview_pane.isReadOnly()


# ---------------------------------------------------------------------------
# Restore action tests
# ---------------------------------------------------------------------------


class TestRestoreAction:
    """Tests for the restore button behavior."""

    def test_restore_emits_signal_with_version(self, qtbot):
        """Clicking Restore emits the version_restored signal."""
        from templatr.ui.version_history import VersionHistoryDialog

        template = _make_template()
        versions = [_make_version(1), _make_version(2, "Better")]

        dialog = VersionHistoryDialog(template=template, versions=versions)
        qtbot.addWidget(dialog)

        # Select the second item (v1, since list is reversed)
        dialog.version_list.setCurrentRow(1)

        with qtbot.waitSignal(dialog.version_restored, timeout=1000) as sig:
            dialog.restore_btn.click()

        assert sig.args[0] == 1  # version number

    def test_restore_button_disabled_with_no_selection(self, qtbot):
        """Restore button is disabled when no version is selected."""
        from templatr.ui.version_history import VersionHistoryDialog

        template = _make_template()
        versions = [_make_version(1)]

        dialog = VersionHistoryDialog(template=template, versions=versions)
        qtbot.addWidget(dialog)

        # Clear selection
        dialog.version_list.clearSelection()
        dialog.version_list.setCurrentRow(-1)

        assert not dialog.restore_btn.isEnabled()


# ---------------------------------------------------------------------------
# Integration with _template_actions tests
# ---------------------------------------------------------------------------


class TestTemplateActionsIntegration:
    """Tests that _show_version_history uses the new dialog."""

    def test_no_qinputdialog_import(self):
        """_template_actions should no longer use QInputDialog for versions."""
        import inspect

        from templatr.ui._template_actions import TemplateActionsMixin

        source = inspect.getsource(TemplateActionsMixin._show_version_history)
        assert "QInputDialog" not in source, (
            "_show_version_history should use VersionHistoryDialog, not QInputDialog"
        )
