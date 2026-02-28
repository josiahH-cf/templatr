#!/usr/bin/env python3
"""
One-time deduplication script for templatr templates.

Rule: Templates in folders take precedence over root-level templates.
If a template exists in both root and a folder, the root version is removed.

Usage:
    python scripts/dedupe_templates.py           # Dry-run (preview changes)
    python scripts/dedupe_templates.py --apply   # Actually remove duplicates
"""

import argparse
import os
from pathlib import Path


def get_templates_dir() -> Path:
    """Get the templates directory path."""
    if os.name == "nt":  # Windows
        config_dir = Path(os.environ.get("APPDATA", "")) / "templatr"
    elif os.uname().sysname == "Darwin":  # macOS
        config_dir = Path.home() / "Library" / "Application Support" / "templatr"
    else:  # Linux/WSL
        config_dir = (
            Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
            / "templatr"
        )
    return config_dir / "templates"


def find_duplicates(templates_dir: Path) -> dict[str, list[Path]]:
    """Find templates with duplicate filenames."""
    # Build map: filename -> list of paths
    by_name: dict[str, list[Path]] = {}
    for p in templates_dir.rglob("*.json"):
        by_name.setdefault(p.name, []).append(p)

    # Filter to only duplicates
    return {name: paths for name, paths in by_name.items() if len(paths) > 1}


def deduplicate(
    templates_dir: Path, dry_run: bool = True
) -> list[tuple[str, Path, Path]]:
    """
    Remove root-level duplicates when folder version exists.

    Returns list of (filename, removed_path, kept_path) tuples.
    """
    duplicates = find_duplicates(templates_dir)
    removed = []

    for filename, paths in duplicates.items():
        # Separate root vs folder versions
        root_versions = [p for p in paths if p.parent == templates_dir]
        folder_versions = [p for p in paths if p.parent != templates_dir]

        if root_versions and folder_versions:
            # Folder version takes precedence - remove root version
            root_path = root_versions[0]
            kept_path = folder_versions[0]

            if dry_run:
                print(f"  Would remove: {root_path.relative_to(templates_dir)}")
                print(f"       Keeping: {kept_path.relative_to(templates_dir)}")
            else:
                root_path.unlink()
                print(f"  Removed: {root_path.relative_to(templates_dir)}")
                print(f"  Keeping: {kept_path.relative_to(templates_dir)}")

            removed.append((filename, root_path, kept_path))

    return removed


def main():
    parser = argparse.ArgumentParser(
        description="Remove duplicate templates (folder versions take precedence)"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually remove duplicates (default is dry-run)",
    )
    args = parser.parse_args()

    templates_dir = get_templates_dir()
    print(f"Templates directory: {templates_dir}")
    print()

    if not templates_dir.exists():
        print("ERROR: Templates directory does not exist")
        return 1

    duplicates = find_duplicates(templates_dir)

    if not duplicates:
        print("✓ No duplicate templates found")
        return 0

    print(f"Found {len(duplicates)} template(s) with duplicates:")
    print()

    if args.apply:
        print("=== Applying deduplication ===")
    else:
        print("=== Dry run (use --apply to actually remove) ===")

    print()
    removed = deduplicate(templates_dir, dry_run=not args.apply)

    print()
    if removed:
        if args.apply:
            print(f"✓ Removed {len(removed)} root-level duplicate(s)")
        else:
            print(f"Would remove {len(removed)} root-level duplicate(s)")
            print()
            print("Run with --apply to actually remove duplicates:")
            print(f"  python {__file__} --apply")
    else:
        print("✓ No root-level duplicates to remove (duplicates are all in folders)")

    return 0


if __name__ == "__main__":
    exit(main())
