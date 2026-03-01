# Tasks: project-rename

**Spec:** /specs/project-rename.md

## Status

- Total: 4
- Complete: 4
- Remaining: 0

## Task List

### Task 1: Decision record and name selection

- **Files:** `decisions/0002-project-name.md`
- **Done when:** Decision record exists with chosen name, 3+ alternatives considered, and rationale documented. User has approved the name.
- **Criteria covered:** Criterion 1 (decision record)
- **Status:** [x] Complete

### Task 2: Rename Python package and update all imports

- **Files:** `automatr/` → `<newname>/` (directory rename), all `*.py` files with `from automatr` or `import automatr` imports, `pyproject.toml` (package name, entry point)
- **Done when:** `python -c "import <newname>"` succeeds, `python -c "import automatr"` fails, `pyproject.toml` reflects new name, all internal imports resolve.
- **Criteria covered:** Criterion 2 (pyproject.toml), Criterion 3 (imports resolve)
- **Status:** [x] Complete

### Task 3: Update config paths, install script, and migration

- **Files:** `<newname>/core/config.py` (new config dir paths + migration from old), `install.sh` (aliases, paths, messages)
- **Done when:** Config dir is `~/.config/<newname>/`, existing `~/.config/automatr/` contents are auto-migrated on first run, `install.sh` references new name throughout.
- **Criteria covered:** Criterion 4 (install.sh), Criterion 5 (config paths + migration)
- **Status:** [x] Complete

### Task 4: Update documentation and verify tests

- **Files:** `README.md`, `AGENTS.md`, `CLAUDE.md`, `tests/` (import updates)
- **Done when:** README title/first paragraph use new name, all test files import from new package, `pytest` passes with zero failures.
- **Criteria covered:** Criterion 6 (tests pass), Criterion 7 (README)
- **Status:** [x] Complete

## Test Strategy

| Criterion | Tested in Task |
|-----------|---------------|
| 1. Decision record exists | Task 1 (manual verification) |
| 2. pyproject.toml updated | Task 2 (pytest import test) |
| 3. Imports resolve | Task 2 (pytest full suite) |
| 4. install.sh updated | Task 3 (grep verification) |
| 5. Config paths + migration | Task 3 (unit test: mock old dir, verify migration) |
| 6. Tests pass | Task 4 (full pytest run) |
| 7. README updated | Task 4 (manual verification) |

## Session Log

<!-- Append after each session: date, completed, blockers -->

### 2026-02-27

- Chose name **templatr** (decision record: `/decisions/0002-project-name.md`)
- Renamed `automatr/` → `templatr/` directory
- Updated all Python imports (package + tests + mock patch targets)
- Updated `pyproject.toml` (name, entry point, URLs, package find pattern)
- Updated `install.sh` (aliases, paths, messages, smoke tests)
- Updated `config.py` with `templatr` config dir + migration from `~/.config/automatr/`
- Updated `README.md`, `AGENTS.md`, `scripts/dedupe_templates.py`
- Updated `llm.py` data directory paths (Linux + macOS)
- Added 2 migration tests to `test_config.py`
- Final: 74/74 tests pass, ruff clean
