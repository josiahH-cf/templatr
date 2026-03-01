# Feature: Model Performance Dashboard

## Description

Users generate many outputs over time but have no visibility into performance patterns — which models are fastest, which templates they use most, or how latency trends over time. The app already records prompt history, and the comparison/test flows collect timing data, but none of it is surfaced. This feature adds a read-only dashboard that aggregates existing history data into useful performance summaries.

## Acceptance Criteria

- [x] AC-1: History entries gain optional timing metadata (latency, estimated output tokens, model name). Existing history files without these fields continue to load without errors.
- [x] AC-2: The generation flow records timing and model metadata into history entries when available.
- [x] AC-3: A `/performance` slash command opens the performance dashboard.
- [x] AC-4: The dashboard displays summary statistics: total generations, average latency, estimated total tokens, and number of distinct models used.
- [x] AC-5: A per-model breakdown shows generation count, average latency, total estimated tokens, and last-used date for each model.
- [x] AC-6: A per-template breakdown shows generation count, average latency, and last-used date for each template.
- [x] AC-7: Both breakdowns are sortable by column.
- [x] AC-8: A date range filter (last 7 days / last 30 days / all time) controls which entries are included.
- [x] AC-9: If no entries have timing data, the dashboard shows an empty-state message with guidance.
- [x] AC-10: `/help` output is updated to document the `/performance` command.
- [x] AC-11: README is updated to describe the performance dashboard.

## Constraints

- No new dependencies. Use standard Qt table widgets — no charting library.
- Backward compatible: existing history files load cleanly with default values for new fields.
- Token counts are estimates and must be labeled as such.
- The dashboard is read-only — no editing or deleting from this view.
- Aggregation runs synchronously on open (small data set — capped by existing per-template limits).
- **UI principle:** The dashboard is accessed exclusively via `/performance` — no new menu items or toolbar buttons. It opens as a dialog, not a permanent panel. The chat interface remains the primary workspace.

## Out of Scope

- Charts or graphs (future: trend visualization).
- Exporting data to CSV or JSON.
- Real-time updating during generation (refresh on next open).
- Cost estimation (local models have no API pricing).
- Actual tokenizer-based token counting.

## Dependencies

- All v1.1 features (complete).
- Benefits from prompt-ab-testing landing first (richer timing data), but can land independently.

## Notes

- The history schema extension (adding optional fields to existing entries) must be done carefully for backward compatibility. The implementer should ensure old entries round-trip without data loss.
- Per-model breakdowns require knowing which model produced each entry. Currently entries don't track the model name — this needs to be added to the history schema.
- Date range filtering can use the existing `created_at` ISO timestamps in history entries.
