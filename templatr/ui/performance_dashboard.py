"""Performance dashboard dialog and aggregation helpers.

Provides ``PerformanceDashboard`` (a ``QDialog``) and pure-function helpers
for computing summary stats, per-model breakdowns, per-template breakdowns,
and date-range filtering over prompt-history entries.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

# ---------------------------------------------------------------------------
# Pure helpers — usable without Qt for easy testing
# ---------------------------------------------------------------------------


def filter_entries_by_range(
    entries: list[dict],
    range_key: str,
    *,
    reference: str | None = None,
) -> list[dict]:
    """Filter history entry dicts by date range.

    Args:
        entries: List of history entry dicts (must have ``created_at``).
        range_key: One of ``"7days"``, ``"30days"``, or ``"all"``.
        reference: ISO timestamp used as "now" (defaults to actual UTC now).

    Returns:
        Filtered list of entry dicts.
    """
    if range_key == "all":
        return list(entries)

    if reference:
        ref_dt = datetime.fromisoformat(reference.replace("Z", "+00:00"))
    else:
        ref_dt = datetime.now(timezone.utc)

    if range_key == "7days":
        cutoff = ref_dt - timedelta(days=7)
    elif range_key == "30days":
        cutoff = ref_dt - timedelta(days=30)
    else:
        return list(entries)

    result: list[dict] = []
    for e in entries:
        ts = e.get("created_at", "")
        if not ts:
            continue
        try:
            entry_dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            continue
        if entry_dt >= cutoff:
            result.append(e)
    return result


def _entries_with_timing(entries: list[dict]) -> list[dict]:
    """Return only entries that have latency_seconds set."""
    return [e for e in entries if e.get("latency_seconds") is not None]


def compute_dashboard_stats(entries: list[dict]) -> dict:
    """Compute aggregated dashboard statistics from history entry dicts.

    Args:
        entries: List of history entry dicts. Entries may or may not have
            timing fields (``latency_seconds``, ``output_tokens_est``,
            ``model_name``).

    Returns:
        A dict with keys:
            ``total_generations`` (int),
            ``avg_latency`` (float | None),
            ``total_tokens_est`` (int),
            ``distinct_models`` (int),
            ``per_model`` (list[dict]),
            ``per_template`` (list[dict]),
            ``has_timing_data`` (bool).
    """
    timed = _entries_with_timing(entries)
    has_timing = len(timed) > 0

    total_generations = len(entries)
    avg_latency: Optional[float] = None
    if timed:
        avg_latency = sum(e["latency_seconds"] for e in timed) / len(timed)

    total_tokens_est = sum(e.get("output_tokens_est", 0) or 0 for e in entries)

    model_names = {e.get("model_name") for e in entries if e.get("model_name")}
    distinct_models = len(model_names)

    # Per-model breakdown
    model_buckets: dict[str, list[dict]] = {}
    for e in entries:
        mn = e.get("model_name")
        if mn:
            model_buckets.setdefault(mn, []).append(e)

    per_model: list[dict] = []
    for mn, bucket in sorted(model_buckets.items()):
        latencies = [e["latency_seconds"] for e in bucket if e.get("latency_seconds") is not None]
        avg_lat = sum(latencies) / len(latencies) if latencies else None
        tokens = sum(e.get("output_tokens_est", 0) or 0 for e in bucket)
        last_used = max(e.get("created_at", "") for e in bucket)
        per_model.append(
            {
                "model_name": mn,
                "count": len(bucket),
                "avg_latency": avg_lat,
                "total_tokens_est": tokens,
                "last_used": last_used,
            }
        )

    # Per-template breakdown
    template_buckets: dict[str, list[dict]] = {}
    for e in entries:
        tn = e.get("template_name", "__plain__")
        template_buckets.setdefault(tn, []).append(e)

    per_template: list[dict] = []
    for tn, bucket in sorted(template_buckets.items()):
        latencies = [e["latency_seconds"] for e in bucket if e.get("latency_seconds") is not None]
        avg_lat = sum(latencies) / len(latencies) if latencies else None
        last_used = max(e.get("created_at", "") for e in bucket)
        per_template.append(
            {
                "template_name": tn,
                "count": len(bucket),
                "avg_latency": avg_lat,
                "last_used": last_used,
            }
        )

    return {
        "total_generations": total_generations,
        "avg_latency": avg_latency,
        "total_tokens_est": total_tokens_est,
        "distinct_models": distinct_models,
        "per_model": per_model,
        "per_template": per_template,
        "has_timing_data": has_timing,
    }


# ---------------------------------------------------------------------------
# Qt dialog
# ---------------------------------------------------------------------------

_RANGE_OPTIONS = [
    ("Last 7 days", "7days"),
    ("Last 30 days", "30days"),
    ("All time", "all"),
]


class PerformanceDashboard(QDialog):
    """Read-only dashboard showing performance metrics from prompt history.

    Opened via the ``/performance`` slash command.

    Args:
        entries: List of history entry dicts (from ``PromptHistoryStore``).
        parent: Optional parent widget.
    """

    def __init__(self, entries: list[dict], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Performance Dashboard")
        self.resize(720, 520)

        self._all_entries = entries

        layout = QVBoxLayout(self)

        # -- Date range filter --
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Date range:"))
        self._range_combo = QComboBox()
        for label, _key in _RANGE_OPTIONS:
            self._range_combo.addItem(label, _key)
        self._range_combo.setCurrentIndex(2)  # default: all time
        self._range_combo.currentIndexChanged.connect(self._on_range_changed)
        filter_row.addWidget(self._range_combo)
        filter_row.addStretch()
        layout.addLayout(filter_row)

        # -- Empty-state label (always present, toggled by _refresh) --
        self.empty_label = QLabel(
            "No performance data yet.\n\n"
            "Generate some outputs and timing metadata will appear here."
        )
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setWordWrap(True)
        layout.addWidget(self.empty_label)

        # -- Summary row --
        self._summary_label = QLabel()
        self._summary_label.setWordWrap(True)
        layout.addWidget(self._summary_label)

        # -- Tabs for model / template breakdowns --
        self._tabs = QTabWidget()

        # Model table
        self.model_table = QTableWidget()
        self.model_table.setColumnCount(5)
        self.model_table.setHorizontalHeaderLabels(
            ["Model", "Generations", "Avg Latency (s)", "Est. Tokens", "Last Used"]
        )
        self.model_table.setSortingEnabled(True)
        self.model_table.horizontalHeader().setStretchLastSection(True)
        self.model_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._tabs.addTab(self.model_table, "By Model")

        # Template table
        self.template_table = QTableWidget()
        self.template_table.setColumnCount(4)
        self.template_table.setHorizontalHeaderLabels(
            ["Template", "Generations", "Avg Latency (s)", "Last Used"]
        )
        self.template_table.setSortingEnabled(True)
        self.template_table.horizontalHeader().setStretchLastSection(True)
        self.template_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._tabs.addTab(self.template_table, "By Template")

        layout.addWidget(self._tabs)

        # Initial population — use all-time by default
        self._refresh()

    # -- internal helpers --

    def _current_range_key(self) -> str:
        """Return the currently selected range key."""
        return self._range_combo.currentData() or "all"

    def _on_range_changed(self, _index: int) -> None:
        """Re-compute stats when the user changes the date-range filter."""
        self._refresh()

    def _refresh(self) -> None:
        """Filter entries by the selected range and repopulate all widgets."""
        range_key = self._current_range_key()
        filtered = filter_entries_by_range(self._all_entries, range_key)
        stats = compute_dashboard_stats(filtered)

        has_data = stats["has_timing_data"]
        self.empty_label.setVisible(not has_data)
        self._summary_label.setVisible(has_data)
        self._tabs.setVisible(has_data)

        if not has_data:
            return

        # Summary
        avg_str = f"{stats['avg_latency']:.2f}s" if stats["avg_latency"] is not None else "—"
        self._summary_label.setText(
            f"<b>Total generations:</b> {stats['total_generations']} &nbsp;|&nbsp; "
            f"<b>Avg latency:</b> {avg_str} &nbsp;|&nbsp; "
            f"<b>Est. total tokens:</b> {stats['total_tokens_est']} &nbsp;|&nbsp; "
            f"<b>Distinct models:</b> {stats['distinct_models']}"
        )

        # Model table
        self.model_table.setSortingEnabled(False)
        self.model_table.setRowCount(len(stats["per_model"]))
        for row, m in enumerate(stats["per_model"]):
            self.model_table.setItem(row, 0, QTableWidgetItem(m["model_name"]))

            count_item = QTableWidgetItem()
            count_item.setData(Qt.ItemDataRole.DisplayRole, m["count"])
            self.model_table.setItem(row, 1, count_item)

            lat_item = QTableWidgetItem()
            lat_val = f"{m['avg_latency']:.2f}" if m["avg_latency"] is not None else "—"
            lat_item.setData(Qt.ItemDataRole.DisplayRole, lat_val)
            self.model_table.setItem(row, 2, lat_item)

            tok_item = QTableWidgetItem()
            tok_item.setData(Qt.ItemDataRole.DisplayRole, m["total_tokens_est"])
            self.model_table.setItem(row, 3, tok_item)

            self.model_table.setItem(row, 4, QTableWidgetItem(m.get("last_used", "")))
        self.model_table.setSortingEnabled(True)

        # Template table
        self.template_table.setSortingEnabled(False)
        self.template_table.setRowCount(len(stats["per_template"]))
        for row, t in enumerate(stats["per_template"]):
            self.template_table.setItem(row, 0, QTableWidgetItem(t["template_name"]))

            count_item = QTableWidgetItem()
            count_item.setData(Qt.ItemDataRole.DisplayRole, t["count"])
            self.template_table.setItem(row, 1, count_item)

            lat_item = QTableWidgetItem()
            lat_val = f"{t['avg_latency']:.2f}" if t["avg_latency"] is not None else "—"
            lat_item.setData(Qt.ItemDataRole.DisplayRole, lat_val)
            self.template_table.setItem(row, 2, lat_item)

            self.template_table.setItem(row, 3, QTableWidgetItem(t.get("last_used", "")))
        self.template_table.setSortingEnabled(True)
