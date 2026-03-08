"""Tests for templatr.integrations.llm.LLMServerManager — filesystem operations mocked.

Covers: find_server_binary() resolves configured path, falls back through
search locations, returns None when nothing found; find_models() discovers
.gguf files in a model directory, returns empty list when no models exist.

No real processes are started. Filesystem interactions use tmp_path or
unittest.mock to avoid side effects.
"""

import stat
from pathlib import Path
from unittest.mock import patch

from templatr.core.config import LLMConfig, PlatformConfig
from templatr.integrations.llm import LLMServerManager

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _linux_platform_config(home: Path) -> PlatformConfig:
    """Build a PlatformConfig for Linux tests."""
    data_dir = home / ".local" / "share" / "templatr"
    return PlatformConfig(
        platform="linux",
        config_dir=home / ".config" / "templatr",
        data_dir=data_dir,
        models_dir=home / "models",
        binary_name="llama-server",
        binary_search_paths=[
            data_dir / "llama.cpp" / "build" / "bin",
            data_dir / "vendor" / "llama-server",
            home / "llama.cpp" / "build" / "bin",
            home / ".local" / "bin",
            Path("/usr/local/bin"),
        ],
    )


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

    pc = _linux_platform_config(tmp_path)
    with patch("templatr.integrations.llm.get_platform_config", return_value=pc):
        with patch("templatr.integrations.llm.shutil.which", return_value=None):
            result = mgr.find_server_binary()

    assert result is None


# ---------------------------------------------------------------------------
# 2. find_server_binary() falls back through search locations
# ---------------------------------------------------------------------------


def test_find_server_binary_finds_binary_in_templatr_data_dir(tmp_path: Path) -> None:
    """find_server_binary() finds the binary in the PlatformConfig data dir search path."""
    pc = _linux_platform_config(tmp_path)
    binary_name = pc.binary_name
    # The first binary_search_path is data_dir/llama.cpp/build/bin
    data_bin_dir = pc.binary_search_paths[0]
    data_bin_dir.mkdir(parents=True)
    binary = data_bin_dir / binary_name
    binary.write_text("#!/bin/sh\n")
    _make_executable(binary)

    cfg = LLMConfig(server_binary="")  # no configured path
    mgr = _manager_with_config(cfg)

    with patch("templatr.integrations.llm.get_platform_config", return_value=pc):
        with patch("templatr.integrations.llm.shutil.which", return_value=None):
            result = mgr.find_server_binary()

    assert result == binary


def test_find_server_binary_falls_back_to_path_environment(tmp_path: Path) -> None:
    """find_server_binary() finds binary via PATH when data dir has nothing."""
    pc = _linux_platform_config(tmp_path)
    binary_name = pc.binary_name
    path_binary = tmp_path / binary_name

    cfg = LLMConfig(server_binary="")
    mgr = _manager_with_config(cfg)

    with patch("templatr.integrations.llm.get_platform_config", return_value=pc):
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
    pc = _linux_platform_config(tmp_path)
    cfg = LLMConfig(server_binary="")
    mgr = _manager_with_config(cfg)

    with patch("templatr.integrations.llm.get_platform_config", return_value=pc):
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


# ---------------------------------------------------------------------------
# 6. find_server_binary() finds binary in vendor/llama-server/ under data dir
# ---------------------------------------------------------------------------


def test_find_server_binary_finds_binary_in_vendor_dir(tmp_path: Path) -> None:
    """find_server_binary() finds the binary in the data_dir/vendor/llama-server/ path."""
    pc = _linux_platform_config(tmp_path)
    binary_name = pc.binary_name
    # The vendor search path is data_dir/vendor/llama-server
    vendor_dir = pc.binary_search_paths[1]
    vendor_dir.mkdir(parents=True)
    binary = vendor_dir / binary_name
    binary.write_text("#!/bin/sh\n")
    _make_executable(binary)

    cfg = LLMConfig(server_binary="")  # no configured path
    mgr = _manager_with_config(cfg)

    with patch("templatr.integrations.llm.get_platform_config", return_value=pc):
        with patch("templatr.integrations.llm.shutil.which", return_value=None):
            result = mgr.find_server_binary()

    assert result == binary


# ---------------------------------------------------------------------------
# 7. LLMClient.close_active_stream() closes the active response
# ---------------------------------------------------------------------------


def test_close_active_stream_closes_response() -> None:
    """close_active_stream() calls close() on the active response."""
    from templatr.integrations.llm import LLMClient

    client = LLMClient()
    mock_response = type("FakeResponse", (), {"close": lambda self: None})()
    client._active_response = mock_response

    with patch.object(mock_response, "close") as mock_close:
        client.close_active_stream()

    mock_close.assert_called_once()


def test_close_active_stream_noop_when_no_response() -> None:
    """close_active_stream() is a no-op when no active response exists."""
    from templatr.integrations.llm import LLMClient

    client = LLMClient()
    assert client._active_response is None
    client.close_active_stream()  # should not raise


# ---------------------------------------------------------------------------
# 8. LLMClient.generate_stream() uses tuple timeout
# ---------------------------------------------------------------------------


def test_generate_stream_uses_tuple_timeout() -> None:
    """generate_stream() passes a (connect, read) timeout tuple to requests."""
    from templatr.integrations.llm import LLMClient

    client = LLMClient()

    mock_response = type(
        "FakeResponse",
        (),
        {
            "raise_for_status": lambda self: None,
            "iter_lines": lambda self: iter([]),
            "close": lambda self: None,
            "__enter__": lambda self: self,
            "__exit__": lambda *a: None,
        },
    )()

    with patch("templatr.integrations.llm.requests.post", return_value=mock_response) as mock_post:
        with patch("templatr.integrations.llm.get_config") as mock_config:
            mock_config.return_value.llm.max_tokens = 100
            mock_config.return_value.llm.temperature = 0.7
            mock_config.return_value.llm.top_p = 1.0
            mock_config.return_value.llm.top_k = 40
            mock_config.return_value.llm.repeat_penalty = 1.1
            # Consume the generator
            list(client.generate_stream("test"))

    _, kwargs = mock_post.call_args
    assert kwargs["timeout"] == (10, 90)
