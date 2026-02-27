"""Tests for cross-platform packaging support.

Covers:
- ``is_frozen()`` and ``get_bundle_dir()`` path detection
- ``find_server_binary()`` prefers a bundled binary over system paths
- ``get_bundled_meta_templates_dir()`` resolves via ``get_bundle_dir()``
- ``download_llama_server`` platform key detection and idempotence
- ``build.spec`` exists and references correct entry point
- ``pyproject.toml`` has no new runtime dependencies
"""

import os
import stat
import sys
from pathlib import Path
from unittest.mock import patch

from scripts import download_llama_server as dl_mod
from templatr.core.config import LLMConfig, get_bundle_dir, is_frozen
from templatr.integrations.llm import LLMServerManager

ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_executable(path: Path) -> None:
    """Mark a file as executable."""
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def _manager_with_config(llm_cfg: LLMConfig) -> LLMServerManager:
    """Build an LLMServerManager using a specific LLMConfig."""
    mgr = LLMServerManager.__new__(LLMServerManager)
    mgr.config = llm_cfg
    mgr._process = None
    return mgr


# ---------------------------------------------------------------------------
# 1. is_frozen() detects PyInstaller environment
# ---------------------------------------------------------------------------


def test_is_frozen_returns_false_in_normal_environment() -> None:
    """is_frozen() returns False when running from source."""
    assert is_frozen() is False


def test_is_frozen_returns_true_when_meipass_set(tmp_path: Path) -> None:
    """is_frozen() returns True when sys._MEIPASS is set."""
    with patch.object(sys, "_MEIPASS", str(tmp_path), create=True):
        assert is_frozen() is True


# ---------------------------------------------------------------------------
# 2. get_bundle_dir() returns correct paths
# ---------------------------------------------------------------------------


def test_get_bundle_dir_returns_project_root_when_not_frozen() -> None:
    """get_bundle_dir() returns the project root during development."""
    bundle_dir = get_bundle_dir()
    # Should be the repo root (parent of templatr/ package)
    assert (bundle_dir / "templatr" / "__init__.py").exists()


def test_get_bundle_dir_returns_meipass_when_frozen(tmp_path: Path) -> None:
    """get_bundle_dir() returns sys._MEIPASS when running inside PyInstaller."""
    with patch.object(sys, "_MEIPASS", str(tmp_path), create=True):
        assert get_bundle_dir() == tmp_path


# ---------------------------------------------------------------------------
# 3. find_server_binary() prefers bundled binary
# ---------------------------------------------------------------------------


def test_find_server_binary_prefers_bundled_binary(tmp_path: Path) -> None:
    """find_server_binary() returns the bundled binary before system paths."""
    binary_name = "llama-server" if os.name != "nt" else "llama-server.exe"

    # Create vendor dir inside fake MEIPASS
    vendor_dir = tmp_path / "vendor" / "llama-server"
    vendor_dir.mkdir(parents=True)
    bundled = vendor_dir / binary_name
    bundled.write_text("#!/bin/sh\n")
    _make_executable(bundled)

    cfg = LLMConfig(server_binary="")
    mgr = _manager_with_config(cfg)

    with patch.object(sys, "_MEIPASS", str(tmp_path), create=True):
        with patch("templatr.integrations.llm.Path.home", return_value=tmp_path / "home"):
            with patch("templatr.integrations.llm.shutil.which", return_value=None):
                result = mgr.find_server_binary()

    assert result == bundled


def test_find_server_binary_falls_through_when_no_bundled(tmp_path: Path) -> None:
    """find_server_binary() falls through to system paths when no bundled binary exists."""
    binary_name = "llama-server" if os.name != "nt" else "llama-server.exe"

    # system binary on PATH
    system_bin = tmp_path / "system" / binary_name

    cfg = LLMConfig(server_binary="")
    mgr = _manager_with_config(cfg)

    # No _MEIPASS, no vendor dir
    with patch("templatr.integrations.llm.Path.home", return_value=tmp_path / "home"):
        with patch("templatr.integrations.llm.shutil.which", return_value=str(system_bin)):
            result = mgr.find_server_binary()

    assert result == system_bin


# ---------------------------------------------------------------------------
# 4. get_bundled_meta_templates_dir() uses get_bundle_dir()
# ---------------------------------------------------------------------------


def test_bundled_meta_templates_dir_uses_bundle_dir(tmp_path: Path) -> None:
    """get_bundled_meta_templates_dir() resolves via get_bundle_dir()."""
    from templatr.core.meta_templates import get_bundled_meta_templates_dir

    with patch.object(sys, "_MEIPASS", str(tmp_path), create=True):
        result = get_bundled_meta_templates_dir()

    assert result == tmp_path / "templates" / "_meta"


# ---------------------------------------------------------------------------
# 5. Download script platform detection
# ---------------------------------------------------------------------------


def test_detect_platform_key_returns_valid_key() -> None:
    """_detect_platform_key() returns a recognized platform key for the host."""
    key = dl_mod._detect_platform_key()
    valid_keys = {"ubuntu-x64", "macos-arm64", "macos-x64", "win-cpu-x64", "win-cpu-arm64"}
    assert key in valid_keys


def test_archive_ext_linux() -> None:
    """Linux archives use .tar.gz."""
    assert dl_mod._archive_ext("ubuntu-x64") == ".tar.gz"


def test_archive_ext_macos() -> None:
    """macOS archives use .tar.gz."""
    assert dl_mod._archive_ext("macos-arm64") == ".tar.gz"


def test_archive_ext_windows() -> None:
    """Windows archives use .zip."""
    assert dl_mod._archive_ext("win-cpu-x64") == ".zip"


# ---------------------------------------------------------------------------
# 6. Download script idempotence
# ---------------------------------------------------------------------------


def test_download_skips_when_version_matches(tmp_path: Path) -> None:
    """download_llama_server() skips download when binary and version match."""
    binary_name = "llama-server" if sys.platform != "win32" else "llama-server.exe"

    dest = tmp_path / "vendor" / "llama-server"
    dest.mkdir(parents=True)
    (dest / binary_name).write_text("fake")
    (dest / ".version").write_text("b1234")

    result = dl_mod.download_llama_server(tag="b1234", dest_dir=dest)
    assert result == dest / binary_name


# ---------------------------------------------------------------------------
# 7. build.spec exists and references correct entry point
# ---------------------------------------------------------------------------


def test_build_spec_exists() -> None:
    """build.spec file exists in the repository root."""
    assert (ROOT / "build.spec").exists()


def test_build_spec_references_main_entry() -> None:
    """build.spec references templatr/__main__.py as the entry point."""
    content = (ROOT / "build.spec").read_text()
    assert "__main__.py" in content
    assert "templatr" in content


def test_build_spec_bundles_templates() -> None:
    """build.spec includes the templates directory as data."""
    content = (ROOT / "build.spec").read_text()
    assert "templates" in content


def test_build_spec_bundles_vendor() -> None:
    """build.spec includes the vendor/llama-server directory as data."""
    content = (ROOT / "build.spec").read_text()
    assert "vendor" in content
    assert "llama-server" in content


# ---------------------------------------------------------------------------
# 8. pyproject.toml has no new runtime dependencies
# ---------------------------------------------------------------------------


def test_no_new_runtime_dependencies() -> None:
    """pyproject.toml runtime dependencies list is unchanged (PyQt6 + requests only)."""
    import tomllib

    pyproject = ROOT / "pyproject.toml"
    with open(pyproject, "rb") as f:
        data = tomllib.load(f)

    deps = data["project"]["dependencies"]
    dep_names = sorted(d.split(">")[0].split("=")[0].split("<")[0].strip() for d in deps)
    assert dep_names == ["PyQt6", "requests"]
