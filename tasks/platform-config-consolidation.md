# Tasks: platform-config-consolidation

**Spec:** /specs/platform-config-consolidation.md

## Status

- Total: 6
- Complete: 6
- Remaining: 0

## Task List

### Task 1: PlatformConfig dataclass and factory function

- **Files:** `templatr/core/config.py`, `tests/test_config.py`, new `tests/test_platform_config.py`
- **Done when:** A `PlatformConfig` dataclass exists with fields: `platform` (str), `config_dir` (Path), `data_dir` (Path), `models_dir` (Path), `binary_name` (str), `binary_search_paths` (list[Path]). A `get_platform_config()` factory is the single source of truth for all platform detection. `get_config_dir()` returns `%APPDATA%/templatr` on Windows. A new `get_data_dir()` returns `XDG_DATA_HOME/templatr` on Linux, `~/Library/Application Support/templatr` on macOS, `%LOCALAPPDATA%/templatr` on Windows. Existing `get_platform()` and `is_windows()` are either removed or become thin wrappers over `PlatformConfig`. Existing tests in `test_config.py` (L200–252) are updated to test `PlatformConfig` factory instead of raw `get_platform()`/`get_config_dir()`. New `test_platform_config.py` covers all platforms via mocked `platform.system()`.
- **Criteria covered:** Criteria 1, 2, 3, 4
- **Test updates required:** `tests/test_config.py` L200–209 (platform detection tests), L219–252 (migration tests); `tests/test_crash_logging.py` L26 (monkeypatch target); `tests/test_feedback.py` L27, L89 (patch target)
- **Status:** [x] Complete

### Task 2: Consume PlatformConfig in llm.py and fix error messages

- **Files:** `templatr/integrations/llm.py`, `templatr/ui/llm_toolbar.py`, `tests/test_cross_platform_packaging.py`, `tests/test_llm_server.py`
- **Done when:** `find_server_binary()` gets its data dir, binary name, and search paths from `PlatformConfig` — no more `os.name` checks or hardcoded paths (L272–315). `find_models()`/`get_models_dir()` use `PlatformConfig.models_dir` instead of hardcoded `~/models/` (L327, L339). All user-facing error messages (L449–453, L461–465) use `get_config_dir()` instead of hardcoded `~/.config/templatr`. `llm_toolbar.py` hint (L217) uses `get_platform_config().models_dir` instead of hardcoded `~/models/`.
- **Criteria covered:** Criteria 2, 4, 7
- **Test updates required:** `tests/test_cross_platform_packaging.py` L83–84, L108, L181 (hardcoded paths and `os.name` checks → `PlatformConfig` mocks); `tests/test_llm_server.py` L83, L105 (`os.name` binary name checks → `PlatformConfig` mocks)
- **Status:** [x] Complete

### Task 3: First-run template seeding in the app

- **Files:** `templatr/core/templates.py`, `templatr/core/config.py`, new `tests/test_template_seeding.py`
- **Done when:** On app launch, if the user's template dir is empty (no `.json` files), bundled templates from the package's `templates/` directory are copied into it. Works for pip install, PyInstaller binary, and install.sh installs. Never overwrites existing files. Idempotent — safe to run on every startup. `get_bundle_dir()` (config.py) correctly resolves to the package's `templates/` dir in all contexts (dev, installed, frozen).
- **Criteria covered:** Criteria 5, 6
- **Test updates required:** New `tests/test_template_seeding.py` — unit tests for empty dir seeding, non-empty dir skip, idempotency, frozen-app bundle resolution
- **Status:** [x] Complete

### Task 4: Fix install.sh and dedupe_templates.py

- **Files:** `install.sh`, `scripts/dedupe_templates.py`
- **Done when:** `install.sh` config.json creation block is removed (or font_size fixed to 13). The native Windows error message no longer references a non-existent PowerShell installer — it says "Use WSL2 or download the pre-built binary from GitHub Releases." `dedupe_templates.py` imports `get_config_dir()` and `get_templates_dir()` from `templatr.core.config` instead of reimplementing path logic.
- **Criteria covered:** Criteria 8, 9, 10
- **Status:** [x] Complete

### Task 5: `templatr --doctor` CLI command

- **Files:** `templatr/__main__.py`, new `tests/test_doctor.py`
- **Done when:** `templatr --doctor` prints a diagnostic report: platform detected, config dir, data dir, templates found (count), model files found (count + paths), llama-server binary found (path or "not found" with install guidance). Each missing item includes actionable next-step guidance. Exits 0 if all checks pass, 1 if any critical item is missing.
- **Criteria covered:** Criterion 11
- **Test updates required:** New `tests/test_doctor.py` — unit tests with mocked environment verifying output sections and exit codes
- **Status:** [x] Complete

### Task 6: Post-landing doc cleanup

- **Files:** `specs/documentation-overhaul.md`, `tasks/documentation-overhaul.md`, `README.md`
- **Done when:** All resolved audit caveats are removed or annotated in `specs/documentation-overhaul.md` (audit findings table, criteria 2/3/5 workaround language, out-of-scope section). `tasks/documentation-overhaul.md` "Caveats from audit" sections in Tasks 1 and 2 are updated to reflect fixed state. `README.md` "Where Files Are Stored" section adds Windows paths and updates removal commands to reference `templatr --doctor`. `decisions/0002-project-name.md` optionally annotated with note that paths are now platform-aware.
- **Criteria covered:** N/A (documentation maintenance)
- **Status:** [x] Complete

## Test Strategy

| Criterion | Tested in Task |
|-----------|---------------|
| 1. PlatformConfig dataclass | Task 1 (unit: construct PlatformConfig for each platform, verify fields) |
| 2. Single factory function | Task 1 + Task 2 (unit: mock platform.system, verify only get_platform_config calls it) |
| 3. Windows get_config_dir → %APPDATA% | Task 1 (unit: mock Windows platform, verify APPDATA path) |
| 4. get_data_dir respects XDG_DATA_HOME | Task 1 (unit: set env var, verify path) |
| 5. Template seeding on empty dir | Task 3 (unit: empty temp dir, verify templates copied) |
| 6. Seeding never overwrites | Task 3 (unit: pre-existing file, verify not replaced) |
| 7. Error messages use canonical paths | Task 2 (unit: mock macOS, verify error string contains ~/Library) |
| 8. dedupe_templates uses config module | Task 4 (unit: import check, no os.uname in file) |
| 9. install.sh config.json removed/fixed | Task 4 (manual: verify install.sh diff) |
| 10. install.sh no phantom PowerShell ref | Task 4 (grep: verify "PowerShell" not in install.sh) |
| 11. --doctor command | Task 5 (unit: run with mocked env, verify output sections) |

### Existing tests requiring updates

| Test File | Risk | What to verify after each task |
|-----------|------|-------------------------------|
| `tests/test_config.py` | HIGH | Task 1: platform detection tests (L200–209) and migration tests (L219–252) pass with PlatformConfig |
| `tests/test_cross_platform_packaging.py` | HIGH | Task 2: hardcoded path expectations (L83, L108, L181) updated to use PlatformConfig mocks |
| `tests/test_llm_server.py` | HIGH | Task 2: binary name checks (L83, L105) updated to use PlatformConfig mocks |
| `tests/test_crash_logging.py` | MEDIUM | Task 1: monkeypatch target (L26) still resolves correctly |
| `tests/test_feedback.py` | MEDIUM | Task 1: patch targets (L27, L89) still resolve correctly |

## Session Log

<!-- Append after each session: date, completed, blockers -->
