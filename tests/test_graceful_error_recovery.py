"""Tests for graceful error recovery & model validation (spec: graceful-error-recovery)."""

import struct
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


# ---------------------------------------------------------------------------
# Task 2: Human-readable errors, retry button, exponential backoff
# ---------------------------------------------------------------------------


class TestFormatErrorMessage:
    """format_error_message() translates exceptions to user-friendly text."""

    def test_connection_refused(self):
        """ConnectionRefusedError → helpful message about starting server."""
        from templatr.ui.workers import format_error_message

        msg = format_error_message(ConnectionRefusedError("Connection refused"))
        assert "server" in msg.lower()
        assert "start" in msg.lower()

    def test_connection_error(self):
        """ConnectionError → helpful message about starting server."""
        from templatr.ui.workers import format_error_message

        msg = format_error_message(
            ConnectionError("Cannot connect to LLM server")
        )
        assert "server" in msg.lower()

    def test_timeout_error(self):
        """TimeoutError → message about model loading or long prompt."""
        from templatr.ui.workers import format_error_message

        msg = format_error_message(TimeoutError("timed out"))
        assert "timed out" in msg.lower() or "timeout" in msg.lower()

    def test_runtime_error_passthrough(self):
        """RuntimeError with existing message → preserved as-is."""
        from templatr.ui.workers import format_error_message

        msg = format_error_message(RuntimeError("Generation failed: 500"))
        assert "Generation failed" in msg

    def test_unknown_error(self):
        """Unknown exception types → generic user-friendly message."""
        from templatr.ui.workers import format_error_message

        msg = format_error_message(ValueError("something weird"))
        assert len(msg) > 0  # should produce some message, not crash


class TestExponentialBackoff:
    """GenerationWorker uses 1s/2s/4s exponential backoff on retries."""

    def test_backoff_delays(self):
        """Retry delays follow exponential backoff pattern."""
        from templatr.ui.workers import GenerationWorker

        worker = GenerationWorker("test prompt")
        delays = worker.RETRY_DELAYS
        assert delays == [1.0, 2.0, 4.0]

    def test_retry_count_matches_delays(self):
        """MAX_RETRY_ATTEMPTS matches the number of delay values."""
        from templatr.ui.workers import GenerationWorker

        worker = GenerationWorker("test prompt")
        assert worker.MAX_RETRY_ATTEMPTS == len(worker.RETRY_DELAYS)


class TestOutputPaneErrorDisplay:
    """OutputPaneWidget.show_error() displays styled error with Retry button."""

    @pytest.fixture
    def output_pane(self, qtbot):
        from templatr.ui.output_pane import OutputPaneWidget

        widget = OutputPaneWidget()
        qtbot.addWidget(widget)
        widget.show()
        return widget

    def test_show_error_displays_message(self, output_pane):
        """show_error() puts error text in the output area."""
        output_pane.show_error("Something went wrong")
        text = output_pane.get_text()
        assert "Something went wrong" in text

    def test_show_error_shows_retry_button(self, output_pane):
        """show_error() makes the retry button visible."""
        output_pane.show_error("fail")
        assert output_pane._retry_btn.isVisible()

    def test_retry_button_emits_signal(self, output_pane, qtbot):
        """Clicking the retry button emits retry_requested."""
        output_pane.show_error("fail")
        with qtbot.waitSignal(output_pane.retry_requested, timeout=1000):
            output_pane._retry_btn.click()

    def test_retry_button_hidden_on_clear(self, output_pane):
        """Clearing the output hides the retry button."""
        output_pane.show_error("fail")
        output_pane.clear()
        assert not output_pane._retry_btn.isVisible()

    def test_retry_button_hidden_during_streaming(self, output_pane):
        """Starting streaming hides the retry button."""
        output_pane.show_error("fail")
        output_pane.set_streaming(True)
        assert not output_pane._retry_btn.isVisible()


# ---------------------------------------------------------------------------
# Task 3: Health polling, server death detection, button states
# ---------------------------------------------------------------------------


class TestHealthPoller:
    """LLMToolbar polls server health and reflects status in the UI."""

    @pytest.fixture
    def toolbar(self, qtbot):
        from templatr.ui.llm_toolbar import LLMToolbar

        widget = LLMToolbar()
        qtbot.addWidget(widget)
        widget.show()
        return widget

    def test_toolbar_has_health_timer(self, toolbar):
        """LLMToolbar has a _health_timer attribute for periodic polling."""
        assert hasattr(toolbar, "_health_timer")

    def test_status_label_shows_healthy(self, toolbar):
        """When server is healthy, label shows 'Healthy'."""
        toolbar._update_health_status("healthy")
        assert "Healthy" in toolbar.llm_status_label.text()

    def test_status_label_shows_degraded(self, toolbar):
        """When health check returns degraded, label reflects it."""
        toolbar._update_health_status("degraded")
        assert "Degraded" in toolbar.llm_status_label.text()

    def test_status_label_shows_stopped(self, toolbar):
        """When server is stopped, label shows 'Stopped'."""
        toolbar._update_health_status("stopped")
        assert "Stopped" in toolbar.llm_status_label.text()

    @patch("templatr.ui.llm_toolbar.get_llm_server")
    def test_process_death_detected(self, mock_get_server, toolbar):
        """If server process unexpectedly exits, status updates to stopped."""
        mock_server = MagicMock()
        mock_server.is_running.return_value = False
        mock_server._process = None
        mock_get_server.return_value = mock_server

        toolbar._poll_health()
        assert "Stopped" in toolbar.llm_status_label.text() or "Not Running" in toolbar.llm_status_label.text()


class TestRenderButtonDisabledState:
    """'Render with AI' button disabled when no model is loaded."""

    @pytest.fixture
    def variable_form(self, qtbot):
        from templatr.ui.variable_form import VariableFormWidget

        widget = VariableFormWidget()
        qtbot.addWidget(widget)
        widget.show()
        return widget

    def test_button_disabled_by_default(self, variable_form):
        """Button starts disabled."""
        assert not variable_form.generate_btn.isEnabled()

    def test_update_llm_state_no_model(self, variable_form):
        """When server not running, button is disabled with tooltip."""
        variable_form.update_llm_ready(False)
        assert not variable_form.generate_btn.isEnabled()
        tooltip = variable_form.generate_btn.toolTip()
        assert "server" in tooltip.lower() or "model" in tooltip.lower()

    def test_update_llm_state_with_model(self, variable_form):
        """When server is running with a model, button is enabled."""
        variable_form.update_llm_ready(True)
        assert variable_form.generate_btn.isEnabled()
        assert variable_form.generate_btn.toolTip() == ""
