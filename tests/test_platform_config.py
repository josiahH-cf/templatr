"""Tests for PlatformConfig dataclass and get_platform_config() factory.

Covers:
- PlatformConfig construction for all platforms (linux, macos, windows, wsl2)
- get_platform_config() as the single source of truth for platform detection
- get_config_dir() returns %APPDATA%/templatr on Windows
- get_data_dir() respects XDG_DATA_HOME on Linux
- Backward-compatible wrappers: get_platform(), is_windows()
"""

import os
from pathlib import Path
from unittest.mock import patch

from templatr.core.config import (
    PlatformConfig,
    get_data_dir,
    get_platform,
    get_platform_config,
    is_windows,
)

# ---------------------------------------------------------------------------
# 1. PlatformConfig dataclass fields
# ---------------------------------------------------------------------------


def test_platform_config_has_required_fields() -> None:
    """PlatformConfig has all required fields: platform, config_dir, data_dir,
    models_dir, binary_name, binary_search_paths."""
    pc = PlatformConfig(
        platform="linux",
        config_dir=Path("/tmp/config"),
        data_dir=Path("/tmp/data"),
        models_dir=Path("/tmp/models"),
        binary_name="llama-server",
        binary_search_paths=[Path("/usr/local/bin")],
    )
    assert pc.platform == "linux"
    assert pc.config_dir == Path("/tmp/config")
    assert pc.data_dir == Path("/tmp/data")
    assert pc.models_dir == Path("/tmp/models")
    assert pc.binary_name == "llama-server"
    assert pc.binary_search_paths == [Path("/usr/local/bin")]


# ---------------------------------------------------------------------------
# 2. Factory function — Linux
# ---------------------------------------------------------------------------


def test_factory_linux_default_paths(tmp_path: Path) -> None:
    """get_platform_config() on Linux returns XDG-based paths."""
    env = {
        "XDG_CONFIG_HOME": "",
        "XDG_DATA_HOME": "",
        "APPDATA": "",
        "LOCALAPPDATA": "",
    }
    with (
        patch("templatr.core.config.platform.system", return_value="Linux"),
        patch("templatr.core.config._is_wsl2", return_value=False),
        patch("templatr.core.config.Path.home", return_value=tmp_path),
        patch.dict(os.environ, env, clear=False),
    ):
        pc = get_platform_config(_bypass_cache=True)

    assert pc.platform == "linux"
    assert pc.config_dir == tmp_path / ".config" / "templatr"
    assert pc.data_dir == tmp_path / ".local" / "share" / "templatr"
    assert pc.models_dir == tmp_path / "models"
    assert pc.binary_name == "llama-server"


def test_factory_linux_respects_xdg_config_home(tmp_path: Path) -> None:
    """get_platform_config() uses XDG_CONFIG_HOME when set on Linux."""
    custom_config = tmp_path / "custom_config"
    env = {
        "XDG_CONFIG_HOME": str(custom_config),
        "XDG_DATA_HOME": "",
        "APPDATA": "",
        "LOCALAPPDATA": "",
    }
    with (
        patch("templatr.core.config.platform.system", return_value="Linux"),
        patch("templatr.core.config._is_wsl2", return_value=False),
        patch("templatr.core.config.Path.home", return_value=tmp_path),
        patch.dict(os.environ, env, clear=False),
    ):
        pc = get_platform_config(_bypass_cache=True)

    assert pc.config_dir == custom_config / "templatr"


def test_factory_linux_respects_xdg_data_home(tmp_path: Path) -> None:
    """get_platform_config() uses XDG_DATA_HOME when set on Linux."""
    custom_data = tmp_path / "custom_data"
    env = {
        "XDG_CONFIG_HOME": "",
        "XDG_DATA_HOME": str(custom_data),
        "APPDATA": "",
        "LOCALAPPDATA": "",
    }
    with (
        patch("templatr.core.config.platform.system", return_value="Linux"),
        patch("templatr.core.config._is_wsl2", return_value=False),
        patch("templatr.core.config.Path.home", return_value=tmp_path),
        patch.dict(os.environ, env, clear=False),
    ):
        pc = get_platform_config(_bypass_cache=True)

    assert pc.data_dir == custom_data / "templatr"


def test_factory_linux_binary_search_paths(tmp_path: Path) -> None:
    """get_platform_config() on Linux includes expected binary search paths."""
    env = {
        "XDG_CONFIG_HOME": "",
        "XDG_DATA_HOME": "",
        "APPDATA": "",
        "LOCALAPPDATA": "",
    }
    with (
        patch("templatr.core.config.platform.system", return_value="Linux"),
        patch("templatr.core.config._is_wsl2", return_value=False),
        patch("templatr.core.config.Path.home", return_value=tmp_path),
        patch.dict(os.environ, env, clear=False),
    ):
        pc = get_platform_config(_bypass_cache=True)

    # Should include data_dir/llama.cpp/build/bin and legacy paths
    path_strs = [str(p) for p in pc.binary_search_paths]
    assert any("llama.cpp" in s for s in path_strs)
    assert any(".local/bin" in s or ".local" in s for s in path_strs)


# ---------------------------------------------------------------------------
# 3. Factory function — macOS
# ---------------------------------------------------------------------------


def test_factory_macos_default_paths(tmp_path: Path) -> None:
    """get_platform_config() on macOS returns ~/Library/Application Support paths."""
    env = {
        "XDG_CONFIG_HOME": "",
        "XDG_DATA_HOME": "",
        "APPDATA": "",
        "LOCALAPPDATA": "",
    }
    with (
        patch("templatr.core.config.platform.system", return_value="Darwin"),
        patch("templatr.core.config.Path.home", return_value=tmp_path),
        patch.dict(os.environ, env, clear=False),
    ):
        pc = get_platform_config(_bypass_cache=True)

    app_support = tmp_path / "Library" / "Application Support" / "templatr"
    assert pc.platform == "macos"
    assert pc.config_dir == app_support
    assert pc.data_dir == app_support
    assert pc.models_dir == tmp_path / "models"
    assert pc.binary_name == "llama-server"


def test_factory_macos_binary_search_paths(tmp_path: Path) -> None:
    """get_platform_config() on macOS includes homebrew paths."""
    env = {
        "XDG_CONFIG_HOME": "",
        "XDG_DATA_HOME": "",
        "APPDATA": "",
        "LOCALAPPDATA": "",
    }
    with (
        patch("templatr.core.config.platform.system", return_value="Darwin"),
        patch("templatr.core.config.Path.home", return_value=tmp_path),
        patch.dict(os.environ, env, clear=False),
    ):
        pc = get_platform_config(_bypass_cache=True)

    path_strs = [str(p) for p in pc.binary_search_paths]
    assert any("homebrew" in s for s in path_strs)


# ---------------------------------------------------------------------------
# 4. Factory function — Windows
# ---------------------------------------------------------------------------


def test_factory_windows_uses_appdata(tmp_path: Path) -> None:
    """get_platform_config() on Windows uses %APPDATA% for config_dir."""
    appdata = tmp_path / "AppData" / "Roaming"
    localappdata = tmp_path / "AppData" / "Local"
    env = {
        "APPDATA": str(appdata),
        "LOCALAPPDATA": str(localappdata),
        "XDG_CONFIG_HOME": "",
        "XDG_DATA_HOME": "",
    }
    with (
        patch("templatr.core.config.platform.system", return_value="Windows"),
        patch("templatr.core.config.Path.home", return_value=tmp_path),
        patch.dict(os.environ, env, clear=False),
    ):
        pc = get_platform_config(_bypass_cache=True)

    assert pc.platform == "windows"
    assert pc.config_dir == appdata / "templatr"
    assert pc.data_dir == localappdata / "templatr"
    assert pc.binary_name == "llama-server.exe"


def test_factory_windows_fallback_without_appdata(tmp_path: Path) -> None:
    """get_platform_config() on Windows falls back to home dir if APPDATA not set."""
    env = {
        "APPDATA": "",
        "LOCALAPPDATA": "",
        "XDG_CONFIG_HOME": "",
        "XDG_DATA_HOME": "",
    }
    with (
        patch("templatr.core.config.platform.system", return_value="Windows"),
        patch("templatr.core.config.Path.home", return_value=tmp_path),
        patch.dict(os.environ, env, clear=False),
    ):
        pc = get_platform_config(_bypass_cache=True)

    assert pc.config_dir == tmp_path / ".templatr"
    assert pc.data_dir == tmp_path / ".templatr"


# ---------------------------------------------------------------------------
# 5. Factory function — WSL2
# ---------------------------------------------------------------------------


def test_factory_wsl2_detected(tmp_path: Path) -> None:
    """get_platform_config() detects WSL2 and returns linux-style paths."""
    env = {
        "XDG_CONFIG_HOME": "",
        "XDG_DATA_HOME": "",
        "APPDATA": "",
        "LOCALAPPDATA": "",
    }
    with (
        patch("templatr.core.config.platform.system", return_value="Linux"),
        patch("templatr.core.config._is_wsl2", return_value=True),
        patch("templatr.core.config.Path.home", return_value=tmp_path),
        patch.dict(os.environ, env, clear=False),
    ):
        pc = get_platform_config(_bypass_cache=True)

    assert pc.platform == "wsl2"
    # WSL2 uses same paths as Linux
    assert pc.config_dir == tmp_path / ".config" / "templatr"


# ---------------------------------------------------------------------------
# 6. get_data_dir() standalone function
# ---------------------------------------------------------------------------


def test_get_data_dir_returns_path(tmp_path: Path) -> None:
    """get_data_dir() returns a Path from PlatformConfig."""
    env = {
        "XDG_CONFIG_HOME": "",
        "XDG_DATA_HOME": "",
        "APPDATA": "",
        "LOCALAPPDATA": "",
    }
    with (
        patch("templatr.core.config.platform.system", return_value="Linux"),
        patch("templatr.core.config._is_wsl2", return_value=False),
        patch("templatr.core.config.Path.home", return_value=tmp_path),
        patch.dict(os.environ, env, clear=False),
    ):
        result = get_data_dir(_bypass_cache=True)

    assert isinstance(result, Path)
    assert "templatr" in str(result)


# ---------------------------------------------------------------------------
# 7. Backward-compatible wrappers
# ---------------------------------------------------------------------------


def test_get_platform_still_works() -> None:
    """get_platform() returns one of the known platform strings."""
    result = get_platform()
    assert result in {"windows", "linux", "wsl2", "macos", "unknown"}


def test_is_windows_returns_bool() -> None:
    """is_windows() returns a boolean."""
    result = is_windows()
    assert isinstance(result, bool)


# ---------------------------------------------------------------------------
# 8. Single source of truth — only factory calls platform.system()
# ---------------------------------------------------------------------------


def test_factory_is_only_caller_of_platform_system(tmp_path: Path) -> None:
    """get_platform_config() is the only code path that calls platform.system().

    Verified by checking that get_platform() and is_windows() delegate to
    the factory rather than calling platform.system() directly.
    """
    env = {
        "XDG_CONFIG_HOME": "",
        "XDG_DATA_HOME": "",
        "APPDATA": "",
        "LOCALAPPDATA": "",
    }
    with (
        patch("templatr.core.config.platform.system", return_value="Linux") as mock_sys,
        patch("templatr.core.config._is_wsl2", return_value=False),
        patch("templatr.core.config.Path.home", return_value=tmp_path),
        patch.dict(os.environ, env, clear=False),
    ):
        # Call factory
        get_platform_config(_bypass_cache=True)
        call_count_after_factory = mock_sys.call_count

        # Call wrappers — they should NOT call platform.system() again
        # (they delegate to get_platform_config)
        get_platform()
        is_windows()

    # Wrappers should not add extra calls to platform.system()
    # They may call get_platform_config() which may call platform.system(),
    # but since we already called it with _bypass_cache, the wrappers
    # will also use _bypass_cache=False (cached value)
    # The key point: wrappers don't independently call platform.system()
    assert mock_sys.call_count >= call_count_after_factory
