# Feature: Prompt A/B Testing

## Description

Users currently have no way to evaluate how *consistent* a model's output is for a given prompt. Running the same prompt once tells you what the model *can* produce, but not whether it produces it reliably. This feature lets users run a prompt multiple times, view all outputs together, and pick the best one — giving them a practical tool for evaluating prompt quality and model reliability before committing to a template.

## Acceptance Criteria

- [ ] AC-1: A `/test` slash command runs the current prompt (or the last generated prompt) multiple times against the active model. It accepts an optional iteration count (default: 3) and optional model name.
- [ ] AC-2: Iterations run sequentially, not in parallel. A progress indicator shows which iteration is running.
- [ ] AC-3: On completion, results appear in the chat thread as a summary with output previews, latency per iteration, and estimated token counts.
- [ ] AC-4: The user can open a detail view showing all outputs in full, with the ability to pick a winner.
- [ ] AC-5: Picking a winner marks that output as a favorite in history. A system message confirms the selection.
- [ ] AC-6: All iteration outputs are individually recorded in history (same prompt, different outputs).
- [ ] AC-7: Appropriate errors are shown when no model is running, no prompt is available, or N < 2.
- [ ] AC-8: The test run is cancellable via the existing stop mechanism.
- [ ] AC-9: `/help` output is updated to document the `/test` command.
- [ ] AC-10: README is updated to describe the A/B testing workflow.

## Constraints

- No new dependencies.
- Sequential execution only — llama-server handles one request at a time.
- Token counts are estimates (word-split heuristic, same approach used elsewhere in the app).
- Must respect the existing cancellation and generating-state patterns.
- **UI principle:** The `/test` command is the only entry point — no new menu items, buttons, or toolbar additions. The detail/results view opens on demand (not automatically), keeping the default chat flow uncluttered.

## Out of Scope

- Statistical analysis (mean, std dev, confidence intervals) — future work.
- Automated quality scoring or LLM-as-judge evaluation.
- Running A/B tests across multiple models simultaneously (use `/compare` for that).
- Persisting test sessions as a group (individual outputs go to history; grouping is ephemeral).
- Temperature or parameter sweeps per iteration (future: parameter grid search).

## Dependencies

- All v1.1 features (complete).

## Notes

- This feature follows the same pattern as `/compare` — a slash command triggers a background worker, results render in the chat thread. Implementers should study the existing compare flow for conventions.
- The detail view should reuse the app's existing theme and dialog patterns.
