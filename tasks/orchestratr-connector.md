# Tasks: orchestratr-connector

**Spec:** /specs/orchestratr-connector.md

## Status

- Total: 5
- Complete: 0
- Remaining: 5

## Task List

### Task 1: Connector module (`templatr/integrations/orchestratr.py`)

- **Files:** `templatr/integrations/orchestratr.py`, `templatr/__init__.py`
- **Done when:** Module exists with `generate_manifest()`, `manifest_needs_update()`, `get_status_json()`, `resolve_orchestratr_apps_dir()`; no side effects on import; version mismatch fixed
- **Criteria covered:** AC 4, 5, 6, 7, 8, 9, 12
- **Status:** [ ] Not started

### Task 2: CLI `status --json` subcommand

- **Files:** `templatr/__main__.py`
- **Done when:** `templatr status --json` outputs valid JSON with required fields, exit 0; `templatr` (no args) still launches GUI; `--doctor` still works
- **Criteria covered:** AC 1, 2, 3
- **Status:** [ ] Not started

### Task 3: Integrations settings dialog

- **Files:** `templatr/ui/integration_settings.py`
- **Done when:** Dialog shows orchestratr status (registered/not registered/stale), manifest path, chord, Register/Re-register button
- **Criteria covered:** AC 10
- **Status:** [ ] Not started

### Task 4: Main window integration (menu + startup hint)

- **Files:** `templatr/ui/main_window.py`
- **Done when:** File → Integrations menu item opens dialog; startup shows dismissible status bar hint when manifest stale
- **Criteria covered:** AC 10, 11
- **Status:** [ ] Not started

### Task 5: Tests

- **Files:** `tests/test_orchestratr_connector.py`, `tests/conftest.py`
- **Done when:** Tests cover manifest generation, flat schema validation, status JSON, CLI flag, path resolution (Linux, WSL2), GUI dialog (mock-based)
- **Criteria covered:** AC 13
- **Status:** [ ] Not started
