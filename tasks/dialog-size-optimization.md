# Tasks: dialog-size-optimization

**Spec:** /tasks/roadmap-v1.1.md (Backlog: Dialog Size Optimization)

## Status

- Total: 4
- Complete: 4
- Remaining: 0

## Task List

### Task 1: Define and test shared dialog utility behavior

- **Files:** New `templatr/ui/template_dialog_utils.py`, new `tests/test_template_dialog_utils.py`
- **Done when:** Shared helper functions cover response-tag extraction, markdown fence cleanup, and connection-error detection used by both generate/improve flows.
- **Criteria covered:** Shared behavior consistency
- **Status:** [x] Complete

### Task 2: Extract shared AI worker logic

- **Files:** New `templatr/ui/template_ai_workers.py`, `templatr/ui/template_generate.py`, `templatr/ui/template_improve.py`
- **Done when:** Retry + extraction logic is defined once and consumed by generation/improvement workers without behavior regressions.
- **Criteria covered:** Reduced duplication and maintainability
- **Status:** [x] Complete

### Task 3: Extract prompt editor dialogs into dedicated module

- **Files:** New `templatr/ui/template_prompt_editors.py`, `templatr/ui/template_generate.py`, `templatr/ui/template_improve.py`, `templatr/ui/_template_actions.py`
- **Done when:** Prompt editor classes are centralized and existing call-sites continue to work without functional changes.
- **Criteria covered:** Dialog module size reduction
- **Status:** [x] Complete

### Task 4: Final slim-down and verification

- **Files:** `templatr/ui/template_generate.py`, `templatr/ui/template_improve.py`
- **Done when:** `template_generate.py` and `template_improve.py` are each under 300 lines, `ruff check .` passes, and full test suite passes.
- **Criteria covered:** Backlog item completion
- **Status:** [x] Complete

## Session Log

- 2026-02-28: Branch created and implementation started.
- 2026-02-28: Extracted shared dialog utilities/workers/prompt-editors, reduced dialog modules to 284 and 222 lines, added utility tests, and verified with `ruff check .` + `pytest` (365 passed).
