"""Tests for the ``templatr --doctor`` CLI diagnostic command.

Covers:
- Prints platform, config dir, data dir, templates count, models count, binary status
- Exits 0 when all checks pass
- Exits 1 when critical item is missing (e.g. no templates)
- Works without llama-server installed
"""

from pathlib import Path
from unittest.mock import patch

from templatr.core.config import PlatformConfig

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_platform_config(tmp_path: Path) -> PlatformConfig:
    """Build a PlatformConfig for testing."""
    config_dir = tmp_path / "config"
    data_dir = tmp_path / "data"
    models_dir = tmp_path / "models"
    return PlatformConfig(
        platform="linux",
        config_dir=config_dir,
        data_dir=data_dir,
        models_dir=models_dir,
        binary_name="llama-server",
        binary_search_paths=[data_dir / "llama.cpp" / "build" / "bin"],
    )


def _run_doctor(pc: PlatformConfig, capsys) -> int:
    """Run the doctor command with a mocked PlatformConfig."""
    with patch("templatr.doctor.get_platform_config", return_value=pc):
        from templatr.doctor import run_doctor

        code = run_doctor()
    return code


# ---------------------------------------------------------------------------
# 1. Doctor reports platform info
# ---------------------------------------------------------------------------


def test_doctor_reports_platform(tmp_path: Path, capsys) -> None:
    """--doctor output includes the detected platform."""
    pc = _make_platform_config(tmp_path)
    pc.config_dir.mkdir(parents=True)
    pc.models_dir.mkdir(parents=True)
    # Create a template dir with at least one template
    templates_dir = pc.config_dir / "templates"
    templates_dir.mkdir(parents=True)
    (templates_dir / "test.json").write_text("{}")

    _run_doctor(pc, capsys)
    captured = capsys.readouterr()
    assert "linux" in captured.out


def test_doctor_reports_config_dir(tmp_path: Path, capsys) -> None:
    """--doctor output includes the config directory path."""
    pc = _make_platform_config(tmp_path)
    pc.config_dir.mkdir(parents=True)
    pc.models_dir.mkdir(parents=True)
    templates_dir = pc.config_dir / "templates"
    templates_dir.mkdir(parents=True)
    (templates_dir / "test.json").write_text("{}")

    _run_doctor(pc, capsys)
    captured = capsys.readouterr()
    assert str(pc.config_dir) in captured.out


def test_doctor_reports_data_dir(tmp_path: Path, capsys) -> None:
    """--doctor output includes the data directory path."""
    pc = _make_platform_config(tmp_path)
    pc.config_dir.mkdir(parents=True)
    pc.models_dir.mkdir(parents=True)
    templates_dir = pc.config_dir / "templates"
    templates_dir.mkdir(parents=True)
    (templates_dir / "test.json").write_text("{}")

    _run_doctor(pc, capsys)
    captured = capsys.readouterr()
    assert str(pc.data_dir) in captured.out


# ---------------------------------------------------------------------------
# 2. Exit code 0 when all checks pass
# ---------------------------------------------------------------------------


def test_doctor_exits_0_when_healthy(tmp_path: Path, capsys) -> None:
    """--doctor exits 0 when templates exist."""
    pc = _make_platform_config(tmp_path)
    pc.config_dir.mkdir(parents=True)
    pc.models_dir.mkdir(parents=True)
    templates_dir = pc.config_dir / "templates"
    templates_dir.mkdir(parents=True)
    (templates_dir / "test.json").write_text("{}")

    code = _run_doctor(pc, capsys)
    assert code == 0


# ---------------------------------------------------------------------------
# 3. Exit code 1 when critical item missing
# ---------------------------------------------------------------------------


def test_doctor_exits_1_when_no_templates(tmp_path: Path, capsys) -> None:
    """--doctor exits 1 when no templates are found."""
    pc = _make_platform_config(tmp_path)
    pc.config_dir.mkdir(parents=True)
    pc.models_dir.mkdir(parents=True)
    templates_dir = pc.config_dir / "templates"
    templates_dir.mkdir(parents=True)
    # No .json files

    code = _run_doctor(pc, capsys)
    assert code == 1


# ---------------------------------------------------------------------------
# 4. Works without llama-server installed
# ---------------------------------------------------------------------------


def test_doctor_works_without_server(tmp_path: Path, capsys) -> None:
    """--doctor runs successfully even when llama-server is not installed."""
    pc = _make_platform_config(tmp_path)
    pc.config_dir.mkdir(parents=True)
    pc.models_dir.mkdir(parents=True)
    templates_dir = pc.config_dir / "templates"
    templates_dir.mkdir(parents=True)
    (templates_dir / "test.json").write_text("{}")

    # No binary exists anywhere
    _run_doctor(pc, capsys)
    captured = capsys.readouterr()
    assert "not found" in captured.out.lower() or "llama-server" in captured.out


# ---------------------------------------------------------------------------
# 5. Reports model count
# ---------------------------------------------------------------------------


def test_doctor_reports_model_count(tmp_path: Path, capsys) -> None:
    """--doctor reports the number of model files found."""
    pc = _make_platform_config(tmp_path)
    pc.config_dir.mkdir(parents=True)
    pc.models_dir.mkdir(parents=True)
    templates_dir = pc.config_dir / "templates"
    templates_dir.mkdir(parents=True)
    (templates_dir / "test.json").write_text("{}")
    # Create some model files
    (pc.models_dir / "model1.gguf").write_bytes(b"\x00")
    (pc.models_dir / "model2.gguf").write_bytes(b"\x00")

    _run_doctor(pc, capsys)
    captured = capsys.readouterr()
    assert "2" in captured.out


# ---------------------------------------------------------------------------
# 6. Reports binary found with path
# ---------------------------------------------------------------------------


def test_doctor_reports_binary_found(tmp_path: Path, capsys) -> None:
    """--doctor reports the llama-server binary path when found."""
    pc = _make_platform_config(tmp_path)
    pc.config_dir.mkdir(parents=True)
    pc.models_dir.mkdir(parents=True)
    templates_dir = pc.config_dir / "templates"
    templates_dir.mkdir(parents=True)
    (templates_dir / "test.json").write_text("{}")

    # Create a binary in a search path
    bin_dir = pc.binary_search_paths[0]
    bin_dir.mkdir(parents=True)
    binary = bin_dir / pc.binary_name
    binary.write_text("#!/bin/sh\n")
    binary.chmod(0o755)

    with patch("templatr.doctor.shutil.which", return_value=None):
        _run_doctor(pc, capsys)

    captured = capsys.readouterr()
    assert str(binary) in captured.out
