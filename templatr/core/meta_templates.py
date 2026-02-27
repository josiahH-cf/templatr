"""Meta-template loading and management.

Meta-templates are system templates used by features like "Improve
Template" and "Generate Template". This module is extracted from
templates.py to break the circular import between feedback.py and
templates.py.
"""

import json
from pathlib import Path
from typing import Optional

from templatr.core.config import get_templates_dir
from templatr.core.templates import Template


def get_meta_templates_dir() -> Path:
    """Get the path to the _meta templates directory.

    First checks the user's templates directory, then falls back to
    the bundled templates in the package.

    Returns:
        Path to _meta directory.
    """
    user_meta = get_templates_dir() / "_meta"
    if user_meta.exists():
        return user_meta

    bundled_meta = Path(__file__).parent.parent.parent / "templates" / "_meta"
    return bundled_meta


def get_bundled_meta_templates_dir() -> Path:
    """Get the path to the bundled _meta templates directory.

    Returns:
        Path to bundled _meta directory.
    """
    return Path(__file__).parent.parent.parent / "templates" / "_meta"


def get_user_meta_templates_dir() -> Path:
    """Get the path to the user's _meta templates directory.

    Creates the directory if it doesn't exist.

    Returns:
        Path to user's _meta directory.
    """
    user_meta = get_templates_dir() / "_meta"
    user_meta.mkdir(parents=True, exist_ok=True)
    return user_meta


def load_meta_template(name: str) -> Optional[Template]:
    """Load a meta-template by name from the _meta directory.

    Meta-templates are system templates used by features like
    "Improve Template" and "Generate Template".

    Checks user's _meta directory first, then falls back to bundled.

    Args:
        name: Template name (without .json extension), e.g., "template_improver"

    Returns:
        Template object, or None if not found.
    """
    user_path = get_templates_dir() / "_meta" / f"{name}.json"
    if user_path.exists():
        try:
            with open(user_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return Template.from_dict(data, path=user_path)
        except (json.JSONDecodeError, OSError):
            pass

    bundled_path = get_bundled_meta_templates_dir() / f"{name}.json"
    if bundled_path.exists():
        try:
            with open(bundled_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return Template.from_dict(data, path=bundled_path)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Error loading meta-template {name}: {e}")

    return None


def save_meta_template(name: str, content: str) -> bool:
    """Save a meta-template's content to the user's _meta directory.

    Preserves the template's metadata (name, description, variables) and
    only updates the content field.

    Args:
        name: Template name (without .json extension)
        content: New content for the template

    Returns:
        True if saved successfully, False otherwise.
    """
    template = load_meta_template(name)
    if not template:
        return False

    template.content = content

    user_path = get_user_meta_templates_dir() / f"{name}.json"
    try:
        with open(user_path, "w", encoding="utf-8") as f:
            json.dump(template.to_dict(), f, indent=2)
        return True
    except OSError as e:
        print(f"Error saving meta-template {name}: {e}")
        return False


def reset_meta_template(name: str) -> bool:
    """Reset a meta-template to its bundled default.

    Deletes the user's copy so the bundled version is used.

    Args:
        name: Template name (without .json extension)

    Returns:
        True if reset successfully, False otherwise.
    """
    user_path = get_templates_dir() / "_meta" / f"{name}.json"
    if user_path.exists():
        try:
            user_path.unlink()
            return True
        except OSError as e:
            print(f"Error resetting meta-template {name}: {e}")
            return False
    return True


def get_bundled_meta_template_content(name: str) -> Optional[str]:
    """Get the content of a bundled meta-template.

    Used by the "Reset to Default" functionality.

    Args:
        name: Template name (without .json extension)

    Returns:
        Template content string, or None if not found.
    """
    bundled_path = get_bundled_meta_templates_dir() / f"{name}.json"
    if bundled_path.exists():
        try:
            with open(bundled_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("content", "")
        except (json.JSONDecodeError, OSError):
            pass
    return None
