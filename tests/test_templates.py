"""Tests for automatr.core.templates — TemplateManager CRUD, versioning, folders, and rendering.

Covers: load from directory, save new, update existing, delete, version creation,
version listing and restore, folder creation and movement, Template.render(),
and loading templates that contain unknown fields (e.g., 'trigger').
"""

import json
from pathlib import Path

from automatr.core.templates import Template, TemplateManager, Variable

# ---------------------------------------------------------------------------
# 1. Load templates from directory
# ---------------------------------------------------------------------------


def test_list_all_returns_templates(tmp_templates_dir: Path) -> None:
    """TemplateManager.list_all() returns all JSON templates in the directory."""
    mgr = TemplateManager(templates_dir=tmp_templates_dir)
    templates = mgr.list_all()
    assert len(templates) == 3
    names = {t.name for t in templates}
    assert "Code Review" in names
    assert "Summarize Text" in names
    assert "Simple Greeting" in names


def test_list_all_sorted_by_name(tmp_templates_dir: Path) -> None:
    """list_all() returns templates sorted alphabetically by name."""
    mgr = TemplateManager(templates_dir=tmp_templates_dir)
    templates = mgr.list_all()
    names = [t.name for t in templates]
    assert names == sorted(names, key=str.lower)


# ---------------------------------------------------------------------------
# 2. Save a new template
# ---------------------------------------------------------------------------


def test_save_new_template_creates_json_file(tmp_path: Path) -> None:
    """Saving a new Template writes a JSON file to the templates dir."""
    mgr = TemplateManager(templates_dir=tmp_path)
    template = Template(name="My New Template", content="Hello {{name}}")
    result = mgr.save(template)

    assert result is True
    expected = tmp_path / "my_new_template.json"
    assert expected.exists()
    data = json.loads(expected.read_text())
    assert data["name"] == "My New Template"
    assert data["content"] == "Hello {{name}}"


def test_create_helper_saves_and_returns_template(tmp_path: Path) -> None:
    """TemplateManager.create() saves template and returns the object."""
    mgr = TemplateManager(templates_dir=tmp_path)
    template = mgr.create(
        name="Quick Template",
        content="Summarize: {{text}}",
        description="A quick test template",
        variables=[{"name": "text", "label": "Text"}],
    )
    assert template.name == "Quick Template"
    assert (tmp_path / "quick_template.json").exists()


# ---------------------------------------------------------------------------
# 3. Update an existing template
# ---------------------------------------------------------------------------


def test_update_existing_template(tmp_path: Path) -> None:
    """Saving a template with an existing _path overwrites the file."""
    mgr = TemplateManager(templates_dir=tmp_path)
    template = mgr.create(name="Editable", content="Original content")

    template.content = "Updated content"
    result = mgr.save(template)

    assert result is True
    data = json.loads(template._path.read_text())
    assert data["content"] == "Updated content"


# ---------------------------------------------------------------------------
# 4. Delete a template
# ---------------------------------------------------------------------------


def test_delete_template_removes_file(tmp_path: Path) -> None:
    """TemplateManager.delete() removes the template's JSON file."""
    mgr = TemplateManager(templates_dir=tmp_path)
    template = mgr.create(name="Ephemeral", content="Gone soon")
    assert template._path.exists()

    result = mgr.delete(template)
    assert result is True
    assert not template._path.exists()


def test_delete_template_without_path_returns_false(tmp_path: Path) -> None:
    """Deleting a Template with no _path returns False without raising."""
    mgr = TemplateManager(templates_dir=tmp_path)
    template = Template(name="Ghost", content="No path set")
    result = mgr.delete(template)
    assert result is False


# ---------------------------------------------------------------------------
# 5. Version creation on save
# ---------------------------------------------------------------------------


def test_create_version_saves_snapshot(tmp_path: Path) -> None:
    """create_version() saves a versioned JSON file under _versions/."""
    mgr = TemplateManager(templates_dir=tmp_path)
    template = mgr.create(name="Versioned", content="v1 content")

    version = mgr.create_version(template, note="initial")
    assert version is not None
    assert version.version == 1
    version_dir = tmp_path / "_versions" / "versioned"
    assert (version_dir / "v1.json").exists()


def test_create_multiple_versions_increments(tmp_path: Path) -> None:
    """Each call to create_version() increments the version number."""
    mgr = TemplateManager(templates_dir=tmp_path)
    template = mgr.create(name="MultiVer", content="first")

    v1 = mgr.create_version(template, note="first")
    template.content = "second"
    v2 = mgr.create_version(template, note="second")

    assert v1.version == 1
    assert v2.version == 2


# ---------------------------------------------------------------------------
# 6. Version listing and restore
# ---------------------------------------------------------------------------


def test_list_versions_returns_sorted(tmp_path: Path) -> None:
    """list_versions() returns versions sorted by version number ascending."""
    mgr = TemplateManager(templates_dir=tmp_path)
    template = mgr.create(name="ListVer", content="original")
    mgr.create_version(template, note="v1")
    template.content = "modified"
    mgr.create_version(template, note="v2")

    versions = mgr.list_versions(template)
    assert len(versions) == 2
    assert versions[0].version < versions[1].version


def test_restore_version_applies_old_content(tmp_path: Path) -> None:
    """restore_version() rewrites the template file with the old content."""
    mgr = TemplateManager(templates_dir=tmp_path)
    template = mgr.create(name="RestoreMe", content="original content")
    mgr.create_version(template, note="snapshot")

    template.content = "changed content"
    mgr.save(template)

    restored = mgr.restore_version(template, version_num=1, create_backup=False)
    assert restored is not None
    assert restored.content == "original content"


# ---------------------------------------------------------------------------
# 7. Folder creation and template movement
# ---------------------------------------------------------------------------


def test_create_folder(tmp_path: Path) -> None:
    """create_folder() creates a subdirectory inside the templates dir."""
    mgr = TemplateManager(templates_dir=tmp_path)
    result = mgr.create_folder("Writing")
    assert result is True
    assert (tmp_path / "Writing").is_dir()


def test_save_to_folder_places_template_in_subfolder(tmp_path: Path) -> None:
    """save_to_folder() writes the template JSON into the specified folder."""
    mgr = TemplateManager(templates_dir=tmp_path)
    mgr.create_folder("Code")
    template = Template(name="Folder Test", content="In a folder")

    result = mgr.save_to_folder(template, folder="Code")
    assert result is True
    assert (tmp_path / "Code" / "folder_test.json").exists()


# ---------------------------------------------------------------------------
# 8. Template.render() with variable substitution
# ---------------------------------------------------------------------------


def test_render_substitutes_variables(sample_template: Template) -> None:
    """Template.render() replaces {{variable}} placeholders with supplied values."""
    result = sample_template.render({"recipient": "Alice", "message_type": "welcome"})
    assert "Alice" in result
    assert "welcome" in result
    assert "{{" not in result


def test_render_uses_defaults_for_missing_values(sample_template: Template) -> None:
    """Template.render() falls back to Variable.default when a value is missing."""
    result = sample_template.render({})
    assert "World" in result   # default for 'recipient'
    assert "test" in result    # default for 'message_type'


def test_render_removes_unreplaced_placeholders(tmp_path: Path) -> None:
    """Template.render() strips {{...}} for variables with no value and no default."""
    template = Template(
        name="Sparse",
        content="Value: {{missing}}",
        variables=[Variable(name="missing", label="Missing", default="")],
    )
    result = template.render({})
    assert "{{missing}}" not in result
    assert "{{" not in result


# ---------------------------------------------------------------------------
# 9. Template with unknown fields loads without error
# ---------------------------------------------------------------------------


def test_load_template_with_unknown_fields(tmp_path: Path) -> None:
    """Templates with extra JSON fields (e.g., 'trigger') load without raising."""
    template_data = {
        "name": "Legacy Template",
        "content": "Some content",
        "trigger": ":legacy",
        "unknown_future_field": "some value",
        "variables": [{"name": "x", "label": "X"}],
    }
    path = tmp_path / "legacy_template.json"
    path.write_text(json.dumps(template_data), encoding="utf-8")

    mgr = TemplateManager(templates_dir=tmp_path)
    template = mgr.load(path)
    assert template is not None
    assert template.name == "Legacy Template"
    # The trigger field is preserved as a passthrough
    assert template.trigger == ":legacy"
