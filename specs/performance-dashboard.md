# Feature: Model Performance Dashboard

## Description

Add a dashboard dialog that surfaces generation performance metrics over time: latency per generation, estimated token throughput, model usage frequency, and per-template generation counts. The data source is the existing `PromptHistoryStore` (extended with timing metadata) plus the metrics already collected by `MultiModelCompareWorker` and the new `ABTestWorker`. The dashboard is read-only and requires no new persistence backend — it queries history entries on open.

## Acceptance Criteria

- [ ] AC-1: `PromptHistoryEntry` gains optional `latency_seconds` (float) and `output_tokens_est` (int) fields, defaulting to `None`/`0` for backward compatibility with existing history files.
- [ ] AC-2: `_record_generation_history()` in `MainWindow` passes latency and token estimates when available (generation worker already times the request; the elapsed time must be threaded through).
- [ ] AC-3: A "Performance…" action in the Help menu and a `/performance` slash command open the `PerformanceDashboardDialog`.
- [ ] AC-4: The dialog displays a **summary card row** at the top: total generations, average latency, estimated total tokens generated, and number of distinct models used.
- [ ] AC-5: A **per-model table** lists each model name with: generation count, average latency, total estimated tokens, and last-used date.
- [ ] AC-6: A **per-template table** lists each template with: generation count, average latency, and last-used date.
- [ ] AC-7: Both tables are sortable by clicking column headers.
- [ ] AC-8: A date range filter (last 7 days / last 30 days / all time) controls which entries are included in the summary and tables.
- [ ] AC-9: The dialog is ≤ 300 lines.
- [ ] AC-10: If the history store has no entries with timing data, the dashboard shows "No performance data yet. Generate some outputs to see metrics here."

## Affected Areas

### Source files modified
- `templatr/core/prompt_history.py` — Add `latency_seconds` and `output_tokens_est` optional fields to `PromptHistoryEntry`. Update `to_dict()` / `from_dict()` for backward-compatible serialization (skip `None` values on write, default on read).
- `templatr/ui/_generation.py` — Thread elapsed time from `GenerationWorker.finished` signal through to `_record_generation_history()`. The worker already uses `time.perf_counter()` internally but doesn't expose it; add a `generation_stats` signal or extend the `finished` signal payload.
- `templatr/ui/main_window.py` — Update `_record_generation_history()` to accept and pass timing data. Add "Performance…" menu action. Wire `/performance` command. Pass timing from compare results (already have `latency_seconds` in the result dict).
- `templatr/ui/slash_input.py` — Register `/performance` in the command palette.
- `templatr/ui/workers.py` — Extend `GenerationWorker.finished` signal to include `latency_seconds` and `output_tokens_est` alongside the output text (breaking change to signal signature, but all connections are internal).

### New files
- `templatr/ui/performance_dashboard.py` — `PerformanceDashboardDialog` (QDialog): summary cards, per-model `QTableWidget`, per-template `QTableWidget`, date range filter. ≤ 300 lines.
- `tests/test_performance_dashboard.py` — Unit tests covering AC-1 through AC-10 with prepopulated history stores.

### Test files requiring updates
- `tests/test_prompt_history.py` — Add tests for new optional fields in `PromptHistoryEntry` (round-trip serialization, backward compat with entries missing the fields).
- `tests/test_workers.py` — Update `GenerationWorker.finished` signal assertions if signature changes.

## Constraints

- No new dependencies. Tables use `QTableWidget`; no charting library.
- Backward compatible: existing `prompt_history.json` files without `latency_seconds` / `output_tokens_est` load cleanly with defaults.
- Token counts remain *estimates* (word-split heuristic). The dashboard labels them as "est." to set expectations.
- The dashboard is read-only — no editing or deleting history from this view.
- All data aggregation runs synchronously on dialog open (history files are small; < 200 entries per template × ~50 templates = ~10K entries max).

## Out of Scope

- Charts or graphs (future: add `matplotlib` or `pyqtgraph` for trend lines).
- Exporting performance data to CSV or JSON.
- Real-time updating while a generation is in progress (refresh on next open).
- Cost estimation (no API pricing; purely local models).
- Actual tokenizer-based token counting (would require a tokenizer dependency).

## Dependencies

- `prompt-history` (complete) — `PromptHistoryStore` is the data source.
- `multi-model-comparison` (complete) — Compare results already include `latency_seconds` and `output_tokens_est`.
- `prompt-ab-testing` (new) — A/B test results also include per-iteration timing. This spec can land independently but benefits from A/B testing being available.

## Notes

- The `GenerationWorker` currently emits `finished(str)`. Changing it to `finished(str, float, int)` (output, latency, tokens) is a clean approach but requires updating all connections. An alternative is a separate `generation_stats(float, int)` signal emitted just before `finished` — simpler but introduces ordering assumptions. The former is preferred for clarity.
- The per-model breakdown requires knowing which model produced each history entry. Currently `PromptHistoryEntry` does not record the model name. Options:
  1. Add an optional `model_name` field to `PromptHistoryEntry` (preferred — small schema addition).
  2. Infer from the config at generation time (fragile if the user switches models).
  The spec assumes option 1.
- Date range filtering uses the `created_at` ISO timestamp already stored in each entry — no new indexing needed.
