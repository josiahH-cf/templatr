# Feature: Platform Config Consolidation

## Description

Consolidate all platform detection, path computation, and first-run bootstrapping into a single source of truth. A cross-platform architecture audit (2026-02-28) found 6 independent platform detection paths, 3 duplicate config-dir implementations, missing data-dir abstraction, and template seeding that only runs inside the bash installer. This spec fixes the engineering debt so that every install path (pip, installer, pre-built binary) produces a working app.

## Acceptance Criteria

- [ ] A single `PlatformConfig` dataclass (or equivalent) in `templatr/core/config.py` holds all platform-derived values: platform name, config dir, data dir, models dir, binary name, and binary search paths
- [ ] A single factory function (`get_platform_config()`) is the only code that calls `platform.system()`, `os.name`, or reads `/proc/version` — all other modules consume the dataclass
- [ ] `get_config_dir()` returns `%APPDATA%/templatr` on native Windows (not XDG `~/.config`)
- [ ] A new `get_data_dir()` function exists and respects `XDG_DATA_HOME` on Linux; `find_server_binary()` calls it instead of hardcoding paths
- [ ] Template seeding runs on first app launch: if the user's template dir is empty, bundled templates are copied from the package's `templates/` directory (works for pip install, PyInstaller binary, and install.sh)
- [ ] First-run seeding never overwrites existing user templates
- [ ] All user-facing error messages use the canonical path functions — no hardcoded `~/.config/templatr` strings
- [ ] `scripts/dedupe_templates.py` imports from `templatr.core.config` instead of reimplementing path logic
- [ ] `install.sh` config.json creation is removed (the app handles missing config.json with correct defaults) or the hardcoded `font_size: 11` is fixed to match the Python default of `13`
- [ ] `install.sh` native Windows message no longer references a non-existent PowerShell installer
- [ ] A `templatr --doctor` CLI command reports: platform detected, config dir, data dir, templates found, model files found, llama-server binary found — with actionable guidance for each missing item

## Affected Areas

### Source files modified
- `templatr/core/config.py` — new `PlatformConfig` dataclass, `get_platform_config()` factory, `get_data_dir()`, fix `get_config_dir()` Windows path
- `templatr/core/templates.py` — add first-run seed logic in `TemplateManager.__init__` or startup path
- `templatr/integrations/llm.py` — consume `PlatformConfig` in `find_server_binary()`, `find_models()`, `get_models_dir()`, `start()` error messages
- `templatr/__main__.py` — add `--doctor` CLI command
- `scripts/dedupe_templates.py` — replace local path logic with `templatr.core.config` imports
- `install.sh` — remove/fix config.json creation (L270–288), fix Windows message (L75–76)
- `templatr/ui/llm_toolbar.py` — replace hardcoded `~/models/` hint (L217) with `PlatformConfig.models_dir`

### Test files requiring updates
- `tests/test_cross_platform_packaging.py` — rewrite hardcoded path expectations and `os.name` checks to use `PlatformConfig` mocks
- `tests/test_llm_server.py` — rewrite binary name and path expectations to use `PlatformConfig` mocks
- `tests/test_config.py` — update `get_platform()` and `get_config_dir()` tests to test `PlatformConfig` factory
- `tests/test_crash_logging.py` — verify monkeypatch target string after refactor
- `tests/test_feedback.py` — verify patch target string after refactor
- New: `tests/test_platform_config.py` — unit tests for `PlatformConfig` dataclass and factory across all platforms
- New: `tests/test_template_seeding.py` — unit tests for first-run seeding (empty dir, non-empty dir, idempotency)
- New: `tests/test_doctor.py` — unit tests for `--doctor` CLI output

### Docs requiring post-landing cleanup
- `specs/documentation-overhaul.md` — remove resolved audit caveats
- `tasks/documentation-overhaul.md` — remove workaround language from task done-whens
- `README.md` — add Windows file-storage paths, update removal commands

## Constraints

- Backward compatible: existing users' config dirs and data dirs must continue to work — migration, not breakage
- `PlatformConfig` must be constructable without a running GUI (for CLI commands and scripts)
- First-run template seeding must be idempotent — safe to run on every launch, only copies if user dir is empty
- `--doctor` must work without llama-server installed (it reports the absence, doesn't require it)
- No new dependencies

## Out of Scope

- Creating a Windows PowerShell installer (future work; this spec only removes the false reference)
- Linux ARM64 release builds (separate CI/packaging concern)
- Changing the installer's system dependency logic (apt/brew/etc.) — that must stay in the shell script
- Adding a `templatr --setup` interactive wizard (--doctor is diagnostic only)

## Dependencies

- None — this is foundational debt cleanup with no feature dependencies

## Notes

### Audit Evidence

| Finding | File(s) | Line(s) |
|---------|---------|---------|
| `get_platform()` exists but nothing calls it | `templatr/core/config.py` | 33–55 |
| `get_config_dir()` re-queries `platform.system()` directly, no Windows handling | `templatr/core/config.py` | 63–93 |
| `find_server_binary()` uses `os.name` independently, hardcodes data paths | `templatr/integrations/llm.py` | 274, 288–313 |
| `dedupe_templates.py` reimplements config dir with `os.name`+`os.uname` | `scripts/dedupe_templates.py` | 18–29 |
| `download_llama_server.py` uses `sys.platform` (4th detection API) | `scripts/download_llama_server.py` | 42, 192 |
| installer creates config.json with `font_size: 11` (Python default: 13) | `install.sh` | 270–288 |
| installer is the only code that seeds templates | `install.sh` | 227–264 |
| error messages hardcode `~/.config/templatr/config.json` (wrong on macOS) | `templatr/integrations/llm.py` | 442, 454 |
| `install.sh` references non-existent PowerShell installer | `install.sh` | 75–76 |
| No `get_data_dir()` — `XDG_DATA_HOME` ignored by app, respected by installer | `install.sh` 37 vs `llm.py` 288 | — |

### Detection API Inventory (current state)

| API | Files Using It |
|-----|---------------|
| `platform.system()` | config.py, download_llama_server.py, build.py |
| `os.name` | llm.py, dedupe_templates.py, tests |
| `sys.platform` | download_llama_server.py, tests |
| `os.uname()` | dedupe_templates.py |

### Target state

All Python code uses `get_platform_config()` → `PlatformConfig`. Build/CI scripts (`build.py`, `download_llama_server.py`) may retain direct `platform.system()` calls since they run outside the installed package context, but should use the same vocabulary (`"linux"`, `"macos"`, `"windows"`, `"wsl2"`).

## Downstream Impact Catalog

A full downstream analysis (2026-02-28) identified every file that will be affected when this spec lands. This catalog must be consulted during implementation to avoid regressions.

### Python files that MUST change (HIGH risk)

| File | Lines | What changes | Why |
|------|-------|-------------|-----|
| `templatr/core/config.py` | 33–119 | Replace `get_platform()`, `is_windows()`, `get_config_dir()` with `PlatformConfig` and `get_platform_config()`. Add `get_data_dir()`. Fix Windows `get_config_dir()` to use `%APPDATA%`. | Primary change target — single source of truth |
| `templatr/integrations/llm.py` | 272–315, 327, 339, 449–465 | `find_server_binary()`: replace `os.name` check + 6 hardcoded paths with `PlatformConfig.binary_search_paths`. `find_models()`/`get_models_dir()`: use `PlatformConfig.models_dir`. `start()`: replace hardcoded `~/.config/templatr/config.json` in error messages with `get_config_dir()`. | 2 platform detection calls, 8 hardcoded paths, 2 wrong error messages |
| `templatr/ui/llm_toolbar.py` | 217 | Replace `"Place .gguf files in ~/models/"` with `PlatformConfig.models_dir` | Hardcoded user-facing path hint |
| `templatr/core/templates.py` | 237 (`__init__`) | Add first-run seed logic: if user template dir is empty, copy bundled templates | Template seeding currently only in `install.sh` |
| `templatr/__main__.py` | 44–56 | Add `--doctor` argument and diagnostic report handler | New CLI command |
| `scripts/dedupe_templates.py` | 18–29 | Replace local `get_templates_dir()` reimplementation with import from `templatr.core.config` | Duplicated platform logic with 4th detection API |

### Tests that MUST be updated (HIGH risk)

| Test File | Lines | What breaks | Action needed |
|-----------|-------|------------|---------------|
| `tests/test_cross_platform_packaging.py` | 83–84, 108, 181 | Hardcodes `~/.local/share/templatr/llama.cpp/build/bin/` and uses `os.name != "nt"` for binary name — these paths will be replaced by `PlatformConfig` | Rewrite to mock `get_platform_config()` instead of `Path.home()` |
| `tests/test_llm_server.py` | 83, 105 | Uses `os.name != "nt"` for binary name and hardcodes paths matching `find_server_binary()` | Rewrite to use `PlatformConfig` mocks |
| `tests/test_config.py` | 200–252 | Tests `get_platform()` directly and `get_config_dir()` migration logic | Update to test `PlatformConfig` factory; migration tests may need adjustment if `get_config_dir` signature changes |

### Tests that need MINOR patches (MEDIUM risk)

| Test File | Lines | What changes | Action needed |
|-----------|-------|-------------|---------------|
| `tests/test_crash_logging.py` | 26 | Monkeypatches `templatr.core.config.get_config_dir` | Verify patch target string still valid after refactor |
| `tests/test_feedback.py` | 27, 89 | Patches `templatr.core.feedback.get_config_dir` | Verify patch target string still valid after refactor |

### Tests with NO expected breakage

`test_decoupling.py`, `test_graceful_error_recovery.py`, `test_import_export.py`, `test_interfaces.py`, `test_llm_client.py`, `test_new_template_flow.py`, `test_responsive_layout.py`, `test_slash_input.py`, `test_smoke.py`, `test_templates.py`, `test_widgets.py`, `test_chat_widget.py`, `test_command_palette.py`, `test_authoring_docs.py` — all delegate platform work to config functions and use `tmp_path` fixtures.

### Shell / build files that MUST change

| File | Lines | What changes |
|------|-------|--------------|
| `install.sh` | 75–76 | Remove phantom PowerShell installer reference; replace with "Use WSL2 or download from GitHub Releases" |
| `install.sh` | 270–288 | Remove `config.json` creation block (or fix `font_size: 11` → `13`) |

### Files explicitly NOT changing

| File | Reason |
|------|--------|
| `scripts/build.py` | Build-time script; platform detection is for creating distribution artifacts, not runtime config |
| `scripts/download_llama_server.py` | Pre-build download script; writes to `vendor/`, not user config |
| `build.spec` | PyInstaller spec; handles bundling, not runtime paths |
| `.github/workflows/ci.yml` | Uses standard GitHub Actions matrix; no runtime paths |
| `.github/workflows/release.yml` | Delegates platform logic to `scripts/build.py` |
| All 14 UI files (except `llm_toolbar.py`) | Only call `get_config()` for UI settings; self-adapt through existing abstractions |
| `templatr/core/meta_templates.py` | Uses `get_bundle_dir()` and `get_templates_dir()` — self-adapting |
| `templatr/core/feedback.py` | Uses `get_config_dir()` — self-adapting |
| `templatr/core/logging_setup.py` | Uses `get_log_dir()` — self-adapting |

### Docs that need post-landing updates

When this spec is COMPLETE, the following docs must be updated to remove platform-bug caveats:

| Doc | What to update |
|-----|---------------|
| `specs/documentation-overhaul.md` | Remove/annotate audit findings table rows that are resolved; update criteria 2, 3, 5 to remove workaround language; update out-of-scope section |
| `tasks/documentation-overhaul.md` | Remove "Caveats from audit" sections in Tasks 1 and 2; update done-when criteria to remove workaround requirements |
| `README.md` | "Where Files Are Stored" section — can add Windows paths; removal commands can reference `templatr --doctor` |
| `decisions/0002-project-name.md` | Optional: add note that config dir path was later made platform-aware by platform-config-consolidation |
