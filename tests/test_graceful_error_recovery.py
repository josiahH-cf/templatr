"""Tests for graceful error recovery & model validation (spec: graceful-error-recovery)."""

import struct
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Task 1: GGUF validation
# ---------------------------------------------------------------------------

GGUF_MAGIC = b"GGUF"  # 0x47475546


class TestValidateGguf:
    """validate_gguf() checks the first 4 bytes of a model file."""

    def test_valid_gguf_file(self, tmp_path):
        """A file starting with GGUF magic bytes passes validation."""
        from templatr.integrations.llm import validate_gguf

        model = tmp_path / "good.gguf"
        model.write_bytes(GGUF_MAGIC + b"\x00" * 100)
        valid, msg = validate_gguf(model)
        assert valid is True
        assert msg == ""

    def test_invalid_magic_bytes(self, tmp_path):
        """A file with wrong magic bytes is rejected with a clear message."""
        from templatr.integrations.llm import validate_gguf

        model = tmp_path / "bad.gguf"
        model.write_bytes(b"\x00\x01\x02\x03" + b"\x00" * 100)
        valid, msg = validate_gguf(model)
        assert valid is False
        assert "bad.gguf" in msg
        assert "GGUF" in msg

    def test_file_too_small(self, tmp_path):
        """A file smaller than 4 bytes is rejected."""
        from templatr.integrations.llm import validate_gguf

        model = tmp_path / "tiny.gguf"
        model.write_bytes(b"\x00\x01")
        valid, msg = validate_gguf(model)
        assert valid is False
        assert "tiny.gguf" in msg

    def test_file_not_found(self, tmp_path):
        """A nonexistent file is rejected."""
        from templatr.integrations.llm import validate_gguf

        model = tmp_path / "missing.gguf"
        valid, msg = validate_gguf(model)
        assert valid is False
        assert "missing.gguf" in msg

    def test_valid_gguf_with_version_header(self, tmp_path):
        """A full GGUF header (magic + version) passes validation."""
        from templatr.integrations.llm import validate_gguf

        model = tmp_path / "versioned.gguf"
        # GGUF magic + version 3 (little-endian uint32)
        model.write_bytes(GGUF_MAGIC + struct.pack("<I", 3) + b"\x00" * 100)
        valid, msg = validate_gguf(model)
        assert valid is True


class TestModelCopyWithValidation:
    """ModelCopyWorker should validate GGUF before completing the copy."""

    def test_copy_invalid_file_emits_failure(self, tmp_path):
        """Copying a non-GGUF file should report validation failure."""
        from templatr.ui.workers import ModelCopyWorker

        source = tmp_path / "not_gguf.gguf"
        source.write_bytes(b"NOT_GGUF_DATA" + b"\x00" * 100)
        dest = tmp_path / "dest" / "not_gguf.gguf"
        dest.parent.mkdir(parents=True, exist_ok=True)

        worker = ModelCopyWorker(source, dest)
        results = []
        worker.finished.connect(lambda ok, msg: results.append((ok, msg)))
        worker.run()  # run synchronously for testing

        assert len(results) == 1
        success, message = results[0]
        assert success is False
        assert "GGUF" in message

    def test_copy_valid_file_succeeds(self, tmp_path):
        """Copying a valid GGUF file should succeed."""
        from templatr.ui.workers import ModelCopyWorker

        source = tmp_path / "good.gguf"
        source.write_bytes(GGUF_MAGIC + b"\x00" * 1024)
        dest = tmp_path / "dest" / "good.gguf"
        dest.parent.mkdir(parents=True, exist_ok=True)

        worker = ModelCopyWorker(source, dest)
        results = []
        worker.finished.connect(lambda ok, msg: results.append((ok, msg)))
        worker.run()

        assert len(results) == 1
        success, message = results[0]
        assert success is True
