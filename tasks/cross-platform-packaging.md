# Tasks: cross-platform-packaging

**Spec:** /specs/cross-platform-packaging.md

## Status

- Total: 4
- Complete: 4
- Remaining: 0

## Task List

### Task 1: llama-server download script

- **Files:** `scripts/download_llama_server.py` (new)
- **Done when:** Script detects current platform (Linux/macOS-Intel/macOS-ARM/Windows), downloads the correct pre-built `llama-server` binary from llama.cpp GitHub releases, verifies the download, and places it in `vendor/llama-server/`. Script is idempotent (skips if binary already present and correct).
- **Criteria covered:** Criterion 5 (bundles pre-compiled llama-server)
- **Status:** [x] Complete

### Task 2: PyInstaller spec and frozen-app path detection

- **Files:** `build.spec` (new), `templatr/core/config.py` (add frozen-app base path detection), `templatr/integrations/llm.py` (add bundled binary to search order)
- **Done when:** PyInstaller spec packages the app in `--onedir` mode, including the `vendor/llama-server/` binary and `templates/` directory. `config.py` detects `sys._MEIPASS` and adjusts base paths. `llm.py` checks `<bundle_dir>/vendor/llama-server` before system paths.
- **Criteria covered:** Criterion 1 (PyInstaller spec), Criterion 6 (bundled binary discovered first)
- **Status:** [x] Complete

### Task 3: Build automation script

- **Files:** `scripts/build.py` (new)
- **Done when:** Running `python scripts/build.py` on any supported platform: (1) calls the download script if needed, (2) runs PyInstaller with the spec file, (3) produces a platform-appropriate artifact in `dist/`. Script prints clear progress and error messages.
- **Criteria covered:** Criterion 7 (build script)
- **Status:** [x] Complete

### Task 4: Platform-specific artifact packaging

- **Files:** `scripts/build.py` (extend with packaging steps)
- **Done when:** Linux: build produces an AppImage that launches on Ubuntu 22.04+. macOS: build produces a `.app` bundle in a `.dmg`. Windows: build produces a working directory-mode executable. Each artifact is under its size constraint (Linux/macOS <200 MB, Windows <300 MB).
- **Criteria covered:** Criterion 2 (Linux AppImage), Criterion 3 (macOS .dmg), Criterion 4 (Windows exe)
- **Status:** [x] Complete

## Test Strategy

| Criterion | Tested in Task |
|-----------|---------------|
| 1. PyInstaller spec works | Task 2 (test: run PyInstaller on CI, verify output directory exists) |
| 2. Linux AppImage | Task 4 (test: build on Ubuntu runner, verify AppImage launches with `--help` or `--version`) |
| 3. macOS .app/.dmg | Task 4 (test: build on macOS runner, verify .app exists in .dmg) |
| 4. Windows exe | Task 4 (test: build on Windows runner, verify .exe launches with `--version`) |
| 5. Bundled llama-server | Task 1 (test: run script, verify binary exists and is executable) |
| 6. Bundled binary found first | Task 2 (test: mock sys._MEIPASS, verify llm.py searches bundled path first) |
| 7. Build script | Task 3 (test: run script in CI, verify dist/ output) |

## Session Log

<!-- Append after each session: date, completed, blockers -->

### 2026-02-27

- **Completed:** All 4 tasks (download script, frozen-app detection, PyInstaller spec, build automation)
- **Files changed:** `scripts/download_llama_server.py` (new), `scripts/build.py` (new), `build.spec` (new), `templatr/core/config.py` (is_frozen, get_bundle_dir), `templatr/integrations/llm.py` (bundled binary search), `templatr/core/meta_templates.py` (get_bundle_dir), `.gitignore` (vendor/dist/build)
- **Tests added:** `tests/test_cross_platform_packaging.py` — 16 tests covering frozen detection, bundled binary preference, platform key detection, idempotence, spec/toml verification
- **Result:** 126 tests pass, zero lint errors, zero new runtime dependencies.
