"""Tests for Template Rename feature.

Covers: TemplateManager.rename() backend (AC1), rename_requested signal (AC2),
context menu action (AC3), _template_actions handler (AC4).
Spec: /specs/template-rename.md
"""

import pytest

from templatr.core.templates import TemplateManager


# ---------------------------------------------------------------------------
# AC1 — TemplateManager.rename() backend
# ---------------------------------------------------------------------------


class TestRenameBackend:
    """Tests for TemplateManager.rename()."""

    def test_rename_returns_updated_template(self, tmp_path):
        """rename() returns the template with the new name set."""
        mgr = TemplateManager(templates_dir=tmp_path)
        original = mgr.create("Old Name", content="Hello")

        updated = mgr.rename(original, "New Name")

        assert updated.name == "New Name"

    def test_rename_saves_new_file_on_disk(self, tmp_path):
        """rename() writes a new JSON file for the new name."""
        mgr = TemplateManager(templates_dir=tmp_path)
        original = mgr.create("Old Name", content="Hello")

        updated = mgr.rename(original, "New Name")

        assert updated._path is not None
        assert updated._path.exists()
        assert "new_name" in updated._path.name

    def test_rename_removes_old_file(self, tmp_path):
        """rename() deletes the original JSON file."""
        mgr = TemplateManager(templates_dir=tmp_path)
        original = mgr.create("Old Name", content="Hello")
        old_path = original._path

        mgr.rename(original, "New Name")

        assert not old_path.exists()

    def test_rename_template_retrievable_by_new_name(self, tmp_path):
        """Renamed template can be found via get(new_name)."""
        mgr = TemplateManager(templates_dir=tmp_path)
        original = mgr.create("Old Name", content="Hello")

        mgr.rename(original, "New Name")

        found = mgr.get("New Name")
        assert found is not None
        assert found.name == "New Name"

    def test_rename_old_name_no_longer_findable(self, tmp_path):
        """After rename, get(old_name) returns None."""
        mgr = TemplateManager(templates_dir=tmp_path)
        original = mgr.create("Old Name", content="Hello")

        mgr.rename(original, "New Name")

        assert mgr.get("Old Name") is None

    def test_rename_raises_on_empty_name(self, tmp_path):
        """rename() raises ValueError when new_name is blank."""
        mgr = TemplateManager(templates_dir=tmp_path)
        original = mgr.create("Old Name", content="Hello")

        with pytest.raises(ValueError, match="empty"):
            mgr.rename(original, "   ")

    def test_rename_raises_on_name_conflict(self, tmp_path):
        """rename() raises ValueError when new_name is already in use."""
        mgr = TemplateManager(templates_dir=tmp_path)
        original = mgr.create("Old Name", content="Hello")
        mgr.create("Taken Name", content="World")

        with pytest.raises(ValueError, match="already exists"):
            mgr.rename(original, "Taken Name")

    def test_rename_same_name_is_a_no_op(self, tmp_path):
        """Renaming to the same name succeeds without error."""
        mgr = TemplateManager(templates_dir=tmp_path)
        original = mgr.create("Same Name", content="Hello")

        updated = mgr.rename(original, "Same Name")

        assert updated.name == "Same Name"

    def test_rename_moves_version_history_dir(self, tmp_path):
        """rename() renames the version history directory to match the new slug."""
        mgr = TemplateManager(templates_dir=tmp_path)
        original = mgr.create("Old Name", content="v1")
        # Create a version so the history dir exists
        mgr.save(original)
        mgr.create_version(original)
        old_slug = original.filename.replace(".json", "")

        updated = mgr.rename(original, "New Name")

        new_slug = updated.filename.replace(".json", "")
        new_version_dir = mgr._versions_dir / new_slug
        old_version_dir = mgr._versions_dir / old_slug

        assert new_version_dir.exists()
        assert not old_version_dir.exists()

    def test_rename_preserves_content(self, tmp_path):
        """rename() does not alter template content, description, or variables."""
        mgr = TemplateManager(templates_dir=tmp_path)
        original = mgr.create(
            "Old Name",
            content="Hello {{name}}",
            description="My desc",
            variables=[{"name": "name", "label": "Name", "default": "World"}],
        )

        updated = mgr.rename(original, "New Name")

        assert updated.content == "Hello {{name}}"
        assert updated.description == "My desc"
        assert len(updated.variables) == 1
        assert updated.variables[0].name == "name"


# ---------------------------------------------------------------------------
# AC2 + AC3 — UI signal and context menu
# ---------------------------------------------------------------------------


class TestRenameInTree:
    """Tests for rename_requested signal and context menu."""

    def test_tree_has_rename_requested_signal(self):
        """TemplateTreeWidget exposes a rename_requested signal."""
        from templatr.ui.template_tree import TemplateTreeWidget

        assert hasattr(TemplateTreeWidget, "rename_requested")

    def test_rename_action_in_context_menu(self, qtbot, tmp_path, monkeypatch):
        """Context menu for a template includes a 'Rename...' action."""
        import templatr.ui.template_tree as tree_module
        from templatr.ui.template_tree import TemplateTreeWidget

        mgr = TemplateManager(templates_dir=tmp_path)
        mgr.create("My Template", content="Hello")
        monkeypatch.setattr(tree_module, "get_template_manager", lambda: mgr)

        widget = TemplateTreeWidget()
        qtbot.addWidget(widget)
        widget.load_templates()

        # Signal is connectable
        received = []
        widget.rename_requested.connect(lambda t: received.append(t))
        assert widget.rename_requested is not None


# ---------------------------------------------------------------------------
# AC4 — Handler existence
# ---------------------------------------------------------------------------


class TestRenameHandler:
    """Tests for the _rename_template handler."""

    def test_handler_exists(self):
        """TemplateActionsMixin exposes a _rename_template method."""
        from templatr.ui._template_actions import TemplateActionsMixin

        assert hasattr(TemplateActionsMixin, "_rename_template")
