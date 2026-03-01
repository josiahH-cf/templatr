# Feature: Documentation Overhaul

## Description

Write polished, per-OS getting-started documentation with screenshots, a contributing guide, and a CI check that catches stale install instructions automatically. This is the user-facing companion to the packaging and UI work — it's what turns "a project on GitHub" into "something I can share with a link."

A cross-platform architecture audit (2026-02-28) identified platform-handling issues that affect what can be accurately documented. This spec incorporates those findings as caveats and defers the underlying engineering fixes to a new `platform-config-consolidation` spec.

## Acceptance Criteria

- [ ] README.md has a Quick Start section with sub-sections for macOS, Windows, and Linux, each showing 3–5 steps from download to first prompt
- [ ] Windows Quick Start covers pre-built binary download only; dev setup on Windows is documented as WSL2-only until a native install path exists
- [ ] A `CONTRIBUTING.md` explains developer setup (`pip install -e .[dev]`, running tests, the template authoring workflow from `TEMPLATES.md`), and notes that `pip install` now seeds bundled templates automatically on first launch
- [ ] A `docs/` directory contains per-OS troubleshooting guides (common install errors and their fixes)
- [ ] Windows troubleshooting guide addresses: that native Windows dev builds are not yet supported, and WSL2 is the recommended dev path
- [ ] A CI script (`scripts/check_docs.py` or inline workflow step) verifies that binary names and install commands in README.md match what's in `pyproject.toml` and build scripts — CI fails if they diverge
- [ ] README.md includes badges for: CI status, latest release version, platform support (macOS / Windows / Linux)
- [ ] All screenshots are stored in `docs/images/` and referenced with relative paths in the docs
- [ ] "Where Files Are Stored" section documents platform-specific paths accurately (Linux, macOS, Windows binary users), noting that Windows paths apply only to pre-built binaries

## Affected Areas

- New: `CONTRIBUTING.md`, `docs/` directory, `docs/images/`, `scripts/check_docs.py`
- Modified: `README.md` (major rewrite), `.github/workflows/ci.yml` (add doc-check step)

## Constraints

- Screenshots: chat UI is finalized (chat-ui-core ✅) — capture actual screenshots, not placeholders
- Doc-check script runs in under 10 seconds
- All docs are Markdown — no static site generator, no hosted docs site
- Do not document platform behaviors that are currently broken (e.g., don't claim `pip install` seeds templates, don't suggest a Windows dev workflow beyond WSL2) — document reality, flag known issues, and link to `platform-config-consolidation`

## Out of Scope

- Hosted documentation (GitHub Pages, ReadTheDocs)
- Video tutorials
- Localization / translation
- API documentation (no public API to document)
- Fixing platform detection fragmentation, installer boundary issues, or missing `get_data_dir()` — resolved by `platform-config-consolidation` ✅
- Creating a Windows PowerShell installer — not planned; `install.sh` now directs to WSL2 or GitHub Releases ✅

## Dependencies

- Spec: `cross-platform-packaging` ✅ — install instructions depend on final artifact format
- Spec: `chat-ui-core` ✅ — screenshots depend on final UI
- Soft dependency: `platform-config-consolidation` (not blocking — docs can be written with accurate caveats now, and updated after platform fixes land)

### Execution Order Note

`platform-config-consolidation` is now **complete**. The following changes apply:
- **Criteria 2** (Windows binary-only caveat): Windows dev path remains WSL2-only; binary download is primary
- **Criteria 3** (CONTRIBUTING.md): template seeding now runs on first launch — no manual workaround needed
- **Criteria 5** (Windows troubleshooting): phantom PowerShell reference removed from `install.sh`
- **Audit findings table**: 7 of 9 rows resolved; see table below for current status
- **Task caveats**: audit-related caveats in Tasks 1 and 2 are simplified

If this spec is implemented **before** `platform-config-consolidation`, document reality with caveats as currently specified. The `platform-config-consolidation` Task 6 (post-landing doc cleanup) will update these docs after the platform fixes land.

## Notes

- The doc-freshness CI check: a Python script that (1) extracts fenced code blocks from README, (2) checks that referenced file paths exist, (3) checks that the binary/package name matches `pyproject.toml`'s `[project]` name. If `README.md` says "download automatr" but the package is now "promptlocal," CI fails.
- Quick Start format per OS: a numbered list that a non-technical user can follow. Example: "1. Go to [Releases page]. 2. Download `appname-linux.AppImage`. 3. Make it executable: `chmod +x appname-linux.AppImage`. 4. Double-click to run."
- Screenshot convention: use descriptive filenames (`docs/images/main-chat-view.png`, `docs/images/slash-command-palette.png`).
- Badge URLs: CI `https://github.com/josiahH-cf/templatr/actions/workflows/ci.yml/badge.svg`, Release `https://img.shields.io/github/v/release/josiahH-cf/templatr`, Platforms: static shield for `Linux | macOS | Windows`.
- Windows Quick Start: pre-built zip from GitHub Releases (primary), WSL2 + `./install.sh` (dev alternative). There is **no native Windows installer** — `install.sh` rejects Windows and references a non-existent PowerShell script.
- Known issue: `pip install -e .` leaves zero bundled templates because template seeding only runs inside `install.sh`. The CONTRIBUTING.md must note this and provide a workaround (manually copy `templates/` to config dir).
- Known issue: app error messages hardcode `~/.config/templatr/config.json` which is wrong on macOS — troubleshooting docs should document the correct platform-specific paths, not repeat the hardcoded strings.

## Audit Findings Reference

The following issues were identified during the 2026-02-28 cross-platform architecture audit. They are **not in scope** for this spec but inform what the documentation must say (or carefully avoid saying):

| Finding | Severity | Impact on Docs |
|---------|----------|---------------|
| `get_platform()` is dead code — nothing calls it | ~~High~~ | ✅ Resolved — now delegates to `PlatformConfig` |
| Config dir computed in 3 places with inconsistent Windows handling | ~~High~~ | ✅ Resolved — single `PlatformConfig` source of truth |
| `pip install` leaves zero templates (seeding only in install.sh) | ~~High~~ | ✅ Resolved — first-run seeding in app |
| No Windows install path despite CI building Windows artifacts | High | Windows Quick Start = binary download only |
| `install.sh` references non-existent PowerShell installer | ~~High~~ | ✅ Resolved — reference removed |
| `get_config_dir()` uses XDG path on Windows instead of `%APPDATA%` | ~~Medium~~ | ✅ Resolved — `PlatformConfig` uses `%APPDATA%` |
| Error messages hardcode `~/.config/templatr` (wrong on macOS) | ~~Medium~~ | ✅ Resolved — messages use canonical paths |
| `llm.py` ignores `XDG_DATA_HOME` for binary search | ~~Medium~~ | ✅ Resolved — `PlatformConfig` respects `XDG_DATA_HOME` |
| Linux ARM64 has no release build | Medium | Quick Start should note x86_64 only for pre-built Linux binaries |
