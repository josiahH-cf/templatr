# Tasks: Phase 4 — Template Ownership Decision

**Spec:** /specs/app-split-refactor.md

## Status

- Total: 3
- Complete: 0
- Remaining: 3

## Prerequisites

- Phase 1 complete (prompt app exists and runs)

## Task List

### Task 1: Audit all 31 bundled templates for app affinity

- **Files:** All files in `templates/` (read-only audit)
- **Done when:** A table exists listing every template with columns: name, has trigger, primary use case (prompt optimization / text expansion / both), recommended owner (prompt app / espanso app / both). No template is unclassified
- **Criteria covered:** AC-6
- **Status:** [ ] Not started

### Task 2: Define ownership criteria and write decision record

- **Files:** New: `decisions/0001-template-ownership-split.md`
- **Done when:** Decision record exists with: (1) classification criteria (what makes a template belong to prompt app vs espanso app), (2) the full assignment table from Task 1, (3) handling of templates that belong to both (duplicate vs shared reference), (4) schema compatibility statement (both apps read the same JSON format, ignore unknown fields), (5) guidelines for where future templates should be placed
- **Criteria covered:** AC-6
- **Status:** [ ] Not started

### Task 3: Move templates into app-specific bundles

- **Files:** `templates/` directory restructuring
- **Done when:** Templates are organized into clear ownership groups. The prompt app's `install.sh` or setup only copies prompt-app templates. A manifest or directory convention makes ownership obvious (e.g., templates stay as-is for prompt app; espanso-specific templates are tagged or listed in the decision doc for later extraction). App still loads all templates correctly
- **Criteria covered:** AC-6
- **Status:** [ ] Not started

## Test Strategy

| Criterion | Verified by |
|-----------|-------------|
| AC-6 | Task 2: decision record file exists and is complete |
| AC-6 | Task 3: app launches, template count matches expected |

## Definition of Done

- Decision record committed at `decisions/0001-template-ownership-split.md`
- Every bundled template has a clear owner
- Template loading still works — no regressions

## Notes

- Most templates are prompt-optimization focused (code review, research, analysis). The likely outcome is: all or nearly all stay with the prompt app, and the espanso app either bundles a small subset or starts with zero bundled templates (user creates their own).
- The `_meta/` templates (`template_generator.json`, `template_improver.json`) are exclusively prompt-app assets — they power the AI generation/improvement features.
- This phase can run in parallel with Phase 2 or Phase 3 since it's primarily a documentation task.

## Session Log

<!-- Append after each session: date, completed, blockers -->
