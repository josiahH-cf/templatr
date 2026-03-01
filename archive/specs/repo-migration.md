# Feature: Repository Migration to Templatr

## Description

Complete the rename from `automatr-prompt` to `templatr` by creating a new GitHub repository, removing all legacy `automatr` references, deleting the legacy `automatr/` shim package, and migrating the full project to a clean `~/templatr` workspace. The prior `project-rename` spec renamed the Python package and internal imports but left the repository name, workspace directory, GitHub remote, several documentation files, `pyproject.toml` metadata, `install.sh`, the legacy `automatr/` directory, and assorted file-level references unchanged.

## Problem

1. **Repository is still named `automatr-prompt`** — GitHub URL, git remote, and workspace directory all reference the old name.
2. **Legacy `automatr/` directory still exists** — a full parallel package with old imports, confusing for contributors and tooling.
3. **`pyproject.toml`** — `name`, entry point, URLs, and `packages` still reference `automatr`.
4. **`install.sh`** — aliases, data/config paths, and verification commands still reference `automatr`.
5. **`README.md`** — 9 references to "automatr", 0 to "templatr".
6. **`AGENTS.md`** — architecture section still documents `automatr/` paths.
7. **`GOVERNANCE.md`** — references `automatr-espanso`.
8. **`decisions/0001-template-ownership-split.md`** — references old package imports.
9. **Source files in `templatr/`** — several contain stale `automatr` in docstrings or comments (e.g., `llm.py` docstring: "Local LLM integration for Automatr").
10. **Test files** — some import or reference `automatr`.
11. **Git remotes** — `origin` points to `automatr-prompt.git`, `legacy` points to `automatr.git`.
12. **Feature specs/tasks** — downstream specs don't need path changes since they already reference `templatr/` paths.

## Acceptance Criteria

- [ ] A new GitHub repository `josiahH-cf/templatr` exists and is initialized
- [ ] The workspace directory is `~/templatr` (not `~/automatr-prompt`)
- [ ] The `automatr/` directory is deleted — no legacy shim package remains
- [ ] `pyproject.toml` `[project]` name is `templatr`, entry point is `templatr = "templatr.__main__:main"`, URLs point to `github.com/josiahH-cf/templatr`
- [ ] `install.sh` references `templatr` in all aliases, paths, messages, and verification commands
- [ ] `README.md` references only `templatr` (zero `automatr` matches, except historical context)
- [ ] `AGENTS.md` architecture section documents `templatr/` paths (no `automatr/`)
- [ ] `GOVERNANCE.md` links updated or annotated where external repos are referenced
- [ ] All Python source files in `templatr/` have no `automatr` in docstrings or comments (except migration logic in `config.py`)
- [ ] All test files import only from `templatr`, no `automatr` references
- [ ] `git remote -v` shows only `origin → github.com/josiahH-cf/templatr.git` (legacy remote removed)
- [ ] `ruff check .` passes with zero errors
- [ ] `pytest` passes with zero failures
- [ ] No new dependencies added
- [ ] VS Code opens a new window in `~/templatr` as the final step

## Affected Areas

### Delete
- `automatr/` — entire legacy shim directory (7+ files)

### Rename / Heavy Edit
- `pyproject.toml` — name, entry point, URLs, packages
- `install.sh` — aliases, paths, messages, verification (~15 references)
- `README.md` — title, descriptions, URLs (~9 references)
- `AGENTS.md` — architecture section (~4 references)
- `GOVERNANCE.md` — external repo link (~1 reference)

### Light Edit (docstrings/comments)
- `templatr/integrations/llm.py` — module docstring
- `templatr/core/config.py` — any remaining `automatr` comments
- `templatr/core/feedback.py` — any remaining `automatr` comments
- `templatr/core/templates.py` — any remaining `automatr` comments
- `templatr/ui/main_window.py` — any remaining `automatr` comments
- `decisions/0001-template-ownership-split.md` — import references
- `scripts/dedupe_templates.py` — any remaining references
- `tests/test_config.py`, `tests/test_smoke.py`, `tests/test_responsive_layout.py` — any remaining references

### Git / Infrastructure
- Create new GitHub repo `josiahH-cf/templatr`
- Clone/copy project to `~/templatr`
- Update git remote origin
- Remove legacy remote
- Push all branches and tags

## Constraints

- **Backward-compatible config migration** must remain — `config.py` already migrates from `~/.config/automatr/`, that code stays
- Must not break any existing tests
- Must not change behavior — structural/naming only
- The `automatr` entry point in pyproject.toml should be removed (only `templatr` remains)
- `build.spec` already references `templatr` — verify, don't break

## Out of Scope

- Archiving the old `automatr-prompt` GitHub repo (manual, post-migration)
- Updating any external references outside this repository
- PyPI registration

## Dependencies

- All prior specs complete (project-rename ✅, ci-pipeline ✅, etc.)
- Must be done **before** chat-ui-core to avoid a messy mid-feature repo migration

## Implementation Steps (High Level)

1. **Create new GitHub repo** — `gh repo create josiahH-cf/templatr --public`
2. **Copy project** — `cp -a ~/automatr-prompt ~/templatr` (preserving git history)
3. **In `~/templatr`:** delete `automatr/`, update all files, fix remotes
4. **Run lint + tests** — verify clean
5. **Push to new remote** — all branches and tags
6. **Open VS Code window** — `code ~/templatr`

## Notes

- The `automatr/` directory is not a backwards-compat shim — it's a full stale copy of the old code that imports from itself. It should be deleted entirely.
- The `templatr.egg-info/` directory will be regenerated on next `pip install -e .` and doesn't need manual management.
- The `config.py` migration code (`~/.config/automatr/` → `~/.config/templatr/`) is intentional and should remain as the only legitimate `automatr` reference in source code.
- After this migration, the `project-rename` spec's "Out of Scope" item "GitHub repo rename" is resolved.
