# Tasks: Phase 5 — Create automatr-espanso Repo

**Spec:** /specs/app-split-refactor.md

## Status

- Total: 7
- Complete: 0
- Remaining: 7

## Prerequisites

- Phase 1 complete (prompt app exists — provides core code to copy)
- Phase 4 complete (template ownership decided — know which templates to bundle)

## Task List

### Task 1: Create new repo and copy core code

- **Files:** New repo: `automatr-espanso/`. Copied from `automatr-prompt`: `core/config.py`, `core/templates.py`, `ui/theme.py`
- **Done when:** New repo exists with: `pyproject.toml` (PyYAML dependency, no `requests`), `README.md`, `AGENTS.md` (adapted), basic directory structure. Core code copied and imports adjusted. `EspansoConfig` dataclass re-added to `config.py`. `LLMConfig` removed from `config.py`. Package installs cleanly with `pip install -e .`
- **Criteria covered:** AC-7 (prerequisite)
- **Status:** [ ] Not started

### Task 2: Lift espanso.py integration

- **Files:** New: `automatr_espanso/integrations/espanso.py`
- **Done when:** `espanso.py` from the original codebase is restored into this repo. Imports updated to reference new package structure. WSL2→Windows path detection, YAML v2 form rendering, and Espanso process restart logic all preserved. `sync_to_espanso()` function works from CLI
- **Criteria covered:** AC-7
- **Status:** [ ] Not started

### Task 3: Create CLI entry point

- **Files:** `automatr_espanso/__main__.py`, `pyproject.toml`
- **Done when:** `automatr-espanso sync` command syncs templates to Espanso (equivalent to old `automatr --sync`). `automatr-espanso status` shows Espanso process status and config path. `automatr-espanso list` shows templates with triggers. Console script registered in `pyproject.toml`
- **Criteria covered:** AC-7
- **Status:** [ ] Not started

### Task 4: Build template browser GUI

- **Files:** New: `automatr_espanso/ui/main_window.py`, `automatr_espanso/ui/template_browser.py`
- **Done when:** PyQt6 window launches with: template tree view (filtered to show trigger info prominently), template preview pane showing content and trigger, search/filter capability. Reuses `TemplateTreeWidget` pattern from Phase 3 if applicable, but adapted for Espanso focus (trigger column, trigger highlighting)
- **Criteria covered:** AC-7
- **Status:** [ ] Not started

### Task 5: Build trigger editor and sync UI

- **Files:** New: `automatr_espanso/ui/trigger_editor.py`, `automatr_espanso/ui/sync_panel.py`
- **Done when:** (1) Trigger editor dialog allows: editing trigger string, previewing Espanso match output, toggling templates for sync. (2) Sync panel shows: last sync time, sync status (success/error/pending), manual sync button, auto-sync toggle, Espanso process status indicator. (3) "Sync Now" button calls `sync_to_espanso()` and displays result
- **Criteria covered:** AC-7
- **Status:** [ ] Not started

### Task 6: Create install.sh for Espanso app

- **Files:** `install.sh`
- **Done when:** Installer handles: (1) Python + PyQt6 system deps, (2) venv creation + `pip install -e .`, (3) Espanso detection and config path resolution, (4) AutoHotkey script setup (WSL2 only), (5) Template copying (Espanso-app templates only, per Phase 4 decision), (6) Smoke test. No llama.cpp build step. No LLM-related config. Runs on Linux/WSL2/macOS
- **Criteria covered:** AC-7
- **Status:** [ ] Not started

### Task 7: Write tests and verify

- **Files:** `tests/` in new repo
- **Done when:** Tests exist for: (1) `sync_to_espanso()` produces valid YAML with correct Espanso v2 syntax (mocked filesystem), (2) WSL2 path detection (mocked platform), (3) `ConfigManager` with `EspansoConfig` only, (4) template loading with trigger field, (5) CLI commands (`sync`, `status`, `list`) run without error. Minimum 8 test functions. All pass. `ruff check .` passes
- **Criteria covered:** AC-7
- **Status:** [ ] Not started

## Test Strategy

| Criterion | Verified by |
|-----------|-------------|
| AC-7 | Task 7: full test suite + manual GUI verification |

## Definition of Done

- `automatr-espanso` installs and runs independently
- `automatr-espanso sync` produces a valid `automatr.yml` in Espanso config
- GUI launches, shows templates, allows trigger editing and manual sync
- No dependency on `requests` or llama.cpp
- All tests pass, `ruff check .` passes

## Rollback Strategy

This is a new repo — rollback is simply not merging. No risk to `automatr-prompt`.

## Notes

- This phase is a **separate epic** — it should get its own scoping pass and potentially its own spec when the time comes. This task file is a roadmap, not a commitment.
- The Espanso GUI is ~70% new work. Consider building the CLI (Task 3) first and using it for a while before investing in the GUI (Tasks 4-5).
- The duplicated core code (`config.py`, `templates.py`) will diverge over time. This is acceptable — each app evolves independently. If divergence becomes painful, revisit the shared library decision.
- Reference the original `automatr` repo's `integrations/espanso.py` commit history for edge-case handling context.

## Session Log

<!-- Append after each session: date, completed, blockers -->
