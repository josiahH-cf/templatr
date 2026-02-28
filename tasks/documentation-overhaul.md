# Tasks: documentation-overhaul

**Spec:** /specs/documentation-overhaul.md

## Status

- Total: 3
- Complete: 3
- Remaining: 0

## Task List

### Task 1: README rewrite with per-OS quick start

- **Files:** `README.md` (major rewrite)
- **Done when:** README has: project description, feature highlights, Quick Start sections for macOS/Windows/Linux (3–5 steps each, from download to first prompt), actual screenshots (referenced from `docs/images/`), badges for CI status, latest release, and platform support. Windows Quick Start covers pre-built binary download only (zip from Releases); dev-on-Windows is WSL2-only. Linux Quick Start notes pre-built binaries are x86_64 only. "Where Files Are Stored" section documents correct platform-specific paths (not hardcoded `~/.config` for all).
- **Criteria covered:** Criterion 1 (per-OS Quick Start), Criterion 2 (Windows binary-only caveat), Criterion 7 (badges), Criterion 9 (accurate file-storage paths)
- **Caveats from audit:** There is no native Windows installer — `install.sh` rejects Windows. The pre-built zip from GitHub Releases is the only Windows path. Don't document `pip install` as giving a working out-of-box experience (no bundled templates). Verify release artifact names against `release.yml` build matrix.
- **Status:** [x] Complete

### Task 2: CONTRIBUTING.md, docs directory, troubleshooting, and screenshots

- **Files:** `CONTRIBUTING.md` (new), `docs/` (new directory), `docs/troubleshooting-linux.md`, `docs/troubleshooting-macos.md`, `docs/troubleshooting-windows.md`, `docs/images/` (new directory with screenshots)
- **Done when:** `CONTRIBUTING.md` covers: dev setup (`pip install -e .[dev]`), running tests (`pytest`), lint (`ruff check .`), format (`black .`), the template authoring workflow (reference `TEMPLATES.md`), PR expectations, and the known empty-state issue after `pip install` (workaround: manually copy `templates/` to config dir). Each troubleshooting doc lists 3–5 common errors with fixes. Windows troubleshooting explicitly addresses the phantom "PowerShell installer" message from `install.sh` and notes native Windows dev builds are unsupported. macOS troubleshooting notes that error messages referencing `~/.config/templatr` are incorrect — the actual path is `~/Library/Application Support/templatr/`. `docs/images/` contains actual screenshots: `main-chat-view.png`, `slash-command-palette.png`, `template-editor.png`, `new-template-flow.png`.
- **Criteria covered:** Criterion 3 (CONTRIBUTING.md + empty-state documentation), Criterion 4 (docs/ troubleshooting), Criterion 5 (Windows troubleshooting caveats), Criterion 8 (screenshots in docs/images/)
- **Caveats from audit:** Document **reality**, not aspirational behavior. `pip install -e .` does NOT seed templates — this is a known gap. macOS error messages hardcode Linux paths — troubleshooting must note the correct path. The "PowerShell installer" referenced by `install.sh` does not exist — troubleshooting must say so clearly.
- **Status:** [x] Complete

### Task 3: Doc-freshness CI check

- **Files:** `scripts/check_docs.py` (new), `.github/workflows/ci.yml` (add doc-check step)
- **Done when:** `scripts/check_docs.py` extracts referenced binary/package names from README fenced code blocks and verifies they match `pyproject.toml` `[project]` name. Script also checks that file paths referenced in docs (e.g., `docs/images/*.png`, `CONTRIBUTING.md`) actually exist. Script exits non-zero on mismatch. CI workflow runs this script and fails the build if docs are stale. Script completes in under 10 seconds.
- **Criteria covered:** Criterion 6 (doc-freshness CI check)
- **Status:** [x] Complete

## Test Strategy

| Criterion | Tested in Task |
|-----------|---------------|
| 1. Per-OS Quick Start | Task 1 (test: verify README contains macOS, Windows, Linux sections with numbered steps) |
| 2. Windows binary-only caveat | Task 1 (test: verify Windows section references Releases download, not install.sh) |
| 3. CONTRIBUTING.md + empty-state note | Task 2 (test: verify file exists with required sections including pip-install caveat) |
| 4. Troubleshooting docs | Task 2 (test: verify docs/ directory contains per-OS troubleshooting files) |
| 5. Windows troubleshooting caveats | Task 2 (test: verify troubleshooting-windows.md addresses PowerShell installer gap) |
| 6. Doc-freshness CI | Task 3 (test: run check_docs.py with matching/mismatching names, verify exit codes) |
| 7. Badges | Task 1 (test: verify README contains badge markdown syntax) |
| 8. Screenshots dir | Task 2 (test: verify docs/images/ directory exists with .png files) |
| 9. Accurate file-storage paths | Task 1 (test: verify README documents macOS path as ~/Library/Application Support/templatr/) |

## Session Log

<!-- Append after each session: date, completed, blockers -->
