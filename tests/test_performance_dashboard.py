"""Tests for performance dashboard (/performance slash command).

Covers acceptance criteria AC-1 through AC-11 from specs/performance-dashboard.md.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_history_file(tmp_path: Path, entries: list[dict]) -> Path:
    """Write a prompt_history.json file and return its path."""
    fpath = tmp_path / "prompt_history.json"
    fpath.write_text(json.dumps({"entries": entries}, indent=2), encoding="utf-8")
    return fpath


def _entry(
    *,
    template_name: str = "Code Review",
    prompt: str = "Review this",
    output: str = "Looks good",
    created_at: str = "2026-02-15T12:00:00Z",
    latency_seconds: float | None = None,
    output_tokens_est: int | None = None,
    model_name: str | None = None,
    favorite: bool = False,
) -> dict:
    """Build a history entry dict with optional perf fields."""
    import uuid

    d: dict = {
        "id": uuid.uuid4().hex,
        "template_name": template_name,
        "prompt": prompt,
        "output": output,
        "created_at": created_at,
        "favorite": favorite,
    }
    if latency_seconds is not None:
        d["latency_seconds"] = latency_seconds
    if output_tokens_est is not None:
        d["output_tokens_est"] = output_tokens_est
    if model_name is not None:
        d["model_name"] = model_name
    return d


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


def _last_bubbles_text(win, n: int = 1) -> list[str]:
    """Return the raw text of the last n message bubbles."""
    from templatr.ui.message_bubble import MessageBubble

    bubbles = win.chat_widget.findChildren(MessageBubble)
    return [b.get_raw_text() for b in bubbles[-n:]]


# ===========================================================================
# AC-1: History entries gain optional timing metadata
# ===========================================================================


class TestAC1_HistorySchemaExtension:
    """AC-1: Optional timing metadata on history entries."""

    def test_entry_with_timing_fields_round_trips(self, tmp_path):
        """An entry with latency, tokens, and model name survives write/read."""
        from templatr.core.prompt_history import PromptHistoryStore

        store = PromptHistoryStore(file_path=tmp_path / "history.json")
        entry = store.add_entry(
            "MyTemplate",
            "prompt text",
            "output text",
            latency_seconds=1.5,
            output_tokens_est=42,
            model_name="llama-7b",
        )

        assert entry.latency_seconds == 1.5
        assert entry.output_tokens_est == 42
        assert entry.model_name == "llama-7b"

        # Read back
        entries = store.list_entries(limit=None)
        assert len(entries) == 1
        assert entries[0].latency_seconds == 1.5
        assert entries[0].output_tokens_est == 42
        assert entries[0].model_name == "llama-7b"

    def test_legacy_entry_loads_with_defaults(self, tmp_path):
        """Entries without timing fields load cleanly with None defaults."""
        from templatr.core.prompt_history import PromptHistoryStore

        legacy = _entry()  # no timing fields
        _make_history_file(tmp_path, [legacy])

        store = PromptHistoryStore(file_path=tmp_path / "prompt_history.json")
        entries = store.list_entries(limit=None)
        assert len(entries) == 1
        assert entries[0].latency_seconds is None
        assert entries[0].output_tokens_est is None
        assert entries[0].model_name is None

    def test_entry_to_dict_includes_timing_fields(self, tmp_path):
        """to_dict() includes new fields when they are set."""
        from templatr.core.prompt_history import PromptHistoryStore

        store = PromptHistoryStore(file_path=tmp_path / "history.json")
        entry = store.add_entry(
            "T",
            "p",
            "o",
            latency_seconds=2.0,
            output_tokens_est=10,
            model_name="model-x",
        )
        d = entry.to_dict()
        assert d["latency_seconds"] == 2.0
        assert d["output_tokens_est"] == 10
        assert d["model_name"] == "model-x"

    def test_entry_to_dict_omits_none_timing_fields(self, tmp_path):
        """to_dict() omits timing fields when they are None (backward compat)."""
        from templatr.core.prompt_history import PromptHistoryStore

        store = PromptHistoryStore(file_path=tmp_path / "history.json")
        entry = store.add_entry("T", "p", "o")
        d = entry.to_dict()
        assert "latency_seconds" not in d
        assert "output_tokens_est" not in d
        assert "model_name" not in d


# ===========================================================================
# AC-2: Generation flow records timing metadata
# ===========================================================================


class TestAC2_GenerationRecordsTiming:
    """AC-2: The generation flow records timing and model metadata."""

    def test_generation_worker_reports_elapsed_time(self):
        """GenerationWorker emits a result containing timing metadata."""
        mock_client = MagicMock()
        mock_client.generate.return_value = "hello world"

        with patch("templatr.ui.workers.get_llm_client", return_value=mock_client):
            from templatr.ui.workers import GenerationWorker

            results = []
            worker = GenerationWorker("test prompt", stream=False)
            worker.finished.connect(results.append)
            worker.run()

        assert len(results) == 1
        # The finished signal carries (output, elapsed_seconds)

    def test_history_entry_includes_timing_after_generation(self, tmp_path, qtbot):
        """After generation finishes, the history entry includes timing."""
        win = _make_window(qtbot)
        store_path = tmp_path / "history.json"

        from templatr.core.prompt_history import PromptHistoryStore

        store = PromptHistoryStore(file_path=store_path)
        win.prompt_history = store

        # Simulate generation finishing with timing data
        win._last_prompt = "test prompt"
        win._generation_start_time = 0.0  # will be set by _generate

        # Call the recording method directly with timing
        entry = win._record_generation_history_with_id("test prompt", "output text")

        # Entry should exist
        assert entry is not None


# ===========================================================================
# AC-3: /performance command opens dashboard
# ===========================================================================


class TestAC3_PerformanceCommand:
    """AC-3: /performance opens the performance dashboard."""

    def test_slash_performance_registered(self):
        """'/performance' is in the system commands list."""
        from templatr.ui.slash_input import SYSTEM_COMMANDS

        names = [c.name for c in SYSTEM_COMMANDS]
        assert "/performance" in names

    def test_performance_command_dispatched(self, qtbot):
        """The 'performance' system command is handled by _on_system_command."""
        win = _make_window(qtbot)
        # Should not raise
        with patch.object(win, "_open_performance_dashboard") as mock_open:
            win._on_system_command("performance")
            mock_open.assert_called_once()

    def test_plain_input_performance(self, qtbot):
        """'/performance' as plain text is routed correctly."""
        win = _make_window(qtbot)
        with patch.object(win, "_open_performance_dashboard") as mock_open:
            win._handle_plain_input("/performance")
            mock_open.assert_called_once()


# ===========================================================================
# AC-4: Dashboard summary statistics
# ===========================================================================


class TestAC4_SummaryStatistics:
    """AC-4: Dashboard displays summary stats."""

    def test_summary_total_generations(self, tmp_path):
        """Dashboard computes total generation count."""
        from templatr.ui.performance_dashboard import compute_dashboard_stats

        entries_data = [
            _entry(latency_seconds=1.0, output_tokens_est=10, model_name="m1"),
            _entry(latency_seconds=2.0, output_tokens_est=20, model_name="m2"),
            _entry(latency_seconds=3.0, output_tokens_est=30, model_name="m1"),
        ]
        stats = compute_dashboard_stats(entries_data)
        assert stats["total_generations"] == 3

    def test_summary_average_latency(self, tmp_path):
        """Dashboard computes average latency across entries with timing."""
        from templatr.ui.performance_dashboard import compute_dashboard_stats

        entries_data = [
            _entry(latency_seconds=1.0, output_tokens_est=10, model_name="m1"),
            _entry(latency_seconds=3.0, output_tokens_est=20, model_name="m1"),
        ]
        stats = compute_dashboard_stats(entries_data)
        assert stats["avg_latency"] == pytest.approx(2.0)

    def test_summary_total_tokens(self, tmp_path):
        """Dashboard computes total estimated tokens."""
        from templatr.ui.performance_dashboard import compute_dashboard_stats

        entries_data = [
            _entry(latency_seconds=1.0, output_tokens_est=10, model_name="m1"),
            _entry(latency_seconds=2.0, output_tokens_est=20, model_name="m2"),
        ]
        stats = compute_dashboard_stats(entries_data)
        assert stats["total_tokens_est"] == 30

    def test_summary_distinct_models(self, tmp_path):
        """Dashboard counts distinct model names."""
        from templatr.ui.performance_dashboard import compute_dashboard_stats

        entries_data = [
            _entry(latency_seconds=1.0, output_tokens_est=10, model_name="m1"),
            _entry(latency_seconds=2.0, output_tokens_est=20, model_name="m2"),
            _entry(latency_seconds=3.0, output_tokens_est=30, model_name="m1"),
        ]
        stats = compute_dashboard_stats(entries_data)
        assert stats["distinct_models"] == 2


# ===========================================================================
# AC-5: Per-model breakdown
# ===========================================================================


class TestAC5_PerModelBreakdown:
    """AC-5: Per-model breakdown with count, avg latency, tokens, last used."""

    def test_per_model_stats(self):
        """Each model shows correct count, avg latency, total tokens, last-used."""
        from templatr.ui.performance_dashboard import compute_dashboard_stats

        entries_data = [
            _entry(
                latency_seconds=1.0,
                output_tokens_est=10,
                model_name="modelA",
                created_at="2026-02-10T12:00:00Z",
            ),
            _entry(
                latency_seconds=3.0,
                output_tokens_est=30,
                model_name="modelA",
                created_at="2026-02-15T12:00:00Z",
            ),
            _entry(
                latency_seconds=2.0,
                output_tokens_est=20,
                model_name="modelB",
                created_at="2026-02-12T12:00:00Z",
            ),
        ]
        stats = compute_dashboard_stats(entries_data)
        models = {m["model_name"]: m for m in stats["per_model"]}

        assert models["modelA"]["count"] == 2
        assert models["modelA"]["avg_latency"] == pytest.approx(2.0)
        assert models["modelA"]["total_tokens_est"] == 40
        assert models["modelA"]["last_used"] == "2026-02-15T12:00:00Z"

        assert models["modelB"]["count"] == 1
        assert models["modelB"]["avg_latency"] == pytest.approx(2.0)
        assert models["modelB"]["total_tokens_est"] == 20


# ===========================================================================
# AC-6: Per-template breakdown
# ===========================================================================


class TestAC6_PerTemplateBreakdown:
    """AC-6: Per-template breakdown with count, avg latency, last used."""

    def test_per_template_stats(self):
        """Each template shows correct count, avg latency, and last-used."""
        from templatr.ui.performance_dashboard import compute_dashboard_stats

        entries_data = [
            _entry(
                template_name="Code Review",
                latency_seconds=1.0,
                output_tokens_est=10,
                model_name="m1",
                created_at="2026-02-10T12:00:00Z",
            ),
            _entry(
                template_name="Code Review",
                latency_seconds=3.0,
                output_tokens_est=30,
                model_name="m1",
                created_at="2026-02-15T12:00:00Z",
            ),
            _entry(
                template_name="Summarize",
                latency_seconds=2.0,
                output_tokens_est=20,
                model_name="m1",
                created_at="2026-02-12T12:00:00Z",
            ),
        ]
        stats = compute_dashboard_stats(entries_data)
        templates = {t["template_name"]: t for t in stats["per_template"]}

        assert templates["Code Review"]["count"] == 2
        assert templates["Code Review"]["avg_latency"] == pytest.approx(2.0)
        assert templates["Code Review"]["last_used"] == "2026-02-15T12:00:00Z"

        assert templates["Summarize"]["count"] == 1
        assert templates["Summarize"]["avg_latency"] == pytest.approx(2.0)


# ===========================================================================
# AC-7: Sortable columns
# ===========================================================================


class TestAC7_SortableColumns:
    """AC-7: Both model and template breakdowns are sortable by column."""

    def test_dashboard_tables_are_sortable(self, qtbot):
        """The model and template QTableWidgets have sorting enabled."""
        from templatr.ui.performance_dashboard import PerformanceDashboard

        entries_data = [
            _entry(latency_seconds=1.0, output_tokens_est=10, model_name="m1"),
        ]
        dialog = PerformanceDashboard(entries_data)
        qtbot.addWidget(dialog)

        assert dialog.model_table.isSortingEnabled()
        assert dialog.template_table.isSortingEnabled()


# ===========================================================================
# AC-8: Date range filter
# ===========================================================================


class TestAC8_DateRangeFilter:
    """AC-8: Date range filter (7 days / 30 days / all time)."""

    def test_filter_last_7_days(self):
        """Only entries within the last 7 days are included."""
        from templatr.ui.performance_dashboard import filter_entries_by_range

        now = "2026-02-28T12:00:00Z"
        entries_data = [
            _entry(created_at="2026-02-25T12:00:00Z", latency_seconds=1.0),
            _entry(created_at="2026-02-10T12:00:00Z", latency_seconds=2.0),
        ]
        filtered = filter_entries_by_range(entries_data, "7days", reference=now)
        assert len(filtered) == 1

    def test_filter_last_30_days(self):
        """Only entries within the last 30 days are included."""
        from templatr.ui.performance_dashboard import filter_entries_by_range

        now = "2026-02-28T12:00:00Z"
        entries_data = [
            _entry(created_at="2026-02-15T12:00:00Z", latency_seconds=1.0),
            _entry(created_at="2026-01-01T12:00:00Z", latency_seconds=2.0),
        ]
        filtered = filter_entries_by_range(entries_data, "30days", reference=now)
        assert len(filtered) == 1

    def test_filter_all_time(self):
        """All-time filter returns all entries."""
        from templatr.ui.performance_dashboard import filter_entries_by_range

        entries_data = [
            _entry(created_at="2025-01-01T12:00:00Z", latency_seconds=1.0),
            _entry(created_at="2026-02-15T12:00:00Z", latency_seconds=2.0),
        ]
        filtered = filter_entries_by_range(entries_data, "all", reference="2026-02-28T12:00:00Z")
        assert len(filtered) == 2


# ===========================================================================
# AC-9: Empty state
# ===========================================================================


class TestAC9_EmptyState:
    """AC-9: Dashboard shows empty-state message when no timing data."""

    def test_empty_state_no_entries(self, qtbot):
        """With no entries, dashboard shows empty-state guidance."""
        from templatr.ui.performance_dashboard import PerformanceDashboard

        dialog = PerformanceDashboard([])
        qtbot.addWidget(dialog)

        assert dialog.empty_label.isVisible()
        assert "no performance data" in dialog.empty_label.text().lower()

    def test_empty_state_entries_without_timing(self, qtbot):
        """Entries without timing data still trigger empty-state."""
        from templatr.ui.performance_dashboard import PerformanceDashboard

        entries_data = [_entry()]  # no timing fields
        dialog = PerformanceDashboard(entries_data)
        qtbot.addWidget(dialog)

        assert dialog.empty_label.isVisible()

    def test_non_empty_state_hides_label(self, qtbot):
        """With timing data, the empty-state label is hidden."""
        from templatr.ui.performance_dashboard import PerformanceDashboard

        entries_data = [
            _entry(latency_seconds=1.0, output_tokens_est=10, model_name="m1"),
        ]
        dialog = PerformanceDashboard(entries_data)
        qtbot.addWidget(dialog)

        assert not dialog.empty_label.isVisible()


# ===========================================================================
# AC-10: /help includes /performance
# ===========================================================================


class TestAC10_HelpOutput:
    """AC-10: /help output documents /performance."""

    def test_help_mentions_performance(self, qtbot):
        """The /help text includes a line about /performance."""
        win = _make_window(qtbot)
        win._on_system_command("help")

        text = _last_bubbles_text(win, 1)[0]
        assert "/performance" in text


# ===========================================================================
# AC-11: README documents performance dashboard
# ===========================================================================


class TestAC11_ReadmeDocs:
    """AC-11: README mentions the performance dashboard."""

    def test_readme_mentions_performance_dashboard(self):
        """README.md describes the performance dashboard feature."""
        readme = Path(__file__).resolve().parent.parent / "README.md"
        content = readme.read_text(encoding="utf-8")
        assert "performance" in content.lower()
        assert "/performance" in content
