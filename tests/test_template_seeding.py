"""Tests for first-run template seeding.

Covers:
- Templates are copied from bundle to empty user templates dir
- Non-empty user templates dir is not modified
- Seeding is idempotent — safe to run on every launch
- Existing user templates are never overwritten
"""

import json
from pathlib import Path
from unittest.mock import patch

from templatr.core.templates import TemplateManager, seed_templates

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_bundle_template(bundle_dir: Path, name: str, content: dict) -> Path:
    """Create a template JSON file in a fake bundle directory."""
    templates_dir = bundle_dir / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)
    path = templates_dir / f"{name}.json"
    path.write_text(json.dumps(content), encoding="utf-8")
    return path


def _create_user_template(user_dir: Path, name: str, content: dict) -> Path:
    """Create a template JSON file in a user templates directory."""
    user_dir.mkdir(parents=True, exist_ok=True)
    path = user_dir / f"{name}.json"
    path.write_text(json.dumps(content), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# 1. Seeding copies templates into empty user dir
# ---------------------------------------------------------------------------


def test_seed_copies_templates_to_empty_dir(tmp_path: Path) -> None:
    """seed_templates() copies bundled templates into an empty user dir."""
    bundle_dir = tmp_path / "bundle"
    user_dir = tmp_path / "user_templates"
    user_dir.mkdir(parents=True)

    _create_bundle_template(
        bundle_dir, "hello", {"name": "Hello", "template": "Hi {{name}}"}
    )
    _create_bundle_template(
        bundle_dir, "bye", {"name": "Bye", "template": "Goodbye {{name}}"}
    )

    with patch("templatr.core.templates.get_bundle_dir", return_value=bundle_dir):
        count = seed_templates(user_dir)

    assert count == 2
    assert (user_dir / "hello.json").exists()
    assert (user_dir / "bye.json").exists()


# ---------------------------------------------------------------------------
# 2. Non-empty user dir is not modified
# ---------------------------------------------------------------------------


def test_seed_skips_nonempty_dir(tmp_path: Path) -> None:
    """seed_templates() does nothing when user dir already has .json files."""
    bundle_dir = tmp_path / "bundle"
    user_dir = tmp_path / "user_templates"

    _create_bundle_template(
        bundle_dir, "hello", {"name": "Hello", "template": "Hi {{name}}"}
    )
    _create_user_template(
        user_dir, "existing", {"name": "Mine", "template": "My template"}
    )

    with patch("templatr.core.templates.get_bundle_dir", return_value=bundle_dir):
        count = seed_templates(user_dir)

    assert count == 0
    # Only the user's file, not the bundled one
    json_files = list(user_dir.glob("*.json"))
    assert len(json_files) == 1
    assert json_files[0].name == "existing.json"


# ---------------------------------------------------------------------------
# 3. Seeding is idempotent
# ---------------------------------------------------------------------------


def test_seed_idempotent_when_already_seeded(tmp_path: Path) -> None:
    """Calling seed_templates() twice does not duplicate templates."""
    bundle_dir = tmp_path / "bundle"
    user_dir = tmp_path / "user_templates"
    user_dir.mkdir(parents=True)

    _create_bundle_template(
        bundle_dir, "hello", {"name": "Hello", "template": "Hi {{name}}"}
    )

    with patch("templatr.core.templates.get_bundle_dir", return_value=bundle_dir):
        first_count = seed_templates(user_dir)
        second_count = seed_templates(user_dir)

    assert first_count == 1
    assert second_count == 0  # Already populated — skip


# ---------------------------------------------------------------------------
# 4. Seeding never overwrites existing files
# ---------------------------------------------------------------------------


def test_seed_never_overwrites_existing_file(tmp_path: Path) -> None:
    """seed_templates() never overwrites files that already exist."""
    bundle_dir = tmp_path / "bundle"
    user_dir = tmp_path / "user_templates"
    user_dir.mkdir(parents=True)

    _create_bundle_template(
        bundle_dir, "conflict", {"name": "Bundle", "template": "Bundle version"}
    )
    _create_user_template(
        user_dir, "conflict", {"name": "User", "template": "User version"}
    )

    with patch("templatr.core.templates.get_bundle_dir", return_value=bundle_dir):
        count = seed_templates(user_dir)

    assert count == 0
    content = json.loads((user_dir / "conflict.json").read_text())
    assert content["name"] == "User"  # User content preserved


# ---------------------------------------------------------------------------
# 5. Missing bundle dir is handled gracefully
# ---------------------------------------------------------------------------


def test_seed_handles_missing_bundle_dir(tmp_path: Path) -> None:
    """seed_templates() returns 0 when the bundle templates dir doesn't exist."""
    bundle_dir = tmp_path / "nonexistent_bundle"
    user_dir = tmp_path / "user_templates"
    user_dir.mkdir(parents=True)

    with patch("templatr.core.templates.get_bundle_dir", return_value=bundle_dir):
        count = seed_templates(user_dir)

    assert count == 0


# ---------------------------------------------------------------------------
# 6. TemplateManager calls seed_templates on init
# ---------------------------------------------------------------------------


def test_template_manager_seeds_on_init(tmp_path: Path) -> None:
    """TemplateManager seeds templates on first init when dir is empty."""
    bundle_dir = tmp_path / "bundle"
    user_dir = tmp_path / "user_templates"

    _create_bundle_template(
        bundle_dir, "hello", {"name": "Hello", "template": "Hi {{name}}"}
    )

    with patch("templatr.core.templates.get_bundle_dir", return_value=bundle_dir):
        TemplateManager(templates_dir=user_dir)

    # The _versions dir doesn't count — check for actual template files
    json_files = [f for f in user_dir.glob("*.json")]
    assert len(json_files) == 1
    assert json_files[0].name == "hello.json"
