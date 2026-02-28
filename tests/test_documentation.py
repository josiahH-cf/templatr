"""Tests for scripts/check_docs.py documentation freshness checks."""

import sys
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture()
def repo_root():
    """Return the repository root path."""
    return Path(__file__).resolve().parent.parent


class TestCheckDocs:
    """Tests for the doc-freshness CI script."""

    def test_script_passes_on_current_repo(self, repo_root):
        """The check_docs script exits 0 on the actual repo."""
        import subprocess

        result = subprocess.run(
            [sys.executable, str(repo_root / "scripts" / "check_docs.py")],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
        )
        assert result.returncode == 0, f"check_docs.py failed:\n{result.stdout}\n{result.stderr}"

    def test_script_completes_under_10_seconds(self, repo_root):
        """The check_docs script completes in under 10 seconds."""
        import subprocess
        import time

        start = time.monotonic()
        subprocess.run(
            [sys.executable, str(repo_root / "scripts" / "check_docs.py")],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
        )
        elapsed = time.monotonic() - start
        assert elapsed < 10, f"check_docs.py took {elapsed:.1f}s (limit: 10s)"

    def test_detects_stale_name_in_readme(self, tmp_path):
        """Script detects stale package names in README code blocks."""
        # Create a minimal repo structure with stale name
        (tmp_path / "pyproject.toml").write_text(
            textwrap.dedent("""\
                [project]
                name = "templatr"
            """)
        )
        (tmp_path / "README.md").write_text(
            textwrap.dedent("""\
                # Test
                ```bash
                pip install automatr
                ```
            """)
        )
        (tmp_path / "CONTRIBUTING.md").write_text("# Contributing\n")
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "troubleshooting-linux.md").write_text("")
        (tmp_path / "docs" / "troubleshooting-macos.md").write_text("")
        (tmp_path / "docs" / "troubleshooting-windows.md").write_text("")
        images = tmp_path / "docs" / "images"
        images.mkdir()
        for name in [
            "main-chat-view.png",
            "slash-command-palette.png",
            "template-editor.png",
            "new-template-flow.png",
        ]:
            (images / name).write_bytes(b"\x89PNG")

        # Import and run with patched REPO_ROOT
        import importlib
        import sys

        spec = importlib.util.spec_from_file_location(
            "check_docs",
            str(Path(__file__).resolve().parent.parent / "scripts" / "check_docs.py"),
        )
        mod = importlib.util.module_from_spec(spec)

        # Patch REPO_ROOT before executing
        with patch.object(mod, "__name__", "check_docs"):
            spec.loader.exec_module(mod)
            mod.REPO_ROOT = tmp_path
            mod.errors = []  # Reset errors
            result = mod.main()

        assert result == 1, "Should fail when stale name 'automatr' is in README"

    def test_passes_with_correct_name(self, tmp_path):
        """Script passes when README uses the correct project name."""
        (tmp_path / "pyproject.toml").write_text(
            textwrap.dedent("""\
                [project]
                name = "templatr"
            """)
        )
        (tmp_path / "README.md").write_text(
            textwrap.dedent("""\
                # Templatr
                ```bash
                pip install templatr
                ```
            """)
        )
        (tmp_path / "CONTRIBUTING.md").write_text("# Contributing\n")
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "troubleshooting-linux.md").write_text("")
        (tmp_path / "docs" / "troubleshooting-macos.md").write_text("")
        (tmp_path / "docs" / "troubleshooting-windows.md").write_text("")
        images = tmp_path / "docs" / "images"
        images.mkdir()
        for name in [
            "main-chat-view.png",
            "slash-command-palette.png",
            "template-editor.png",
            "new-template-flow.png",
        ]:
            (images / name).write_bytes(b"\x89PNG")

        import importlib

        spec = importlib.util.spec_from_file_location(
            "check_docs",
            str(Path(__file__).resolve().parent.parent / "scripts" / "check_docs.py"),
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.REPO_ROOT = tmp_path
        mod.errors = []
        result = mod.main()

        assert result == 0, "Should pass when correct name is used"

    def test_detects_missing_required_files(self, tmp_path):
        """Script fails when required doc files are missing."""
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "templatr"\n')
        (tmp_path / "README.md").write_text("# Templatr\n")
        # Deliberately omit CONTRIBUTING.md and docs/

        import importlib

        spec = importlib.util.spec_from_file_location(
            "check_docs",
            str(Path(__file__).resolve().parent.parent / "scripts" / "check_docs.py"),
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.REPO_ROOT = tmp_path
        mod.errors = []
        result = mod.main()

        assert result == 1, "Should fail when required files are missing"


class TestReadmeContent:
    """Verify README.md meets acceptance criteria."""

    def test_readme_has_per_os_quick_start(self, repo_root):
        """README has Quick Start sections for Linux, macOS, and Windows."""
        text = (repo_root / "README.md").read_text()
        assert "### Linux" in text
        assert "### macOS" in text
        assert "### Windows" in text

    def test_readme_windows_references_releases(self, repo_root):
        """Windows Quick Start references Releases download, not install.sh."""
        text = (repo_root / "README.md").read_text()
        lines = text.split("\n")
        # Find the Windows section heading
        win_start = None
        win_end = None
        for i, line in enumerate(lines):
            if line.strip() == "### Windows" and win_start is None:
                win_start = i
            elif win_start is not None and line.startswith("## "):
                win_end = i
                break
        if win_end is None:
            win_end = len(lines)
        windows_section = "\n".join(lines[win_start:win_end])

        assert "Releases" in windows_section or "releases" in windows_section
        assert "install.sh" not in windows_section or "WSL2" in windows_section

    def test_readme_has_badges(self, repo_root):
        """README contains CI, release, and platform badges."""
        text = (repo_root / "README.md").read_text()
        assert "badge.svg" in text or "img.shields.io" in text
        assert "ci.yml" in text
        assert "release" in text.lower()

    def test_readme_documents_macos_path(self, repo_root):
        """README documents macOS path as ~/Library/Application Support/templatr/."""
        text = (repo_root / "README.md").read_text()
        assert "~/Library/Application Support/templatr/" in text

    def test_readme_documents_xdg_paths(self, repo_root):
        """README documents XDG config paths for Linux."""
        text = (repo_root / "README.md").read_text()
        assert "XDG_CONFIG_HOME" in text


class TestContributingContent:
    """Verify CONTRIBUTING.md meets acceptance criteria."""

    def test_contributing_exists(self, repo_root):
        """CONTRIBUTING.md exists."""
        assert (repo_root / "CONTRIBUTING.md").exists()

    def test_contributing_has_pip_install(self, repo_root):
        """CONTRIBUTING.md documents pip install -e .[dev]."""
        text = (repo_root / "CONTRIBUTING.md").read_text()
        assert "pip install -e .[dev]" in text

    def test_contributing_has_empty_state_warning(self, repo_root):
        """CONTRIBUTING.md documents the empty-state issue after pip install."""
        text = (repo_root / "CONTRIBUTING.md").read_text()
        assert "does not seed templates" in text.lower() or "known issue" in text.lower()

    def test_contributing_references_templates_md(self, repo_root):
        """CONTRIBUTING.md references TEMPLATES.md."""
        text = (repo_root / "CONTRIBUTING.md").read_text()
        assert "TEMPLATES.md" in text


class TestTroubleshootingContent:
    """Verify troubleshooting docs meet acceptance criteria."""

    def test_troubleshooting_files_exist(self, repo_root):
        """Per-OS troubleshooting files exist in docs/."""
        for name in [
            "troubleshooting-linux.md",
            "troubleshooting-macos.md",
            "troubleshooting-windows.md",
        ]:
            assert (repo_root / "docs" / name).exists(), f"Missing docs/{name}"

    def test_windows_troubleshooting_addresses_powershell(self, repo_root):
        """Windows troubleshooting addresses the phantom PowerShell installer."""
        text = (repo_root / "docs" / "troubleshooting-windows.md").read_text()
        assert "powershell" in text.lower()
        assert "does not exist" in text.lower()

    def test_macos_troubleshooting_addresses_wrong_path(self, repo_root):
        """macOS troubleshooting notes that ~/.config/templatr is incorrect."""
        text = (repo_root / "docs" / "troubleshooting-macos.md").read_text()
        assert "~/.config/templatr" in text
        assert "~/Library/Application Support/templatr/" in text


class TestScreenshots:
    """Verify screenshot files exist."""

    def test_screenshot_files_exist(self, repo_root):
        """docs/images/ contains required screenshot files."""
        images_dir = repo_root / "docs" / "images"
        expected = [
            "main-chat-view.png",
            "slash-command-palette.png",
            "template-editor.png",
            "new-template-flow.png",
        ]
        for name in expected:
            assert (images_dir / name).exists(), f"Missing docs/images/{name}"

    def test_screenshots_are_non_empty(self, repo_root):
        """Screenshot files have content (not empty placeholders)."""
        images_dir = repo_root / "docs" / "images"
        for png in images_dir.glob("*.png"):
            assert png.stat().st_size > 100, f"{png.name} appears to be an empty placeholder"
