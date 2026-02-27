# Feature: Graceful Error Recovery & Model Validation

## Description

Make every LLM failure visible, actionable, and recoverable. Validate model files on import, show clear status in the UI, and ensure the app never silently drops a generation request. This reframes "models don't mess up, ever" into the achievable standard: "failures are obvious, recoverable, and logged."

## Acceptance Criteria

- [ ] Model files are validated on import by checking the GGUF magic bytes (`0x47475546`); invalid files are rejected with a user-facing message naming the file and the specific problem
- [ ] Generation errors display a human-readable message in the output pane (not a Python stack trace) with a "Retry" button that re-submits the last request
- [ ] Server health is polled every 10 seconds while running; the toolbar status label reflects actual server state (healthy / degraded / stopped) within one poll cycle
- [ ] If the server process dies unexpectedly, the UI detects this within 15 seconds and updates status to "Server stopped" with a prompt to restart
- [ ] Streaming generation failures retry up to 3 times with exponential backoff (1s, 2s, 4s) before surfacing a final error to the user
- [ ] When no model is loaded, the "Render with AI" button is disabled with a tooltip explaining why (e.g., "Start the LLM server and load a model first")

## Affected Areas

- `templatr/integrations/llm.py` — GGUF validation function, health polling timer, process-death detection
- `templatr/ui/workers.py` — human-readable error formatting, exponential backoff retry, retry signal
- `templatr/ui/output_pane.py` — error message display, "Retry" button
- `templatr/ui/llm_toolbar.py` — health status label, process-death handling, restart prompt
- `templatr/ui/variable_form.py` — "Render with AI" button disabled state + tooltip

## Constraints

- Health polling must not block the UI thread (use `QTimer` + worker or non-blocking HTTP)
- GGUF validation reads only the first 4 bytes — no full file parse or loading
- Retry backoff must be cancellable by the user (via existing Stop button)
- Error messages must not expose file system paths beyond the model filename

## Out of Scope

- Model quality assessment ("this model gives bad output")
- Automatic model download or recommendation
- Server auto-restart without user consent
- Output quality scoring or validation

## Dependencies

- Spec: `crash-logging` — errors should be logged in addition to being displayed in the UI

## Notes

- GGUF magic bytes: first 4 bytes of a valid GGUF file are `0x47 0x47 0x55 0x46` (ASCII "GGUF").
- The current `ModelCopyWorker` already handles file copy — add validation as a post-copy step.
- The health poller: a `QTimer` that fires every 10s, calls `/health` endpoint in a thread, emits a signal with the result. The toolbar subscribes to the signal.
- Human-readable error mapping: maintain a dict of common exception types → user-facing messages (e.g., `ConnectionRefusedError` → "The LLM server isn't running. Start it from the toolbar.").
