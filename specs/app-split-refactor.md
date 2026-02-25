# Feature: Split Automatr into Two Independent Apps

## Description

Split the current monolithic Automatr application into two fully independent repositories — `automatr-prompt` (local prompt optimizer + LLM integration) and `automatr-espanso` (Espanso automation GUI) — using a lift-and-reorganize approach. Each app duplicates the shared core code rather than publishing a shared library, eliminating cross-repo coordination overhead for a solo developer.

## Context & Decisions

### Approach: Lift-and-Reorganize

The codebase is ~5,650 lines of Python with zero tests and no production users. A phased enterprise-grade migration would cost more than the code itself. Instead:

- **Move files, don't rewrite them** — `git mv` into new structure, fix imports
- **Strip, don't abstract** — remove Espanso code from prompt app, don't build adapter layers
- **Test after restructuring** — write tests for the contracts that exist in the new structure
- **Sequence delivery** — ship Prompt Optimizer first, then build Espanso GUI

### Key Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Packaging | Fully separate repos | Maximum independence, no coordination tax |
| Shared code | Duplicated, not shared library | ~1,000 lines of core code; maintenance cost < coordination cost of a 3rd repo |
| Delivery order | Prompt Optimizer first, Espanso later | Prompt Optimizer is 90% of current app; Espanso GUI is mostly new work |
| Espanso UI | Full GUI (eventually) | Starts as CLI-only after Prompt Optimizer ships |
| Templates | Split between apps | Each app bundles only its relevant templates |
| Espanso sub-app start | After Prompt Optimizer is stable | Depends on prompt app existing to copy core from |

### Current Architecture (as-is)

```
automatr/                    (5,650 lines total)
├── __main__.py              (41 lines)  — CLI entry: run_gui() or --sync
├── core/
│   ├── config.py            (272 lines) — ConfigManager, LLMConfig, UIConfig, EspansoConfig
│   ├── templates.py         (829 lines) — Template/Variable dataclasses, TemplateManager CRUD
│   └── feedback.py          (219 lines) — FeedbackManager, AI prompt builders
├── integrations/
│   ├── llm.py               (505 lines) — LLMClient HTTP, LLMServerManager subprocess
│   └── espanso.py           (349 lines) — EspansoManager, YAML sync, WSL2 path detection
└── ui/
    ├── main_window.py       (1,596 lines) — Monolithic main window (both LLM + Espanso)
    ├── template_editor.py   (404 lines) — Create/edit templates (includes trigger field)
    ├── template_generate.py (604 lines) — AI-powered template generation
    ├── template_improve.py  (436 lines) — AI-powered template improvement
    ├── llm_settings.py      (109 lines) — LLM max tokens dialog
    └── theme.py             (280 lines) — Dark/light theme stylesheets
```

**Dependency graph:**

```
__main__.py ──► ui.main_window.run_gui()
                ├── core.config
                ├── core.feedback
                ├── core.templates
                ├── integrations.llm         ◄── Prompt Optimizer concern
                ├── integrations.espanso     ◄── Espanso concern
                └── ui.* (all dialogs)

integrations.llm ──► core.config
integrations.espanso ──► core.config, core.templates
core.feedback ──► core.config, core.templates
```

**Critical observation:** `integrations.llm` and `integrations.espanso` have **zero dependency on each other**. They share only `core.config` and `core.templates`.

### Espanso Coupling Points (to remove from Prompt Optimizer)

| Location | What | Lines |
|----------|------|-------|
| `core/config.py` | `EspansoConfig` dataclass + fields in `Config` | ~15 lines |
| `core/templates.py` | `Template.trigger` field, `iter_with_triggers()` method | ~10 lines |
| `integrations/espanso.py` | Entire file | 349 lines |
| `ui/main_window.py` | `import get_espanso_manager`, `_sync_espanso()`, auto-sync in `_on_template_saved()` and `_delete_template()`, "Sync to Espanso" menu item | ~30 lines |
| `ui/template_editor.py` | `trigger_edit` field, trigger loading/saving | ~10 lines |
| `__main__.py` | `--sync` CLI flag handling | ~5 lines |
| `install.sh` | `setup_espanso()`, `setup_autohotkey()` functions | ~100 lines |

## Acceptance Criteria

- [ ] AC-1: `automatr-prompt` repo exists with all Espanso references removed
- [ ] AC-2: `automatr-prompt` launches, displays templates, and connects to llama.cpp
- [ ] AC-3: `automatr-prompt` has no dependency on PyYAML
- [ ] AC-4: Baseline tests exist for core modules and LLM integration (mocked)
- [ ] AC-5: `MainWindow` is decomposed — no widget class exceeds 300 lines
- [ ] AC-6: Template ownership decision is documented
- [ ] AC-7: `automatr-espanso` repo exists with full GUI (deferred — separate epic)

## Affected Areas

### Phase 1 — Create automatr-prompt repo
- All files in `automatr/` (lift-and-reorganize)
- `pyproject.toml` (remove PyYAML, update metadata)
- `install.sh` (remove Espanso/AutoHotkey functions)

### Phase 2 — Baseline tests
- New files in `tests/`

### Phase 3 — Decompose MainWindow
- `automatr/ui/main_window.py` → split into 4-5 widget modules
- New files: `ui/template_tree.py`, `ui/variable_form.py`, `ui/output_pane.py`, `ui/llm_toolbar.py`

### Phase 4 — Template ownership decision
- New file: `decisions/0001-template-ownership-split.md`

### Phase 5 — Create automatr-espanso repo (separate epic)
- Entirely new repo

## Constraints

- Template JSON file format must remain backward-compatible (both apps read the same `.json` schema; unknown fields are ignored)
- No big-bang rewrite; each phase produces a working app
- `Template.trigger` field stays in the dataclass as an ignored passthrough — don't break template file loading
- Follow `AGENTS.md` conventions for testing, commits, and branches

## Out of Scope

- Rewriting the LLM integration or changing the llama.cpp protocol
- Analyzing llama.cpp documentation (treat as integration boundary only)
- Building the Espanso app during this refactor (it's a follow-on epic)
- Publishing packages to PyPI
- Adding Docker or containerization
- Redesigning the template JSON schema

## Dependencies

- None — this is greenfield restructuring of an existing codebase

## Notes

- The current repo (`automatr`) can either become `automatr-prompt` directly (rename) or serve as archive. Recommend renaming to avoid orphan repos.
- The 31 bundled templates all have `"trigger"` fields. The JSON schema stays the same; the Prompt Optimizer app simply ignores the trigger field.
- `install.sh` is 596 lines with clearly separated functions (`build_llama_cpp()`, `setup_espanso()`, `setup_autohotkey()`), making it straightforward to strip Espanso sections.
- WSL2 cross-platform path detection in `espanso.py` should be preserved in documentation/comments for the future Espanso app to reference.
