# Feature: Project Rename & Identity

## Description

Choose a memorable, shareable project name and rename the package, imports, config paths, install script, and all references throughout the codebase. This must happen first because the name affects the GitHub repo URL, Python package name, import paths, config directories, and all documentation. Record the naming decision in `/decisions/`.

## Acceptance Criteria

- [x] A decision record exists at `/decisions/0002-project-name.md` documenting the chosen name, alternatives considered, and rationale
- [x] `pyproject.toml` uses the new package name in `[project]` name, entry point, and all metadata
- [x] The Python package directory is renamed and all internal imports resolve without errors (`python -c "import <newname>"` succeeds)
- [x] `install.sh` references the new name in aliases, directory paths, and user-facing messages
- [x] `config.py` uses the new name for config/data directory paths (e.g., `~/.config/<newname>/`) with automatic migration from `~/.config/automatr/` for existing users
- [x] Running `pytest` passes with zero failures after the rename
- [x] The README title and first paragraph use the new name

## Affected Areas

- `pyproject.toml`
- `automatr/` → `<newname>/` (entire directory rename)
- `install.sh`
- `README.md`
- `AGENTS.md`, `CLAUDE.md`
- `tests/` (all imports)
- All internal `from automatr.*` import statements

## Constraints

- Must be backward-compatible for existing users — config directory migration from `~/.config/automatr/` to new path, falling back to old path if new doesn't exist
- Name must be valid as a Python package identifier (lowercase, no hyphens in the package dir)
- Name must be available on GitHub (check before committing)

## Out of Scope

- Logo design
- Domain registration
- GitHub repo rename (done manually after merge)
- PyPI name reservation (not publishing to PyPI per AGENTS.md)

## Dependencies

None — this is the first step in the execution order.

## Notes

- Naming decision requires user input. Present 3–5 name candidates during implementation. Consider: clarity of purpose, memorability, no existing conflicts on GitHub/PyPI.
- The rename touches effectively every file, so it should be done before other work starts to avoid merge conflicts across all other branches.
- The config migration strategy: on first load, check if new config dir exists → if not, check if old `~/.config/automatr/` exists → if so, copy contents to new path and log the migration.
