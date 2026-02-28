"""Tests for templatr.integrations.llm.LLMServerManager — filesystem operations mocked.

Covers: find_server_binary() resolves configured path, falls back through
search locations, returns None when nothing found; find_models() discovers
.gguf files in a model directory, returns empty list when no models exist.

No real processes are started. Filesystem interactions use tmp_path or
unittest.mock to avoid side effects.
"""

import os
import stat
from pathlib import Path
from unittest.mock import patch

from templatr.core.config import LLMConfig
from templatr.integrations.llm import LLMServerManager

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_executable(path: Path) -> None:
    """Mark a file as executable."""
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def _manager_with_config(llm_cfg: LLMConfig) -> LLMServerManager:
    """Build an LLMServerManager using a specific LLMConfig (bypasses global config)."""
    mgr = LLMServerManager.__new__(LLMServerManager)
    mgr.config = llm_cfg
    mgr._process = None
    return mgr


# ---------------------------------------------------------------------------
# 1. find_server_binary() finds binary at configured path
# ---------------------------------------------------------------------------


def test_find_server_binary_uses_configured_path(tmp_path: Path) -> None:
    """find_server_binary() returns the configured path when the binary exists and is executable."""
    binary = tmp_path / "llama-server"
    binary.write_text("#!/bin/sh\n")
    _make_executable(binary)

    cfg = LLMConfig(server_binary=str(binary))
    mgr = _manager_with_config(cfg)

    result = mgr.find_server_binary()
    assert result == binary


def test_find_server_binary_skips_configured_path_when_not_executable(
    tmp_path: Path,
) -> None:
    """find_server_binary() skips the configured path if it is not executable."""
    binary = tmp_path / "llama-server"
    binary.write_text("#!/bin/sh\n")
    # Do NOT make it executable

    cfg = LLMConfig(server_binary=str(binary))
    mgr = _manager_with_config(cfg)

    # Redirect Path.home() to tmp_path and stub PATH lookup to isolate the test
    # from any real llama-server binaries installed on the host machine.
    with patch("templatr.integrations.llm.Path.home", return_value=tmp_path):
        with patch("templatr.integrations.llm.shutil.which", return_value=None):
            result = mgr.find_server_binary()

    assert result is None


# ---------------------------------------------------------------------------
# 2. find_server_binary() falls back through search locations
# ---------------------------------------------------------------------------


def test_find_server_binary_finds_binary_in_templatr_data_dir(tmp_path: Path) -> None:
    """find_server_binary() finds the binary in ~/.local/share/templatr/llama.cpp/build/bin/."""
    # Build the expected templatr data dir path
    binary_name = "llama-server" if os.name != "nt" else "llama-server.exe"
    data_dir = (
        tmp_path / ".local" / "share" / "templatr" / "llama.cpp" / "build" / "bin"
    )
    data_dir.mkdir(parents=True)
    binary = data_dir / binary_name
    binary.write_text("#!/bin/sh\n")
    _make_executable(binary)

    cfg = LLMConfig(server_binary="")  # no configured path
    mgr = _manager_with_config(cfg)

    # Patch Path.home() to point to tmp_path
    with patch("templatr.integrations.llm.Path.home", return_value=tmp_path):
        with patch("templatr.integrations.llm.shutil.which", return_value=None):
            result = mgr.find_server_binary()

    assert result == binary


def test_find_server_binary_falls_back_to_path_environment(tmp_path: Path) -> None:
    """find_server_binary() finds binary via PATH when data dir has nothing."""
    binary_name = "llama-server" if os.name != "nt" else "llama-server.exe"
    path_binary = tmp_path / binary_name

    cfg = LLMConfig(server_binary="")
    mgr = _manager_with_config(cfg)

    with patch("templatr.integrations.llm.Path.home", return_value=tmp_path):
        with patch(
            "templatr.integrations.llm.shutil.which", return_value=str(path_binary)
        ):
            result = mgr.find_server_binary()

    assert result == path_binary


# ---------------------------------------------------------------------------
# 3. find_server_binary() returns None when nothing found
# ---------------------------------------------------------------------------


def test_find_server_binary_returns_none_when_nothing_found(tmp_path: Path) -> None:
    """find_server_binary() returns None when the binary cannot be located anywhere."""
    cfg = LLMConfig(server_binary="")
    mgr = _manager_with_config(cfg)

    with patch("templatr.integrations.llm.Path.home", return_value=tmp_path):
        with patch("templatr.integrations.llm.shutil.which", return_value=None):
            result = mgr.find_server_binary()

    assert result is None


# ---------------------------------------------------------------------------
# 4. find_models() discovers .gguf files in model directory
# ---------------------------------------------------------------------------


def test_find_models_discovers_gguf_files(tmp_path: Path) -> None:
    """find_models() returns ModelInfo for each .gguf file found in model_dir."""
    model_dir = tmp_path / "models"
    model_dir.mkdir()
    (model_dir / "small.gguf").write_bytes(b"\x00" * 1024)
    (model_dir / "large.gguf").write_bytes(b"\x00" * 2048)
    (model_dir / "not_a_model.txt").write_text("ignore me")

    cfg = LLMConfig(model_dir=str(model_dir))
    mgr = _manager_with_config(cfg)

    models = mgr.find_models()

    assert len(models) == 2
    names = {m.name for m in models}
    assert "small" in names
    assert "large" in names


def test_find_models_returns_sorted_by_name(tmp_path: Path) -> None:
    """find_models() returns ModelInfo list sorted by name (case-insensitive)."""
    model_dir = tmp_path / "models"
    model_dir.mkdir()
    (model_dir / "zebra.gguf").write_bytes(b"\x00" * 100)
    (model_dir / "alpha.gguf").write_bytes(b"\x00" * 100)
    (model_dir / "middle.gguf").write_bytes(b"\x00" * 100)

    cfg = LLMConfig(model_dir=str(model_dir))
    mgr = _manager_with_config(cfg)

    models = mgr.find_models()
    names = [m.name for m in models]
    assert names == sorted(names, key=str.lower)


# ---------------------------------------------------------------------------
# 5. find_models() returns empty list when no models exist
# ---------------------------------------------------------------------------


def test_find_models_returns_empty_list_for_empty_directory(tmp_path: Path) -> None:
    """find_models() returns [] when the model directory has no .gguf files."""
    model_dir = tmp_path / "empty_models"
    model_dir.mkdir()

    cfg = LLMConfig(model_dir=str(model_dir))
    mgr = _manager_with_config(cfg)

    models = mgr.find_models()
    assert models == []


def test_find_models_returns_empty_list_when_directory_missing(tmp_path: Path) -> None:
    """find_models() returns [] when the configured model directory does not exist."""
    cfg = LLMConfig(model_dir=str(tmp_path / "nonexistent"))
    mgr = _manager_with_config(cfg)

    models = mgr.find_models()
    assert models == []
