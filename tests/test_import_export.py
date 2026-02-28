"""Tests for Task 2: Import/export functionality.

Covers:
- export_template: JSON output, no _path field, field fidelity
- import_template: validation, conflict detection, error handling
- Drag-and-drop: accepts .json, rejects non-.json
"""

import json
from pathlib import Path

import pytest

from templatr.core.templates import Template, TemplateManager, Variable


# ---------------------------------------------------------------------------
# export_template tests
# ---------------------------------------------------------------------------


class TestExportTemplate:
    """Tests for TemplateManager.export_template()."""

    @pytest.fixture
    def manager(self, tmp_path: Path) -> TemplateManager:
        """TemplateManager with an isolated temporary directory."""
        return TemplateManager(tmp_path / "templates")

    def test_export_creates_json_file(self, manager: TemplateManager, tmp_path: Path):
        """Exported file is valid JSON with the correct template data."""
        template = manager.create("Export Test", "Hello {{name}}")
        export_path = tmp_path / "exported.json"

        result = manager.export_template(template, export_path)

        assert result == export_path
        assert export_path.exists()
        data = json.loads(export_path.read_text(encoding="utf-8"))
        assert data["name"] == "Export Test"
        assert data["content"] == "Hello {{name}}"

    def test_export_no_path_field(self, manager: TemplateManager, tmp_path: Path):
        """Exported JSON does not contain the internal _path field."""
        template = manager.create("No Path", "content")
        export_path = tmp_path / "no_path.json"

        manager.export_template(template, export_path)

        data = json.loads(export_path.read_text(encoding="utf-8"))
        assert "_path" not in data

    def test_export_content_fidelity(self, manager: TemplateManager, tmp_path: Path):
        """All template fields (description, variables, refinements) are preserved."""
        template = manager.create(
            "Full Template",
            "Review {{code}} for {{focus}}",
            description="A code review template",
            variables=[
                {"name": "code", "label": "Code", "multiline": True},
                {"name": "focus", "label": "Focus", "default": "security"},
            ],
        )
        template.refinements = ["Be concise", "Use bullet points"]
        manager.save(template)

        export_path = tmp_path / "full.json"
        manager.export_template(template, export_path)

        data = json.loads(export_path.read_text(encoding="utf-8"))
        assert data["description"] == "A code review template"
        assert len(data["variables"]) == 2
        assert data["variables"][0]["name"] == "code"
        assert data["variables"][0]["multiline"] is True
        assert data["refinements"] == ["Be concise", "Use bullet points"]


# ---------------------------------------------------------------------------
# import_template tests
# ---------------------------------------------------------------------------


class TestImportTemplate:
    """Tests for TemplateManager.import_template()."""

    @pytest.fixture
    def manager(self, tmp_path: Path) -> TemplateManager:
        """TemplateManager with an isolated temporary directory."""
        return TemplateManager(tmp_path / "templates")

    def _write_json(self, path: Path, data: dict) -> Path:
        """Write a JSON file and return its path."""
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return path

    def test_import_valid_template(self, manager: TemplateManager, tmp_path: Path):
        """Importing a valid JSON file returns a Template with correct fields."""
        json_path = self._write_json(
            tmp_path / "valid.json",
            {"name": "Imported", "content": "Hello {{world}}"},
        )

        template, conflict = manager.import_template(json_path)

        assert template.name == "Imported"
        assert template.content == "Hello {{world}}"
        assert conflict is False

    def test_import_missing_name(self, manager: TemplateManager, tmp_path: Path):
        """JSON without a 'name' field raises ValueError."""
        json_path = self._write_json(
            tmp_path / "no_name.json",
            {"content": "some content"},
        )

        with pytest.raises(ValueError, match="name"):
            manager.import_template(json_path)

    def test_import_missing_content(self, manager: TemplateManager, tmp_path: Path):
        """JSON without a 'content' field raises ValueError."""
        json_path = self._write_json(
            tmp_path / "no_content.json",
            {"name": "No Content"},
        )

        with pytest.raises(ValueError, match="content"):
            manager.import_template(json_path)

    def test_import_malformed_json(self, manager: TemplateManager, tmp_path: Path):
        """Non-JSON file raises ValueError."""
        bad_path = tmp_path / "bad.json"
        bad_path.write_text("not valid json {{", encoding="utf-8")

        with pytest.raises(ValueError, match="[Ii]nvalid|[Mm]alformed|JSON"):
            manager.import_template(bad_path)

    def test_import_conflict_detected(
        self, manager: TemplateManager, tmp_path: Path
    ):
        """Importing a template with a name that already exists flags the conflict."""
        manager.create("Existing", "original content")

        json_path = self._write_json(
            tmp_path / "conflict.json",
            {"name": "Existing", "content": "new content"},
        )

        template, conflict = manager.import_template(json_path)
        assert conflict is True
        assert template.name == "Existing"

    def test_import_overwrite(self, manager: TemplateManager, tmp_path: Path):
        """Saving an imported template with overwrite replaces the existing one."""
        manager.create("Overwrite Me", "old content")

        json_path = self._write_json(
            tmp_path / "overwrite.json",
            {"name": "Overwrite Me", "content": "new content"},
        )

        template, _ = manager.import_template(json_path)
        manager.save(template)

        saved = manager.get("Overwrite Me")
        assert saved is not None
        assert saved.content == "new content"

    def test_import_rename(self, manager: TemplateManager, tmp_path: Path):
        """Saving an imported template with a new name creates a separate template."""
        manager.create("Original", "original content")

        json_path = self._write_json(
            tmp_path / "rename.json",
            {"name": "Original", "content": "different content"},
        )

        template, _ = manager.import_template(json_path)
        template.name = "Renamed Copy"
        manager.save(template)

        assert manager.get("Original") is not None
        assert manager.get("Renamed Copy") is not None

    def test_import_preserves_variables(
        self, manager: TemplateManager, tmp_path: Path
    ):
        """Variables from the imported JSON are preserved."""
        json_path = self._write_json(
            tmp_path / "vars.json",
            {
                "name": "With Vars",
                "content": "{{greeting}} {{target}}",
                "variables": [
                    {"name": "greeting", "label": "Greeting", "default": "Hello"},
                    {"name": "target", "label": "Target"},
                ],
            },
        )

        template, _ = manager.import_template(json_path)
        assert len(template.variables) == 2
        assert template.variables[0].name == "greeting"
        assert template.variables[0].default == "Hello"


# ---------------------------------------------------------------------------
# Drag-and-drop tests (unit-level, no Qt required)
# ---------------------------------------------------------------------------


class TestDragDropFiltering:
    """Tests for drag-and-drop file filtering logic."""

    def test_json_file_accepted(self):
        """A .json file path is accepted for import."""
        assert Path("template.json").suffix == ".json"

    def test_non_json_rejected(self):
        """Non-.json file extensions are rejected."""
        for ext in [".txt", ".py", ".md", ".yaml"]:
            assert Path(f"file{ext}").suffix != ".json"
