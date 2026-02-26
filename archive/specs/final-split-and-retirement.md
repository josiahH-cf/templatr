# Feature: Final Split into Two Independent Apps and Retirement of Legacy Project

## Description

Formally separate the existing project into two fully independent applications — `automatr-prompt` and `automatr-espanso` — each with its own GitHub repository, CI pipeline, workspace, and governance. Fix all outstanding lint and bug debt in the prompt app before migration. Archive the legacy `josiahH-cf/automatr` repository.

This work follows the completed lift-and-reorganize phases (see `/archive/specs/app-split-refactor.md`). Both apps already exist locally with passing test suites. The remaining work is cleanup, repository creation, CI setup, validation, and retirement.

## Prior Art

- Original spec: `/archive/specs/app-split-refactor.md` (all 7 ACs met, 29/29 tasks done)
- Decision record: `/decisions/0001-template-ownership-split.md`
- Prompt app: this repo (`automatr/`)
- Espanso app: `/home/josiah/automatr-espanso/` (local, not yet pushed)

## Acceptance Criteria

- [ ] AC-1: All stale Espanso/AHK references removed from prompt app source code, README, and About dialog
- [ ] AC-2: `Config.from_dict()` crash on unknown nested keys is fixed with a regression test
- [ ] AC-3: `ruff check .` passes with zero errors in the prompt app
- [ ] AC-4: `automatr-prompt` GitHub repo exists at `josiahH-cf/automatr-prompt` with clean CI (lint + test on push/PR)
- [ ] AC-5: `automatr-espanso` GitHub repo exists at `josiahH-cf/automatr-espanso` with clean CI (lint + test on push/PR)
- [ ] AC-6: Legacy `josiahH-cf/automatr` repo is tagged, README updated with retirement notice, and archived
- [ ] AC-7: Both apps build and pass tests independently from a fresh clone (no cross-dependency)
- [ ] AC-8: Governance docs exist for both apps defining scope, non-goals, and constraints
- [ ] AC-9: Completed phase tasks are archived; fresh roadmaps exist for both apps

## Affected Areas

### Phase 1 — Current State Cleanup
- `automatr/ui/main_window.py` (About dialog)
- `automatr/core/templates.py` (trigger field comments)
- `automatr/core/config.py` (from_dict bug fix)
- `README.md` (stale sections)
- All `.py` files (ruff lint fixes)

### Phase 2 — Repository Creation
- `pyproject.toml` (URLs)
- GitHub: two new repos

### Phase 3 — CI/CD Setup
- `.github/workflows/ci.yml` (new, both repos)

### Phase 4 — Legacy Retirement
- Legacy repo README, tags

### Phase 5 — Governance
- `AGENTS.md` (both repos)
- New governance docs

### Phase 6 — Validation
- Fresh clone verification (both repos)

### Phase 7 — Task System Reset
- `/archive/` folder
- New roadmap files

## Constraints

- Template JSON format remains backward-compatible (both apps read same schema)
- `Template.trigger` field stays in the dataclass — relabel comments from "Espanso" to generic
- Duplication of shared core code (~1,000 lines) — no shared library
- Follow `AGENTS.md` conventions for testing, commits, and branches
- Each phase produces a working, testable state

## Out of Scope

- Rewriting the LLM integration or llama.cpp protocol
- Publishing packages to PyPI
- Docker/containerization
- Redesigning the template JSON schema
- Adding new features to either app (this is structural work only)

## Dependencies

- Completed phases 1–5 of the original split (`/archive/specs/app-split-refactor.md`)
- GitHub access to create repos and archive the legacy repo
- Local clone of `automatr-espanso` at `/home/josiah/automatr-espanso/`

## Notes

- The prompt app has ~820 ruff lint errors that must be fully resolved before migration to the new repo (clean baseline for CI)
- Known bug: `Config.from_dict()` crashes on unknown nested keys inside `llm`/`ui` sections — must be fixed with a regression test
- 3 remaining Espanso references in Python source are comment-level only (templates.py L85, L521; main_window.py L218)
- The About dialog also has a placeholder URL (`yourname/automatr`) that needs updating
- The `copilot-setup-steps.yml` CI workflow only triggers on changes to itself — a proper `ci.yml` is needed for both repos
- `template_generate.py` (604 lines) and `template_improve.py` (436 lines) exceed the 300-line widget target but are dialog-based and explicitly deferred from decomposition
