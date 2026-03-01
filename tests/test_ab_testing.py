"""Tests for prompt A/B testing (/test slash command).

Covers acceptance criteria AC-1 through AC-10 from specs/prompt-ab-testing.md.
"""

from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_window(qtbot):
    """Create a MainWindow with mocked external dependencies."""
    mock_template_mgr = MagicMock()
    mock_template_mgr.list_all.return_value = []
    mock_template_mgr.list_folders.return_value = []
    mock_template_mgr.get_template_folder.return_value = ""

    mock_llm_server = MagicMock()
    mock_llm_server.is_running.return_value = False
    mock_llm_client = MagicMock()

    with patch(
        "templatr.ui.template_tree.get_template_manager",
        return_value=mock_template_mgr,
    ), patch(
        "templatr.ui.llm_toolbar.get_llm_server",
        return_value=mock_llm_server,
    ):
        from templatr.ui.main_window import MainWindow

        win = MainWindow(
            templates=mock_template_mgr,
            llm_client=mock_llm_client,
            llm_server=mock_llm_server,
        )
        qtbot.addWidget(win)
        win.show()
        return win


def _last_system_messages(win, n: int = 1) -> list[str]:
    """Return the raw text of the last n message bubbles."""
    from templatr.ui.message_bubble import MessageBubble

    bubbles = win.chat_widget.findChildren(MessageBubble)
    return [b.get_raw_text() for b in bubbles[-n:]]


# ---------------------------------------------------------------------------
# ABTestWorker unit tests (AC-1, AC-2, AC-3)
# ---------------------------------------------------------------------------


def test_ab_test_worker_runs_n_iterations():
    """ABTestWorker calls generate() exactly N times and returns N results (AC-1)."""
    mock_client = MagicMock()
    mock_client.generate.return_value = "output"

    with patch("templatr.ui.workers.get_llm_client", return_value=mock_client):
        from templatr.ui.workers import ABTestWorker

        results = []
        worker = ABTestWorker("hello", iterations=3)
        worker.finished.connect(results.append)
        worker.run()  # run directly in-thread for test

    assert mock_client.generate.call_count == 3
    assert len(results) == 1
    assert len(results[0]) == 3


def test_ab_test_worker_progress_signals():
    """ABTestWorker emits progress(i, total) for each iteration (AC-2)."""
    mock_client = MagicMock()
    mock_client.generate.return_value = "out"

    with patch("templatr.ui.workers.get_llm_client", return_value=mock_client):
        from templatr.ui.workers import ABTestWorker

        progress_calls = []
        worker = ABTestWorker("prompt", iterations=3)
        worker.progress.connect(lambda i, t: progress_calls.append((i, t)))
        worker.run()

    assert progress_calls == [(1, 3), (2, 3), (3, 3)]


def test_ab_test_worker_results_include_metadata():
    """Each result dict has iteration, output, latency_seconds, and token estimates (AC-3)."""
    mock_client = MagicMock()
    mock_client.generate.return_value = "hello world"

    with patch("templatr.ui.workers.get_llm_client", return_value=mock_client):
        from templatr.ui.workers import ABTestWorker

        results = []
        worker = ABTestWorker("test", iterations=2)
        worker.finished.connect(results.append)
        worker.run()

    for i, r in enumerate(results[0], start=1):
        assert r["iteration"] == i
        assert r["output"] == "hello world"
        assert isinstance(r["latency_seconds"], float)
        assert r["prompt_tokens_est"] >= 1
        assert r["output_tokens_est"] >= 1


def test_ab_test_worker_respects_stop():
    """Calling stop() prevents remaining iterations from running (AC-8)."""
    call_count = 0

    def slow_generate(*_args, **_kwargs):
        nonlocal call_count
        call_count += 1
        return "output"

    mock_client = MagicMock()
    mock_client.generate.side_effect = slow_generate

    with patch("templatr.ui.workers.get_llm_client", return_value=mock_client):
        from templatr.ui.workers import ABTestWorker

        worker = ABTestWorker("prompt", iterations=5)
        # Stop before any iteration runs
        worker.stop()
        finished_called = []
        worker.finished.connect(finished_called.append)
        worker.run()

    assert call_count == 0
    assert finished_called == []


def test_ab_test_worker_emits_error_on_exception():
    """ABTestWorker emits error signal (not crash) when generate() raises (AC-7)."""
    mock_client = MagicMock()
    mock_client.generate.side_effect = ConnectionRefusedError("no server")

    with patch("templatr.ui.workers.get_llm_client", return_value=mock_client):
        from templatr.ui.workers import ABTestWorker

        errors = []
        worker = ABTestWorker("prompt", iterations=2)
        worker.error.connect(errors.append)
        worker.run()

    assert errors
    assert "LLM server" in errors[0] or "server" in errors[0].lower()


# ---------------------------------------------------------------------------
# /test command parsing and dispatch (main_window, AC-1, AC-7)
# ---------------------------------------------------------------------------


def test_test_command_ignored_for_non_test_input(qtbot):
    """_handle_test_command returns False for unrelated text."""
    win = _make_window(qtbot)
    assert win._handle_test_command("hello world") is False


def test_test_command_no_prompt_shows_error(qtbot):
    """No prompt available → system message with guidance (AC-7)."""
    win = _make_window(qtbot)
    win._last_prompt = None

    handled = win._handle_test_command("/test")

    assert handled is True
    msgs = _last_system_messages(win)
    assert any("No prompt" in m for m in msgs)


def test_test_command_n_less_than_2_shows_error(qtbot):
    """N < 2 shows error message (AC-7)."""
    win = _make_window(qtbot)
    win._last_prompt = "some prompt"

    handled = win._handle_test_command("/test 1")

    assert handled is True
    msgs = _last_system_messages(win)
    assert any("at least 2" in m.lower() for m in msgs)


def test_test_command_server_not_running_shows_error(qtbot):
    """Server not running → system message, no worker started (AC-7)."""
    win = _make_window(qtbot)
    win._last_prompt = "some prompt"
    win.llm_server.is_running.return_value = False

    with patch("templatr.ui.main_window.get_llm_server", return_value=win.llm_server):
        handled = win._handle_test_command("/test 3")

    assert handled is True
    msgs = _last_system_messages(win)
    assert any("not running" in m.lower() or "server" in m.lower() for m in msgs)


def test_test_command_dispatches_worker(qtbot):
    """/test with a prompt and server running starts ABTestWorker (AC-1)."""
    win = _make_window(qtbot)
    win._last_prompt = "test prompt"

    captured = {}

    class _Sig:
        def connect(self, _fn):
            pass

    class FakeABTestWorker:
        def __init__(self, prompt, iterations):
            captured["prompt"] = prompt
            captured["iterations"] = iterations
            self.progress = _Sig()
            self.error = _Sig()
            self.finished = _Sig()

        def isRunning(self):  # noqa: N802
            return False

        def start(self):
            captured["started"] = True

    server_mock = MagicMock()
    server_mock.is_running.return_value = True

    with patch("templatr.ui.main_window.get_llm_server", return_value=server_mock), patch(
        "templatr.ui.main_window.ABTestWorker", FakeABTestWorker
    ):
        handled = win._handle_test_command("/test 3")

    assert handled is True
    assert captured.get("started") is True
    assert captured["iterations"] == 3
    assert captured["prompt"] == "test prompt"


def test_test_command_inline_prompt(qtbot):
    """Custom prompt after | overrides last prompt (AC-1)."""
    win = _make_window(qtbot)
    win._last_prompt = "old prompt"

    captured = {}

    class _Sig:
        def connect(self, _fn):
            pass

    class FakeABTestWorker:
        def __init__(self, prompt, iterations):
            captured["prompt"] = prompt
            captured["iterations"] = iterations
            self.progress = _Sig()
            self.error = _Sig()
            self.finished = _Sig()

        def isRunning(self):  # noqa: N802
            return False

        def start(self):
            pass

    server_mock = MagicMock()
    server_mock.is_running.return_value = True

    with patch("templatr.ui.main_window.get_llm_server", return_value=server_mock), patch(
        "templatr.ui.main_window.ABTestWorker", FakeABTestWorker
    ):
        win._handle_test_command("/test 4 | custom prompt text")

    assert captured["iterations"] == 4
    assert captured["prompt"] == "custom prompt text"


def test_test_command_inline_prompt_without_n(qtbot):
    """/test | prompt uses default 3 iterations (AC-1)."""
    win = _make_window(qtbot)
    win._last_prompt = "old"

    captured = {}

    class _Sig:
        def connect(self, _fn):
            pass

    class FakeABTestWorker:
        def __init__(self, prompt, iterations):
            captured["prompt"] = prompt
            captured["iterations"] = iterations
            self.progress = _Sig()
            self.error = _Sig()
            self.finished = _Sig()

        def isRunning(self):  # noqa: N802
            return False

        def start(self):
            pass

    server_mock = MagicMock()
    server_mock.is_running.return_value = True

    with patch("templatr.ui.main_window.get_llm_server", return_value=server_mock), patch(
        "templatr.ui.main_window.ABTestWorker", FakeABTestWorker
    ):
        win._handle_test_command("/test | inline prompt")

    assert captured["iterations"] == 3
    assert captured["prompt"] == "inline prompt"


def test_test_command_invalid_n_shows_error(qtbot):
    """Non-integer N argument shows error, returns handled=True."""
    win = _make_window(qtbot)
    win._last_prompt = "some prompt"

    handled = win._handle_test_command("/test abc")

    assert handled is True
    msgs = _last_system_messages(win)
    assert any("invalid" in m.lower() or "usage" in m.lower() for m in msgs)


# ---------------------------------------------------------------------------
# On-finish: summary rendering, history recording (AC-3, AC-6)
# ---------------------------------------------------------------------------


def test_test_finished_renders_summary(qtbot):
    """_on_ab_test_finished adds a summary message with per-run latency (AC-3)."""
    win = _make_window(qtbot)
    win.ab_test_worker = None
    win._last_test_results = None
    win._last_test_history_ids = None

    results = [
        {
            "iteration": 1,
            "output": "first output",
            "latency_seconds": 1.23,
            "prompt_tokens_est": 5,
            "output_tokens_est": 2,
        },
        {
            "iteration": 2,
            "output": "second output",
            "latency_seconds": 0.99,
            "prompt_tokens_est": 5,
            "output_tokens_est": 2,
        },
    ]

    win._on_ab_test_finished("test prompt", results)

    msgs = _last_system_messages(win, n=2)
    combined = " ".join(msgs)
    assert "1.23" in combined or "0.99" in combined
    assert "Iteration" in combined or "iteration" in combined


def test_test_finished_records_each_output_in_history(qtbot):
    """Each iteration output is saved to prompt history (AC-6)."""
    win = _make_window(qtbot)
    win.ab_test_worker = None
    win._last_test_results = None
    win._last_test_history_ids = None

    recorded = []
    win.prompt_history.add_entry = MagicMock(
        side_effect=lambda *a, **kw: recorded.append(a) or MagicMock(id="fake-id")
    )

    results = [
        {"iteration": 1, "output": "out1", "latency_seconds": 1.0,
         "prompt_tokens_est": 2, "output_tokens_est": 1},
        {"iteration": 2, "output": "out2", "latency_seconds": 1.1,
         "prompt_tokens_est": 2, "output_tokens_est": 1},
    ]
    win._on_ab_test_finished("my prompt", results)

    assert len(recorded) == 2


def test_test_finished_stores_results_for_view(qtbot):
    """_last_test_results is populated so /test view can open the dialog (AC-4)."""
    win = _make_window(qtbot)
    win.ab_test_worker = None
    win._last_test_results = None
    win._last_test_history_ids = None

    results = [
        {"iteration": 1, "output": "x", "latency_seconds": 0.5,
         "prompt_tokens_est": 1, "output_tokens_est": 1},
    ]
    win._on_ab_test_finished("prompt", results)

    assert win._last_test_results == results


# ---------------------------------------------------------------------------
# /test view: detail dialog (AC-4, AC-5)
# ---------------------------------------------------------------------------


def test_test_view_without_results_shows_message(qtbot):
    """/test view when no results exist shows a guidance message."""
    win = _make_window(qtbot)
    win._last_test_results = None

    handled = win._handle_test_command("/test view")

    assert handled is True
    msgs = _last_system_messages(win)
    assert any("no test results" in m.lower() or "run /test" in m.lower() for m in msgs)


def test_ab_test_results_dialog_shows_iterations(qtbot):
    """ABTestResultsDialog lists all iteration entries in the list widget (AC-4)."""
    from templatr.ui.ab_test_dialog import ABTestResultsDialog

    results = [
        {"iteration": 1, "output": "alpha output", "latency_seconds": 1.0,
         "prompt_tokens_est": 3, "output_tokens_est": 2},
        {"iteration": 2, "output": "beta output", "latency_seconds": 1.5,
         "prompt_tokens_est": 3, "output_tokens_est": 3},
    ]
    dlg = ABTestResultsDialog(results=results, history_ids=["id1", "id2"])
    qtbot.addWidget(dlg)
    dlg.show()

    assert dlg.list_widget.count() == 2
    assert "Iteration 1" in dlg.list_widget.item(0).text()
    assert "Iteration 2" in dlg.list_widget.item(1).text()


def test_ab_test_results_dialog_pick_winner_emits_signal(qtbot):
    """Clicking 'Pick as Winner' emits winner_selected with the entry index (AC-5)."""
    from templatr.ui.ab_test_dialog import ABTestResultsDialog

    results = [
        {"iteration": 1, "output": "first", "latency_seconds": 0.9,
         "prompt_tokens_est": 2, "output_tokens_est": 1},
        {"iteration": 2, "output": "second", "latency_seconds": 1.0,
         "prompt_tokens_est": 2, "output_tokens_est": 1},
    ]
    selected = []
    dlg = ABTestResultsDialog(results=results, history_ids=["a", "b"])
    qtbot.addWidget(dlg)
    dlg.winner_selected.connect(selected.append)
    dlg.show()

    # Select iteration 2 and click pick winner
    dlg.list_widget.setCurrentRow(1)
    dlg._pick_winner()

    assert selected == [1]  # index 1 → iteration 2


# ---------------------------------------------------------------------------
# Stop mechanism (AC-8)
# ---------------------------------------------------------------------------


def test_stop_generation_also_stops_ab_test_worker(qtbot):
    """_stop_generation cancels the ab_test_worker if it is running (AC-8)."""
    win = _make_window(qtbot)
    mock_worker = MagicMock()
    mock_worker.isRunning.return_value = True
    win.ab_test_worker = mock_worker

    with patch("templatr.ui.main_window.get_llm_server"):
        win._stop_generation()

    mock_worker.stop.assert_called_once()


# ---------------------------------------------------------------------------
# /help mentions /test (AC-9)
# ---------------------------------------------------------------------------


def test_help_includes_test_command(qtbot):
    """The /help output mentions the /test command (AC-9)."""
    win = _make_window(qtbot)
    win._on_system_command("help")

    from templatr.ui.message_bubble import MessageBubble

    bubbles = win.chat_widget.findChildren(MessageBubble)
    assert bubbles
    last = bubbles[-1].get_raw_text()
    assert "/test" in last
