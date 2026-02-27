# Feature: Crash Logging & Diagnostics

## Description

Add structured local crash logging so that when the app fails, there's a log file users can reference or share. Currently, errors surface as raw exception text in the UI or disappear entirely. This replaces "hope the user screenshots the error" with "look in the log file." No network calls — all logging is local and privacy-respecting.

## Acceptance Criteria

- [ ] A rotating log file is written to `<config_dir>/logs/<appname>.log` with ISO-8601 timestamps, log level, and module source
- [ ] Unhandled exceptions are captured by a global `sys.excepthook` handler and written to the log at CRITICAL level before the app exits
- [ ] LLM generation errors (from workers) are logged at ERROR level with the full exception chain, not just the message string
- [ ] The Help menu includes a "View Log File" action that opens the log directory in the system file manager
- [ ] Log files rotate at 5 MB with 3 backup files retained (max ~20 MB disk usage)
- [ ] Log entries never include prompt content or model output (user privacy)

## Affected Areas

- `templatr/__main__.py` — global exception hook, logging initialization
- `templatr/core/` — new logging setup (could be a `logging_setup.py` or integrated into config)
- `templatr/ui/main_window.py` — Help menu action
- `templatr/ui/workers.py` — error-level logging in `GenerationWorker`
- `templatr/integrations/llm.py` — server start/stop/error logging

## Constraints

- No network calls — all logging is strictly local
- No prompt content or model output in logs (privacy-first)
- Must work on all 3 platforms (Linux, macOS, Windows path conventions)
- Use Python standard library `logging` + `RotatingFileHandler` — no new dependencies

## Out of Scope

- Remote telemetry or opt-in crash reporting to a server
- Log viewer UI within the app (just open the file manager)
- Log shipping to any external service
- Debug-level verbose logging toggle in the UI

## Dependencies

- Spec: `project-rename` — log directory name depends on final project name

## Notes

- Python's `logging` module with `RotatingFileHandler` handles all requirements natively.
- The global exception hook is `sys.excepthook`. Also consider hooking Qt's `qInstallMessageHandler()` for Qt-level warnings/errors.
- Log format: `%(asctime)s [%(levelname)s] %(name)s: %(message)s`
- The "View Log File" menu action: use `QDesktopServices.openUrl(QUrl.fromLocalFile(log_dir))` to open the directory cross-platform.
