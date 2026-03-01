# Spec: History Browser Panel

## Summary

Add a dedicated `QDialog` for browsing, filtering, and re-using previously generated prompt outputs. The existing `PromptHistoryStore` backend and inline `/history` command are preserved; this adds a proper panel.

## Acceptance Criteria

1. A "View History…" action in the Help menu and `Ctrl+H` shortcut opens the `HistoryBrowserDialog`.
2. The dialog loads all entries from `PromptHistoryStore` and displays them in reverse-chronological order.
3. A search field filters entries in real-time by matching prompt or output text (case-insensitive).
4. A template dropdown filters entries to a single template (or "All Templates").
5. A "Favorites only" checkbox restricts the list to favorited entries.
6. Selecting an entry shows its full output in a read-only detail pane.
7. A "Copy Output" button copies the selected entry's output to the system clipboard.
8. A "Favorite" / "Unfavorite" button toggles the selected entry's favorite state via `store.mark_favorite()`.
9. A "Re-use" button emits an `output_reused(str)` signal carrying the selected entry's output text.
10. The `output_reused` signal is connected in `MainWindow` to insert the text into the chat input.
11. An empty store shows a placeholder message ("No history yet").
12. The dialog is ≤ 300 lines.

## Non-Goals

- Deleting individual history entries (future work).
- Inline replacement of the `/history` chat command.
- Pagination or virtual scrolling (≤200 entries per template is small enough).

## Dependencies

- `templatr.core.prompt_history.PromptHistoryStore` (complete)
- `templatr.ui.main_window.MainWindow` (wiring only)
