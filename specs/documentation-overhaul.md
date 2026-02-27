# Feature: Documentation Overhaul

## Description

Write polished, per-OS getting-started documentation with screenshots, a contributing guide, and a CI check that catches stale install instructions automatically. This is the user-facing companion to the packaging and UI work — it's what turns "a project on GitHub" into "something I can share with a link."

## Acceptance Criteria

- [ ] README.md has a Quick Start section with sub-sections for macOS, Windows, and Linux, each showing 3–5 steps from download to first prompt
- [ ] A `CONTRIBUTING.md` explains developer setup (`pip install -e .[dev]`, running tests, the template authoring workflow from `TEMPLATES.md`)
- [ ] A `docs/` directory contains per-OS troubleshooting guides (common install errors and their fixes)
- [ ] A CI script (`scripts/check_docs.py` or inline workflow step) verifies that binary names and install commands in README.md match what's in `pyproject.toml` and build scripts — CI fails if they diverge
- [ ] README.md includes badges for: CI status, latest release version, platform support (macOS / Windows / Linux)
- [ ] All screenshots are stored in `docs/images/` and referenced with relative paths in the docs

## Affected Areas

- New: `CONTRIBUTING.md`, `docs/` directory, `docs/images/`, `scripts/check_docs.py`
- Modified: `README.md` (major rewrite), `.github/workflows/ci.yml` (add doc-check step)

## Constraints

- Screenshots must be taken after the chat UI (spec 7) is finalized — text content can be written first, screenshot placeholders added
- Doc-check script runs in under 10 seconds
- All docs are Markdown — no static site generator, no hosted docs site

## Out of Scope

- Hosted documentation (GitHub Pages, ReadTheDocs)
- Video tutorials
- Localization / translation
- API documentation (no public API to document)

## Dependencies

- Spec: `cross-platform-packaging` — install instructions depend on final artifact format
- Spec: `chat-ui-core` — screenshots depend on final UI
- Can write text content first and backfill screenshots later

## Notes

- The doc-freshness CI check: a Python script that (1) extracts fenced code blocks from README, (2) checks that referenced file paths exist, (3) checks that the binary/package name matches `pyproject.toml`'s `[project]` name. If `README.md` says "download automatr" but the package is now "promptlocal," CI fails.
- Quick Start format per OS: a numbered list that a non-technical user can follow. Example: "1. Go to [Releases page]. 2. Download `appname-linux.AppImage`. 3. Make it executable: `chmod +x appname-linux.AppImage`. 4. Double-click to run."
- Screenshot convention: use descriptive filenames (`docs/images/main-chat-view.png`, `docs/images/slash-command-palette.png`).
