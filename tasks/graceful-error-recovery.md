# Tasks: graceful-error-recovery

**Spec:** /specs/graceful-error-recovery.md

## Status

- Total: 3
- Complete: 0
- Remaining: 3

## Task List

### Task 1: GGUF validation and model import error handling

- **Files:** `templatr/integrations/llm.py` (add `validate_gguf()` function, call from `import_model()`), `templatr/ui/llm_toolbar.py` (surface validation errors in a dialog)
- **Done when:** Importing a non-GGUF file (e.g., a random `.bin`) is rejected with a clear dialog: "Invalid model file: <filename> — expected GGUF format." Valid GGUF files import normally. Validation checks first 4 bytes for `0x47475546`.
- **Criteria covered:** Criterion 1 (GGUF validation)
- **Status:** [ ] Not started

### Task 2: Human-readable errors, retry button, and backoff

- **Files:** `templatr/ui/workers.py` (error formatting, exponential backoff), `templatr/ui/output_pane.py` (error display, "Retry" button)
- **Done when:** Generation errors show user-friendly messages (e.g., "LLM server isn't running. Start it from the toolbar." instead of `ConnectionRefusedError`). A "Retry" button re-submits the last request. Streaming failures retry 3× with 1s/2s/4s backoff before showing the error. Retry is cancellable via the Stop button.
- **Criteria covered:** Criterion 2 (human-readable errors + retry), Criterion 5 (exponential backoff)
- **Status:** [ ] Not started

### Task 3: Health polling, server death detection, and button states

- **Files:** `templatr/ui/llm_toolbar.py` (QTimer-based health poller, process-alive check, status label updates), `templatr/ui/variable_form.py` ("Render with AI" disabled state + tooltip)
- **Done when:** Toolbar polls `/health` every 10s while server is running; status shows "Healthy"/"Degraded"/"Stopped" within one cycle. If the server process dies, status updates within 15s. "Render with AI" is disabled when no model is loaded, with tooltip "Start the LLM server and load a model first."
- **Criteria covered:** Criterion 3 (health polling), Criterion 4 (death detection), Criterion 6 (button disabled state)
- **Status:** [ ] Not started

## Test Strategy

| Criterion | Tested in Task |
|-----------|---------------|
| 1. GGUF validation | Task 1 (test: valid GGUF bytes → pass; random bytes → reject with message) |
| 2. Human-readable errors + retry | Task 2 (test: mock errors → verify message text; click retry → verify re-submission) |
| 3. Health polling | Task 3 (test: mock /health responses → verify toolbar label updates) |
| 4. Server death detection | Task 3 (test: mock process.poll() returning exit code → verify status change) |
| 5. Exponential backoff | Task 2 (test: mock 3 consecutive failures → verify wait times 1s/2s/4s → then error shown) |
| 6. Button disabled state | Task 3 (test: no model loaded → verify button disabled and tooltip set) |

## Session Log

<!-- Append after each session: date, completed, blockers -->
