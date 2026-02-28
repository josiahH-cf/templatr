# Roadmap — Templatr v1.1

## Backlog

### Platform Config Consolidation
- **Spec:** `/specs/platform-config-consolidation.md` | **Tasks:** `/tasks/platform-config-consolidation.md`
- Consolidate 6 independent platform detection paths into a single `PlatformConfig` source of truth
- Add `get_data_dir()`, fix `get_config_dir()` Windows path, move template seeding into the app
- Add `templatr --doctor` diagnostic CLI command
- Fix install.sh: remove redundant config.json, remove phantom PowerShell installer reference
- Identified by cross-platform architecture audit (2026-02-28)
- **Soft dependency of documentation-overhaul** — docs can be written with caveats now, updated after this lands

### Dialog Size Optimization
- `template_generate.py` (604 lines) and `template_improve.py` (436 lines) exceed the 300-line widget target
- Decompose into smaller, focused components

### Prompt History & Favorites
- Save generated output history per-template
- Mark favorite outputs for quick reuse
- Search history by content or date

### Multi-Model Comparison
- Run the same prompt against multiple local models side-by-side
- Compare output quality, speed, and token usage

### Keyboard Shortcuts
- Add configurable keyboard shortcuts for common actions
- Quick template switching, generation, copy output

### Template Import/Export
- Export templates as shareable JSON bundles
- Import templates from file or URL

## Execution Order

Specs are ordered by dependency chain. Items marked ✅ are complete.

1. ✅ **ci-pipeline** — GitHub Actions CI (no deps)
2. ✅ **project-rename** — Rename to templatr (no deps)
3. ✅ **responsive-layout** — Dynamic sizing & proportional layout (deps: project-rename ✅)
4. ✅ **incremental-decoupling** — Protocol interfaces, DI, circular import fix (no deps)
5. ✅ **crash-logging** — Structured logging + exception hook (deps: project-rename ✅)
6. ✅ **cross-platform-packaging** — PyInstaller standalone builds (deps: project-rename ✅)
7. ✅ **graceful-error-recovery** — GGUF validation, health polling (deps: crash-logging)
8. ✅ **repo-migration** — New repo, delete automatr/, fix all references (deps: graceful-error-recovery ✅)
9. ✅ **chat-ui-core** — Conversational chat UI with / slash commands and inline variable form (deps: repo-migration ✅)
10. ✅ **release-automation** — Tag-triggered CI builds (deps: ci-pipeline ✅, cross-platform-packaging ✅)
11. ✅ **slash-commands** — Extended `/` command system: /help, trigger aliases, enhanced palette UI (deps: chat-ui-core ✅; core slash mechanism already in chat-ui-core)
12. ✅ **template-authoring-workflow** — `/new`, import/export (deps: slash-commands)
13. ✅ **documentation-overhaul** — Per-OS docs, CONTRIBUTING (deps: cross-platform-packaging, chat-ui-core)

## Active

_All v1.1 specs complete. See Backlog for future work._

## Completed

### v1.0.0 — Initial Release
- Template CRUD with JSON storage
- Variable substitution and prompt rendering
- llama.cpp integration (server lifecycle, model management)
- Decomposed UI (14 widgets extracted from monolithic MainWindow)
- 68 tests passing, zero lint errors
- CI/CD with GitHub Actions (Python 3.10–3.12)
- Dark/light theme support

### Post-v1.0.0
- ✅ CI pipeline (pytest + ruff on push/PR, Python 3.10–3.12)
- ✅ Project rename: automatr → templatr (all imports, config, docs, migration)
- ✅ Responsive layout: proportional splitter, dynamic font/padding/header scaling, stretch fill
