# Tasks: documentation-overhaul

**Spec:** /specs/documentation-overhaul.md

## Status

- Total: 3
- Complete: 0
- Remaining: 3

## Task List

### Task 1: README rewrite with per-OS quick start

- **Files:** `README.md` (major rewrite)
- **Done when:** README has: project description, feature highlights, Quick Start sections for macOS/Windows/Linux (3–5 steps each, from download to first prompt), screenshot placeholders (or actual screenshots if UI is finalized), badges for CI status, latest release, and platform support.
- **Criteria covered:** Criterion 1 (per-OS Quick Start), Criterion 5 (badges)
- **Status:** [ ] Not started

### Task 2: CONTRIBUTING.md, docs directory, and troubleshooting

- **Files:** `CONTRIBUTING.md` (new), `docs/` (new directory), `docs/troubleshooting-linux.md`, `docs/troubleshooting-macos.md`, `docs/troubleshooting-windows.md`, `docs/images/` (new directory for screenshots)
- **Done when:** `CONTRIBUTING.md` covers: dev setup (`pip install -e .[dev]`), running tests (`pytest`), the template authoring workflow, and PR expectations. Each troubleshooting doc lists 3–5 common errors with fixes. `docs/images/` exists with a `.gitkeep` or initial screenshots.
- **Criteria covered:** Criterion 2 (CONTRIBUTING.md), Criterion 3 (docs/ troubleshooting), Criterion 6 (screenshots in docs/images/)
- **Status:** [ ] Not started

### Task 3: Doc-freshness CI check

- **Files:** `scripts/check_docs.py` (new), `.github/workflows/ci.yml` (add doc-check step)
- **Done when:** `scripts/check_docs.py` extracts referenced binary/package names from README fenced code blocks and verifies they match `pyproject.toml` `[project]` name. Script exits non-zero on mismatch. CI workflow runs this script and fails the build if docs are stale. Script completes in under 10 seconds.
- **Criteria covered:** Criterion 4 (doc-freshness CI check)
- **Status:** [ ] Not started

## Test Strategy

| Criterion | Tested in Task |
|-----------|---------------|
| 1. Per-OS Quick Start | Task 1 (test: verify README contains macOS, Windows, Linux sections with numbered steps) |
| 2. CONTRIBUTING.md | Task 2 (test: verify file exists with required sections) |
| 3. Troubleshooting docs | Task 2 (test: verify docs/ directory contains per-OS troubleshooting files) |
| 4. Doc-freshness CI | Task 3 (test: run check_docs.py with matching/mismatching names, verify exit codes) |
| 5. Badges | Task 1 (test: verify README contains badge markdown syntax) |
| 6. Screenshots dir | Task 2 (test: verify docs/images/ directory exists) |

## Session Log

<!-- Append after each session: date, completed, blockers -->
