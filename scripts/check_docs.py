#!/usr/bin/env python3
"""Check documentation freshness.

Verifies that:
1. Binary/package names in README fenced code blocks match pyproject.toml
2. File paths referenced in docs actually exist
3. Required documentation files exist

Exits non-zero if any check fails. Designed to run in CI in under 10 seconds.
"""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

errors: list[str] = []


def error(msg: str) -> None:
    """Record an error message."""
    errors.append(msg)
    print(f"  FAIL: {msg}")


def ok(msg: str) -> None:
    """Print a passing check."""
    print(f"  OK:   {msg}")


def get_project_name() -> str:
    """Extract the project name from pyproject.toml."""
    pyproject = REPO_ROOT / "pyproject.toml"
    text = pyproject.read_text()
    match = re.search(r'^name\s*=\s*"(.+?)"', text, re.MULTILINE)
    if not match:
        error("Could not find project name in pyproject.toml")
        return ""
    return match.group(1)


# --------------------------------------------------------------------------
# Check 1: Package name consistency
# --------------------------------------------------------------------------


def check_package_name_in_readme(project_name: str) -> None:
    """Verify README code blocks don't reference a stale package name."""
    readme = REPO_ROOT / "README.md"
    text = readme.read_text()

    # Extract all fenced code blocks
    code_blocks = re.findall(r"```[^\n]*\n(.*?)```", text, re.DOTALL)

    # Known old names that should not appear
    stale_names = {"automatr", "promptlocal"}

    for i, block in enumerate(code_blocks, 1):
        for stale in stale_names:
            if stale in block.lower():
                error(
                    f"README code block #{i} references stale name '{stale}' "
                    f"(project is now '{project_name}')"
                )

    # Verify the current project name appears somewhere in the README
    if project_name and project_name.lower() not in text.lower():
        error(f"README does not mention the project name '{project_name}'")
    else:
        ok(f"README references current project name '{project_name}'")


# --------------------------------------------------------------------------
# Check 2: Referenced files exist
# --------------------------------------------------------------------------


def check_referenced_files_exist() -> None:
    """Verify that files referenced in markdown docs actually exist."""
    doc_files = [
        REPO_ROOT / "README.md",
        REPO_ROOT / "CONTRIBUTING.md",
    ]

    # Patterns to match: [text](relative/path) but not URLs
    link_pattern = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")

    for doc_file in doc_files:
        if not doc_file.exists():
            continue

        text = doc_file.read_text()
        for _label, target in link_pattern.findall(text):
            # Skip URLs, anchors, badges
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            # Skip image badge URLs
            if "img.shields.io" in target or "badge" in target.lower():
                continue

            # Resolve relative to the doc file's directory
            resolved = (doc_file.parent / target).resolve()
            if not resolved.exists():
                error(f"{doc_file.name} links to '{target}' which does not exist")


# --------------------------------------------------------------------------
# Check 3: Required documentation files exist
# --------------------------------------------------------------------------


def check_required_files_exist() -> None:
    """Verify that required documentation files are present."""
    required = [
        "README.md",
        "CONTRIBUTING.md",
        "docs/troubleshooting-linux.md",
        "docs/troubleshooting-macos.md",
        "docs/troubleshooting-windows.md",
        "docs/images/main-chat-view.png",
        "docs/images/slash-command-palette.png",
        "docs/images/template-editor.png",
        "docs/images/new-template-flow.png",
    ]

    for rel_path in required:
        full_path = REPO_ROOT / rel_path
        if full_path.exists():
            ok(f"{rel_path} exists")
        else:
            error(f"Required file missing: {rel_path}")


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------


def main() -> int:
    """Run all documentation freshness checks."""
    print("=== Documentation Freshness Check ===\n")

    project_name = get_project_name()

    print("1. Package name consistency:")
    check_package_name_in_readme(project_name)

    print("\n2. Referenced files exist:")
    check_referenced_files_exist()

    print("\n3. Required documentation files:")
    check_required_files_exist()

    print()
    if errors:
        print(f"FAILED: {len(errors)} issue(s) found")
        return 1
    else:
        print("PASSED: All documentation checks passed")
        return 0


if __name__ == "__main__":
    sys.exit(main())
