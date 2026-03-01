# Performance Dashboard

Track your generation activity with `/performance`.  The dashboard aggregates
timing, token, and model data from your prompt history into a read-only summary.

---

## What You See

| Section | Details |
|---------|---------|
| **Summary row** | Total generations, average latency, estimated total tokens, distinct models used. |
| **By Model** | Per-model breakdown: generation count, average latency, total estimated tokens, last used date. |
| **By Template** | Per-template breakdown: generation count, average latency, last used date. |

Both breakdowns are sortable by any column.

---

## Date Range Filter

Use the dropdown at the top of the dialog to narrow the view:

- **Last 7 days**
- **Last 30 days**
- **All time** (default)

---

## Notes

- Token counts are estimates (word-split heuristic) and are labeled as such.
- The dashboard is read-only — no editing or deleting from this view.
- New history entries gain timing metadata automatically; older entries without
  timing data are counted but excluded from latency/token aggregations.
