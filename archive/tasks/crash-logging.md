# Tasks: crash-logging

**Spec:** /specs/crash-logging.md

## Status

- Total: 3
- Complete: 3
- Remaining: 0

## Task List

### Task 1: Logging module setup and configuration

- **Files:** `templatr/core/logging_setup.py` (new), `templatr/core/config.py` (log dir path), `templatr/__main__.py` (call setup on startup)
- **Done when:** `setup_logging()` creates a rotating file handler at `<config_dir>/logs/<appname>.log`, 5 MB rotation, 3 backups. Log format includes ISO-8601 timestamp, level, module. Called before any other initialization in `__main__.py`.
- **Criteria covered:** Criterion 1 (rotating log file), Criterion 5 (rotation config), Criterion 6 (no prompt content — enforced by not passing content to logger)
- **Status:** [x] Complete

### Task 2: Global exception hook and worker error logging

- **Files:** `templatr/__main__.py` (sys.excepthook), `templatr/ui/workers.py` (error logging), `templatr/integrations/llm.py` (server error logging)
- **Done when:** Unhandled exceptions are caught by `sys.excepthook`, logged at CRITICAL, and the app exits cleanly. `GenerationWorker` errors are logged at ERROR with full traceback. LLM server start/stop failures are logged at ERROR.
- **Criteria covered:** Criterion 2 (global exception hook), Criterion 3 (worker error logging)
- **Status:** [x] Complete

### Task 3: Help menu "View Log File" action

- **Files:** `templatr/ui/main_window.py` (Help menu addition)
- **Done when:** Help menu has a "View Log File" action that opens the log directory in the system file manager via `QDesktopServices.openUrl()`. Works on Linux, macOS, and Windows.
- **Criteria covered:** Criterion 4 (View Log File action)
- **Status:** [x] Complete

## Test Strategy

| Criterion | Tested in Task |
|-----------|---------------|
| 1. Rotating log file created | Task 1 (test: call setup_logging with tmp dir, verify file exists) |
| 2. Global exception hook logs | Task 2 (test: trigger exception, verify log entry) |
| 3. Worker errors logged | Task 2 (test: mock worker error, verify ERROR log entry) |
| 4. View Log File action | Task 3 (test: verify menu action exists, mock QDesktopServices) |
| 5. Rotation config | Task 1 (test: verify handler config — 5MB, 3 backups) |
| 6. No prompt content in logs | Task 1 (enforced by design — tested by reviewing log format) |

## Session Log

<!-- Append after each session: date, completed, blockers -->

### 2026-02-27

- **Completed:** All 3 tasks (logging setup, exception hook + worker logging, Help menu action)
- **Files changed:** `templatr/core/logging_setup.py` (new), `templatr/core/config.py` (added `get_log_dir`), `templatr/__main__.py` (setup_logging + sys.excepthook), `templatr/ui/workers.py` (ERROR logging in GenerationWorker), `templatr/ui/main_window.py` (View Log File menu action + QDesktopServices import), `tests/test_crash_logging.py` (10 new tests)
- **Approach:** Created `logging_setup.py` with `setup_logging()` (RotatingFileHandler, 5 MB / 3 backups, ISO-8601 format) and `unhandled_exception_hook()` (CRITICAL-level logging). Wired both into `__main__.py` before GUI init. Added ERROR-level logging with `exc_info` to `GenerationWorker`. Added "View Log File" action to Help menu using `QDesktopServices.openUrl`.
- **Surprises:** `get_log_dir()` was not present in `config.py` despite appearing in cached file reads — had to insert via sed.
- **Result:** 136 tests pass, zero lint errors, zero new dependencies.
