# Task: Prompt A/B Testing (`/test`)

Spec: [specs/prompt-ab-testing.md](../specs/prompt-ab-testing.md)

## Goal

Add a `/test` slash command that runs the current prompt N times against the
active model, displays a summary in the chat thread, and lets the user open a
detail view to compare all outputs and pick a winner.

## Tasks

- [x] 1. Write tests (`tests/test_ab_testing.py`) — all 15 scenarios covering
       AC-1 through AC-10.
- [x] 2. Add `ABTestWorker` to `templatr/ui/workers.py` — sequential iterations,
       progress signal `(current, total)`, `stop()` support.
- [x] 3. Add `/test` entry to `SYSTEM_COMMANDS` in `templatr/ui/slash_input.py`.
- [x] 4. Create `templatr/ui/ab_test_dialog.py` — `ABTestResultsDialog` with output
       list, full-text pane, and "Pick as Winner" per iteration.
- [x] 5. Implement `_handle_test_command`, `_on_ab_test_progress`,
       `_on_ab_test_finished`, `_on_ab_test_error`, `_open_ab_test_detail`,
       `_render_ab_test_summary` in `templatr/ui/main_window.py`.
- [x] 6. Extend `_stop_generation` override in `main_window.py` to also cancel
       `ab_test_worker`, and route `/test` through `_handle_plain_input`.
- [x] 7. Update `/help` text to include `/test`.

## Parsing Rules

```
/test                   → 3 iterations, last prompt
/test 5                 → 5 iterations, last prompt
/test 5 | my prompt     → 5 iterations, custom prompt
/test | my prompt       → 3 iterations, custom prompt
/test view              → open detail dialog (if results available)
```

Error cases: N < 2, server not running, no prompt available.

## Progress

All tasks complete. See `tests/test_ab_testing.py` for acceptance test coverage.
