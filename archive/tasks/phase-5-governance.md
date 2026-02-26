# Tasks: Phase 5 — Governance and Constraints

**Spec:** /specs/final-split-and-retirement.md

## Status

- Total: 3
- Complete: 0
- Remaining: 3

## Prerequisites

- Phase 2 complete (both repos exist with code)

## Task List

### Task 1: Update AGENTS.md for automatr-prompt

- **Files:** `AGENTS.md` (in `automatr-prompt` repo)
- **Done when:** (1) Project description updated to remove any vestiges of combined-app language. (2) Architecture section reflects the current decomposed UI structure (template_tree, variable_form, output_pane, llm_toolbar, etc.). (3) No references to Espanso, AutoHotkey, or the legacy repo. (4) Scope boundaries defined: local prompt optimization, template management, llama.cpp integration. (5) Non-goals stated: Espanso sync, cloud APIs, multi-user, PyPI publishing. (6) Commit and push
- **Criteria covered:** AC-8
- **Status:** [ ] Not started

### Task 2: Create governance doc for automatr-prompt

- **Files:** `GOVERNANCE.md` (new file in `automatr-prompt` repo)
- **Done when:** File defines: (1) Scope: local-model prompt optimizer, template CRUD, llama.cpp LLM runtime management. (2) Non-goals: Espanso/text-expander integration, cloud LLM APIs, multi-tenant, mobile/web. (3) Architecture constraints: PyQt6 desktop, no network except localhost llama-server, JSON-only template format. (4) Deployment model: single-user desktop install via `install.sh` or `pip install`. (5) Ownership model: solo maintainer, cross-agent review encouraged. (6) Roadmap structure: milestones in `/tasks/`, specs in `/specs/`, decisions in `/decisions/`
- **Criteria covered:** AC-8
- **Status:** [ ] Not started

### Task 3: Create governance doc for automatr-espanso

- **Files:** `GOVERNANCE.md`, `AGENTS.md` (in `automatr-espanso` repo at `/home/josiah/automatr-espanso/`)
- **Done when:** (1) `AGENTS.md` updated with accurate project description, architecture, and conventions (no references to prompt optimizer or LLM). (2) `GOVERNANCE.md` created defining: scope (Espanso config management, template-to-trigger sync, YAML generation), non-goals (LLM integration, prompt optimization, cloud APIs), architecture constraints (PyQt6 desktop + CLI, PyYAML dependency, Espanso config directory integration), deployment/ownership/roadmap same pattern as prompt app. (3) Commit and push
- **Criteria covered:** AC-8
- **Status:** [ ] Not started

## Test Strategy

| Criterion | Verified by |
|-----------|-------------|
| AC-8 | Task 1–3: governance docs exist with required sections; grep confirms no cross-app references |

## Rollback Strategy

Documentation-only changes. Revert commits if content needs revision.

## Session Log

<!-- Append after each session: date, completed, blockers -->
