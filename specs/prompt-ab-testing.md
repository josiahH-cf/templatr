# Feature: Prompt A/B Testing

## Description

Run the same prompt multiple times (against the same model or across models) and display the outputs side-by-side for comparison, scoring, and ranking. The existing `/compare` command compares *different models* on a single run each. This feature extends that with same-model variance analysis: run N iterations, view outputs together, star the best one, and optionally record the winner to history. This helps users evaluate prompt quality and model consistency.

## Acceptance Criteria

- [ ] AC-1: A `/test` slash command accepts an optional iteration count and model selector: `/test [N] [model]`. Default N is 3, default model is the currently loaded model.
- [ ] AC-2: The command runs the current prompt (or the last generated prompt if the input is just `/test`) N times sequentially against the target model, collecting each output.
- [ ] AC-3: While the test is running, a progress message updates in the status bar ("Running iteration 2/3…") and the input bar shows the generating state.
- [ ] AC-4: On completion, the results are displayed in the chat thread as a numbered list with output previews, latency per run, and estimated token counts — following the same summary format as `/compare`.
- [ ] AC-5: An `ABTestResultsDialog` opens automatically (or via a "View Details" link in the summary) showing all N outputs side-by-side in scrollable panes with a "Pick Winner" button for each.
- [ ] AC-6: Clicking "Pick Winner" marks that output as a favorite in `PromptHistoryStore` and closes the dialog. A system message confirms the selection.
- [ ] AC-7: All N outputs are recorded in `PromptHistoryStore` as individual entries (same prompt, different outputs), so they appear in history.
- [ ] AC-8: If the model is not running or N < 2, the command shows an appropriate error message in the chat thread.
- [ ] AC-9: The test run can be cancelled mid-flight via the stop button (same as generation cancel), stopping after the current iteration completes.
- [ ] AC-10: The `ABTestResultsDialog` is ≤ 300 lines.

## Affected Areas

### Source files modified
- `templatr/ui/main_window.py` — Add `_handle_test_command()` to parse `/test` syntax, wire to worker, handle results. Register `/test` in `_on_system_command`.
- `templatr/ui/slash_input.py` — Register `/test` in the command palette entries.
- `templatr/ui/workers.py` — Add `ABTestWorker(QThread)` that runs the same prompt N times, collecting output + latency + token estimates per iteration. Reuses the existing `LLMClient.generate()` call.

### New files
- `templatr/ui/ab_test_results.py` — `ABTestResultsDialog` (QDialog): side-by-side output panes, "Pick Winner" buttons, latency/token display. ≤ 300 lines.
- `tests/test_ab_testing.py` — Unit tests covering AC-1 through AC-10 with mocked LLM client.

### Test files requiring updates
- None expected — `/compare` tests are independent.

## Constraints

- Iterations run sequentially (not parallel) to avoid overloading the llama-server with concurrent requests.
- No new dependencies.
- The token count is estimated (word-split heuristic), same as `/compare` — not actual tokenizer output.
- The worker must respect the existing `_stopped` flag pattern for cancellation.
- The dialog reuses the project's dark/light theme stylesheet — no custom styling.

## Out of Scope

- Statistical analysis (mean, std dev, confidence intervals) across runs — future work.
- Automated quality scoring or LLM-as-judge evaluation.
- Running A/B tests across multiple models simultaneously (use `/compare` for that).
- Persisting A/B test sessions as a group (individual outputs go to history, but the grouping is ephemeral).
- Configurable temperature/parameter sweeps per iteration (future: parameter grid search).

## Dependencies

- `chat-ui-core` (complete) — Chat thread display.
- `slash-commands` (complete) — Command palette and `/` command infrastructure.
- `multi-model-comparison` (complete) — `MultiModelCompareWorker` pattern and result rendering format. The `ABTestWorker` follows the same structure.
- `prompt-history` (complete) — `PromptHistoryStore` for recording each iteration.

## Notes

- `/test` syntax examples:
  - `/test` — 3 iterations, current model, last prompt
  - `/test 5` — 5 iterations, current model, last prompt
  - `/test 3 mistral-7b` — 3 iterations, specific model, last prompt
  - The prompt is always the last generated prompt (same pattern as `/compare` without a `|` argument). If no prompt is available, the command errors with guidance.
- The `ABTestWorker` is simpler than `MultiModelCompareWorker` because it doesn't need to swap models between iterations. It just calls `client.generate()` N times and collects results.
- The results dialog uses a `QTabWidget` with one tab per iteration, each containing a read-only `QPlainTextEdit` showing the full output, plus a stats label (latency, tokens) and a "Pick Winner" button.
