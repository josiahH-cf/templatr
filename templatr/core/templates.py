"""Template management for Templatr.

Handles loading, saving, and rendering JSON templates.
Templates are stored as individual JSON files in the templates directory.
Version history is stored in _versions/ subdirectory.
"""

import json
import logging
import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from templatr.core.config import get_bundle_dir, get_config, get_templates_dir

logger = logging.getLogger(__name__)


@dataclass
class Variable:
    """A variable/placeholder in a template.

    Attributes:
        name: Variable identifier used in content placeholders.
        label: Display label for UI/forms.
        default: Default value.
        multiline: Whether to use multiline input (form type only).
        type: Variable type - "form" (default), "date", etc.
        params: Type-specific parameters (e.g., {"format": "%Y-%m-%d"} for date).
    """

    name: str
    label: str = ""
    default: str = ""
    multiline: bool = False
    type: str = "form"  # "form", "date"
    params: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.label:
            self.label = self.name.replace("_", " ").title()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        d = {"name": self.name, "label": self.label}
        if self.default:
            d["default"] = self.default
        if self.multiline:
            d["multiline"] = True
        if self.type != "form":
            d["type"] = self.type
        if self.params:
            d["params"] = self.params
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Variable":
        """Create from dictionary."""
        label = data.get("label", "")
        if label is None or isinstance(label, (dict, list)):
            label = str(label) if label not in (None, {}) else ""
        elif not isinstance(label, str):
            label = str(label)
        default = data.get("default", "")
        if default is None or isinstance(
            default, (dict, list)
        ):  # keep UI inputs from crashing
            default = str(default) if default not in (None, {}) else ""
        elif not isinstance(default, str):
            default = str(default)
        return cls(
            name=data.get("name", ""),
            label=label,
            default=default,
            multiline=data.get("multiline", False),
            type=data.get("type", "form"),
            params=data.get("params", {}),
        )


@dataclass
class Template:
    """A prompt template."""

    name: str
    content: str
    description: str = ""
    trigger: str = ""  # External trigger alias (e.g., ":review")
    variables: List[Variable] = field(default_factory=list)
    refinements: List[str] = field(
        default_factory=list
    )  # User feedback for template improvement

    # Internal: path to the JSON file (set when loaded from disk)
    _path: Optional[Path] = field(default=None, repr=False)

    @property
    def filename(self) -> str:
        """Generate a safe filename from the template name."""
        # Convert to lowercase, replace spaces with underscores
        safe = self.name.lower().replace(" ", "_")
        # Remove non-alphanumeric characters except underscores
        safe = re.sub(r"[^a-z0-9_]", "", safe)
        return f"{safe}.json"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        d = {
            "name": self.name,
            "content": self.content,
        }
        if self.description:
            d["description"] = self.description
        if self.trigger:
            d["trigger"] = self.trigger
        if self.variables:
            d["variables"] = [v.to_dict() for v in self.variables]
        if self.refinements:
            d["refinements"] = self.refinements
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any], path: Optional[Path] = None) -> "Template":
        """Create from dictionary."""
        variables = [Variable.from_dict(v) for v in data.get("variables", [])]
        return cls(
            name=data.get("name", "Untitled"),
            content=data.get("content", ""),
            description=data.get("description", ""),
            trigger=data.get("trigger", ""),
            variables=variables,
            refinements=data.get("refinements", []),
            _path=path,
        )

    def render(self, values: Dict[str, str]) -> str:
        """Render the template with the given variable values.

        Replaces {{variable_name}} placeholders with their values.

        Args:
            values: Dictionary of variable name -> value.

        Returns:
            Rendered template string.
        """
        result = self.content

        for var in self.variables:
            placeholder = f"{{{{{var.name}}}}}"
            value = values.get(var.name, var.default)
            result = result.replace(placeholder, value)

        # Remove any unreplaced placeholders
        result = re.sub(r"\{\{[^}]+\}\}", "", result)

        return result


@dataclass
class TemplateVersion:
    """A versioned snapshot of a template.

    Attributes:
        version: Version number (1 = original, higher = more recent)
        timestamp: ISO format timestamp when version was created
        note: Optional user note describing what changed
        template_data: Full template data as dict (for restoration)
    """

    version: int
    timestamp: str
    note: str
    template_data: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "version": self.version,
            "timestamp": self.timestamp,
            "note": self.note,
            "template_data": self.template_data,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TemplateVersion":
        """Create from dictionary."""
        return cls(
            version=data.get("version", 1),
            timestamp=data.get("timestamp", ""),
            note=data.get("note", ""),
            template_data=data.get("template_data", {}),
        )


def auto_detect_variables(content: str) -> List[Variable]:
    """Detect ``{{placeholder}}`` patterns in template content.

    Scans *content* for all ``{{word}}`` occurrences (regex ``\\{\\{(\\w+)\\}\\}``),
    deduplicates by name preserving first-seen order, and returns a
    :class:`Variable` for each unique match.

    Args:
        content: Raw template content string.

    Returns:
        List of Variable objects with name, auto-generated label,
        empty default, and ``multiline=False``.
    """
    seen: set[str] = set()
    variables: List[Variable] = []
    for match in re.finditer(r"\{\{(\w+)\}\}", content):
        name = match.group(1)
        if name not in seen:
            seen.add(name)
            variables.append(Variable(name=name, default="", multiline=False))
    return variables


def seed_templates(user_dir: Path) -> int:
    """Copy bundled templates into the user templates directory if it is empty.

    Only runs when the user directory contains no ``.json`` files.  Never
    overwrites existing files.  Safe to call on every startup (idempotent).

    Args:
        user_dir: Path to the user's templates directory.

    Returns:
        Number of templates copied (0 if the directory was non-empty or the
        bundle directory does not exist).
    """
    # Skip if the user already has any templates
    existing = list(user_dir.glob("*.json"))
    if existing:
        return 0

    bundle_templates = get_bundle_dir() / "templates"
    if not bundle_templates.is_dir():
        return 0

    copied = 0
    for src in bundle_templates.rglob("*.json"):
        # Skip meta-templates (_meta/) — those are internal
        rel = src.relative_to(bundle_templates)
        if rel.parts[0] == "_meta" if len(rel.parts) > 1 else False:
            continue
        dest = user_dir / rel
        if dest.exists():
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        copied += 1

    if copied:
        logger.info("Seeded %d bundled templates into %s", copied, user_dir)
    return copied


class TemplateManager:
    """Manages template CRUD operations.

    Templates are stored as individual JSON files in the templates directory.
    Version history is stored in _versions/ subdirectory.
    No SQLite, no indexing — just filesystem operations.
    """

    VERSIONS_DIR = "_versions"

    def __init__(self, templates_dir: Optional[Path] = None):
        """Initialize TemplateManager.

        Args:
            templates_dir: Directory for template files. Uses default if None.
        """
        self.templates_dir = templates_dir or get_templates_dir()
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        # Seed bundled templates on first run
        seed_templates(self.templates_dir)
        # Create versions directory
        self._versions_dir = self.templates_dir / self.VERSIONS_DIR
        self._versions_dir.mkdir(parents=True, exist_ok=True)

    def _get_version_dir(self, template: Template) -> Path:
        """Get the version history directory for a template.

        Args:
            template: Template to get version dir for.

        Returns:
            Path to the template's version directory.
        """
        # Use template filename (without .json) as version subdirectory
        slug = template.filename.replace(".json", "")
        version_dir = self._versions_dir / slug
        version_dir.mkdir(parents=True, exist_ok=True)
        return version_dir

    def _get_max_versions(self) -> int:
        """Get the maximum number of versions to keep per template."""
        config = get_config()
        return config.ui.max_template_versions

    def create_version(
        self, template: Template, note: str = ""
    ) -> Optional[TemplateVersion]:
        """Create a new version snapshot of a template.

        Args:
            template: Template to create version for.
            note: Optional note describing what changed.

        Returns:
            The created TemplateVersion, or None if failed.
        """
        version_dir = self._get_version_dir(template)

        # Find the next version number
        existing_versions = self.list_versions(template)
        next_version = 1 if not existing_versions else existing_versions[-1].version + 1

        # Create version snapshot
        version = TemplateVersion(
            version=next_version,
            timestamp=datetime.now().isoformat(),
            note=note,
            template_data=template.to_dict(),
        )

        # Save version file
        version_path = version_dir / f"v{next_version}.json"
        try:
            with open(version_path, "w", encoding="utf-8") as f:
                json.dump(version.to_dict(), f, indent=2)
        except OSError as e:
            print(f"Error saving version: {e}")
            return None

        # Prune old versions (keep original v1 + most recent N-1)
        self._prune_versions(template)

        return version

    def list_versions(self, template: Template) -> List[TemplateVersion]:
        """List all versions for a template.

        Args:
            template: Template to list versions for.

        Returns:
            List of TemplateVersion objects, sorted by version number (ascending).
        """
        version_dir = self._get_version_dir(template)
        versions = []

        for path in version_dir.glob("v*.json"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                versions.append(TemplateVersion.from_dict(data))
            except (json.JSONDecodeError, OSError) as e:
                print(f"Warning: Failed to load version {path}: {e}")

        return sorted(versions, key=lambda v: v.version)

    def get_version(
        self, template: Template, version_num: int
    ) -> Optional[TemplateVersion]:
        """Get a specific version of a template.

        Args:
            template: Template to get version for.
            version_num: Version number to retrieve.

        Returns:
            TemplateVersion, or None if not found.
        """
        version_dir = self._get_version_dir(template)
        version_path = version_dir / f"v{version_num}.json"

        if not version_path.exists():
            return None

        try:
            with open(version_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return TemplateVersion.from_dict(data)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Error loading version {version_num}: {e}")
            return None

    def restore_version(
        self, template: Template, version_num: int, create_backup: bool = True
    ) -> Optional[Template]:
        """Restore a template to a previous version.

        Args:
            template: Template to restore.
            version_num: Version number to restore to.
            create_backup: If True, create a version snapshot before restoring.

        Returns:
            The restored Template, or None if failed.
        """
        version = self.get_version(template, version_num)
        if not version:
            return None

        # Create backup of current state before restoring
        if create_backup:
            self.create_version(
                template, note=f"Backup before revert to v{version_num}"
            )

        # Restore template data
        restored = Template.from_dict(version.template_data, path=template._path)

        # Save restored template
        if self.save(restored):
            return restored
        return None

    def _prune_versions(self, template: Template) -> None:
        """Prune old versions to stay within the limit.

        Always keeps v1 (original) and the most recent versions up to the limit.

        Args:
            template: Template to prune versions for.
        """
        max_versions = self._get_max_versions()
        versions = self.list_versions(template)

        if len(versions) <= max_versions:
            return

        # Keep v1 (original) and the most recent (max_versions - 1)
        to_keep = set()

        # Always keep original (v1) if it exists
        if versions and versions[0].version == 1:
            to_keep.add(1)

        # Keep the most recent versions
        recent_count = max_versions - len(to_keep)
        for v in versions[-recent_count:]:
            to_keep.add(v.version)

        # Delete versions not in to_keep
        version_dir = self._get_version_dir(template)
        for v in versions:
            if v.version not in to_keep:
                version_path = version_dir / f"v{v.version}.json"
                try:
                    version_path.unlink()
                except OSError:
                    pass

    def delete_version_history(self, template: Template) -> bool:
        """Delete all version history for a template.

        Args:
            template: Template to delete history for.

        Returns:
            True if deleted successfully, False otherwise.
        """
        version_dir = self._get_version_dir(template)
        try:
            import shutil

            if version_dir.exists():
                shutil.rmtree(version_dir)
            return True
        except OSError as e:
            print(f"Error deleting version history: {e}")
            return False

    def list_all(self) -> List[Template]:
        """List all templates.

        Returns:
            List of Template objects, sorted by name.
        """
        templates = []
        for path in self.templates_dir.glob("**/*.json"):
            # Skip version files
            if self.VERSIONS_DIR in path.parts:
                continue
            # Skip meta-templates (system templates)
            if "_meta" in path.parts:
                continue
            try:
                template = self.load(path)
                if template:
                    templates.append(template)
            except Exception as e:
                print(f"Warning: Failed to load {path}: {e}")

        return sorted(templates, key=lambda t: t.name.lower())

    def search_templates(self, query: str) -> List[Template]:
        """Search templates by name, trigger, or description.

        Returns templates ranked by relevance:
        1. Exact name prefix match (case-insensitive)
        2. Name substring match
        3. Trigger match (without ':' prefix)
        4. Description substring match

        An empty query returns all templates sorted by name (same as list_all).

        Args:
            query: Search string to match against templates.

        Returns:
            List of matching Template objects, ordered by relevance.
        """
        all_templates = self.list_all()
        if not query:
            return all_templates

        query_lower = query.lower()
        # Strip leading ':' from query for trigger matching
        trigger_query = query_lower.lstrip(":")

        prefix_matches: List[Template] = []
        name_substring: List[Template] = []
        trigger_matches: List[Template] = []
        desc_matches: List[Template] = []
        seen: set = set()

        for t in all_templates:
            name_lower = t.name.lower()
            trig_lower = t.trigger.lower().lstrip(":") if t.trigger else ""
            desc_lower = t.description.lower() if t.description else ""

            if name_lower.startswith(query_lower):
                prefix_matches.append(t)
                seen.add(id(t))
            elif query_lower in name_lower:
                name_substring.append(t)
                seen.add(id(t))

        for t in all_templates:
            if id(t) in seen:
                continue
            trig_lower = t.trigger.lower().lstrip(":") if t.trigger else ""
            if trig_lower and trigger_query in trig_lower:
                trigger_matches.append(t)
                seen.add(id(t))

        for t in all_templates:
            if id(t) in seen:
                continue
            desc_lower = t.description.lower() if t.description else ""
            if query_lower in desc_lower:
                desc_matches.append(t)
                seen.add(id(t))

        return prefix_matches + name_substring + trigger_matches + desc_matches

    def load(self, path: Path) -> Optional[Template]:
        """Load a template from a JSON file.

        Args:
            path: Path to the JSON file.

        Returns:
            Template object, or None if loading failed.
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return Template.from_dict(data, path=path)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Error loading template {path}: {e}")
            return None

    def get(self, name: str) -> Optional[Template]:
        """Get a template by name.

        Args:
            name: Template name.

        Returns:
            Template object, or None if not found.
        """
        # Create expected filename
        safe_name = name.lower().replace(" ", "_")
        safe_name = re.sub(r"[^a-z0-9_]", "", safe_name)
        path = self.templates_dir / f"{safe_name}.json"

        if path.exists():
            return self.load(path)

        # Fallback: search all templates
        for template in self.list_all():
            if template.name.lower() == name.lower():
                return template

        return None

    def save(self, template: Template) -> bool:
        """Save a template to disk.

        Args:
            template: Template to save.

        Returns:
            True if saved successfully, False otherwise.
        """
        # Determine path
        if template._path:
            path = template._path
        else:
            path = self.templates_dir / template.filename

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(template.to_dict(), f, indent=2)
            template._path = path
            return True
        except OSError as e:
            print(f"Error saving template: {e}")
            return False

    def delete(self, template: Template) -> bool:
        """Delete a template from disk.

        Args:
            template: Template to delete.

        Returns:
            True if deleted successfully, False otherwise.
        """
        if not template._path or not template._path.exists():
            return False

        try:
            template._path.unlink()
            return True
        except OSError as e:
            print(f"Error deleting template: {e}")
            return False

    def create(
        self,
        name: str,
        content: str,
        description: str = "",
        trigger: str = "",
        variables: Optional[List[Dict[str, Any]]] = None,
    ) -> Template:
        """Create and save a new template.

        Args:
            name: Template name.
            content: Template content with {{variable}} placeholders.
            description: Optional description.
            trigger: Optional external trigger alias.
            variables: Optional list of variable dicts.

        Returns:
            The created Template object.
        """
        var_list = []
        if variables:
            var_list = [Variable.from_dict(v) for v in variables]

        template = Template(
            name=name,
            content=content,
            description=description,
            trigger=trigger,
            variables=var_list,
        )

        self.save(template)
        return template

    def export_template(self, template: Template, path: Path) -> Path:
        """Export a template to a standalone JSON file.

        Writes the template data without the internal ``_path`` field so the
        file is portable across installations.

        Args:
            template: Template to export.
            path: Destination file path.

        Returns:
            The path written to.

        Raises:
            OSError: If the file cannot be written.
        """
        data = template.to_dict()
        data.pop("_path", None)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return path

    def import_template(self, path: Path) -> tuple:
        """Import a template from a JSON file without saving.

        Reads and validates the file, checks for name conflicts, and returns
        the parsed template along with a conflict flag.  The caller is
        responsible for resolving conflicts and calling :meth:`save`.

        Args:
            path: Path to the JSON file to import.

        Returns:
            A ``(template, conflict_exists)`` tuple.

        Raises:
            ValueError: If the file is not valid JSON or is missing required
                fields (``name`` and ``content``).
        """
        try:
            raw = path.read_text(encoding="utf-8")
            data = json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ValueError(f"Invalid JSON in {path.name}: {exc}") from exc

        if not isinstance(data, dict):
            raise ValueError(f"Invalid JSON structure in {path.name}: expected object")

        if "name" not in data or not data["name"]:
            raise ValueError(f"Missing required field 'name' in {path.name}")
        if "content" not in data or not data["content"]:
            raise ValueError(f"Missing required field 'content' in {path.name}")

        template = Template.from_dict(data)
        conflict = self.get(template.name) is not None
        return template, conflict

    def list_folders(self) -> List[str]:
        """List all category folders.

        Returns:
            List of folder names (relative to templates_dir), sorted alphabetically.
            Excludes the _versions directory used for version history.
        """
        folders = []
        for path in self.templates_dir.iterdir():
            if path.is_dir() and path.name != self.VERSIONS_DIR:
                folders.append(path.name)
        return sorted(folders, key=str.lower)

    def create_folder(self, name: str) -> bool:
        """Create a new category folder.

        Args:
            name: Folder name.

        Returns:
            True if created successfully, False otherwise.
        """
        # Sanitize folder name
        safe_name = re.sub(r"[^a-zA-Z0-9_ -]", "", name).strip()
        if not safe_name:
            return False

        folder_path = self.templates_dir / safe_name
        if folder_path.exists():
            return False

        try:
            folder_path.mkdir(parents=True, exist_ok=True)
            return True
        except OSError:
            return False

    def delete_folder(self, name: str) -> tuple[bool, str]:
        """Delete a category folder (must be empty).

        Args:
            name: Folder name.

        Returns:
            Tuple of (success, error_message).
        """
        folder_path = self.templates_dir / name
        if not folder_path.exists() or not folder_path.is_dir():
            return False, "Folder does not exist."

        # Check if folder has templates
        templates_in_folder = list(folder_path.glob("*.json"))
        if templates_in_folder:
            return (
                False,
                f"Cannot delete folder '{name}' because it contains {len(templates_in_folder)} template(s). Move or delete them first.",
            )

        try:
            folder_path.rmdir()
            return True, ""
        except OSError as e:
            return False, str(e)

    def get_template_folder(self, template: Template) -> str:
        """Get the folder name for a template.

        Args:
            template: Template to check.

        Returns:
            Folder name, or empty string if in root.
        """
        if not template._path:
            return ""

        parent = template._path.parent
        if parent == self.templates_dir:
            return ""
        return parent.name

    def save_to_folder(self, template: Template, folder: str = "") -> bool:
        """Save a template to a specific folder.

        Args:
            template: Template to save.
            folder: Folder name (empty string for root).

        Returns:
            True if saved successfully, False otherwise.
        """
        # Determine target directory
        if folder:
            target_dir = self.templates_dir / folder
            target_dir.mkdir(parents=True, exist_ok=True)
        else:
            target_dir = self.templates_dir

        # If template already has a path in a different location, we're moving it
        old_path = template._path
        new_path = target_dir / template.filename

        try:
            with open(new_path, "w", encoding="utf-8") as f:
                json.dump(template.to_dict(), f, indent=2)

            # Remove old file if we moved it
            if old_path and old_path != new_path and old_path.exists():
                old_path.unlink()

            template._path = new_path
            return True
        except OSError as e:
            print(f"Error saving template: {e}")
            return False


# Global template manager instance
_template_manager: Optional[TemplateManager] = None


def get_template_manager() -> TemplateManager:
    """Get the global TemplateManager instance."""
    global _template_manager
    if _template_manager is None:
        _template_manager = TemplateManager()
    return _template_manager


def reset() -> None:
    """Clear the cached TemplateManager instance.

    For testing only — allows tests to start with a fresh instance.
    """
    global _template_manager
    _template_manager = None
