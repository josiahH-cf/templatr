# Tasks: incremental-decoupling

**Spec:** /specs/incremental-decoupling.md

## Status

- Total: 3
- Complete: 3
- Remaining: 0

## Task List

### Task 1: Protocol interfaces

- **Files:** `templatr/core/interfaces.py` (new)
- **Done when:** Protocol classes exist for `ConfigManagerProtocol`, `TemplateManagerProtocol`, `LLMClientProtocol`, and `LLMServerProtocol`. Each Protocol documents the public methods and their signatures. All existing concrete classes satisfy their Protocol (verified by type checker or runtime test with `isinstance` + `runtime_checkable`).
- **Criteria covered:** Criterion 1 (Protocol interfaces)
- **Status:** [x] Complete

### Task 2: Circular import fix and singleton reset

- **Files:** `templatr/core/meta_templates.py` (new — extracted from templates.py), `templatr/core/feedback.py` (import from meta_templates instead of templates), `templatr/core/templates.py` (remove load_meta_template or re-export from meta_templates), `templatr/core/config.py` (add reset), `templatr/integrations/llm.py` (add reset)
- **Done when:** No function-level or deferred imports exist between `feedback.py` and `templates.py`. `load_meta_template()` lives in `meta_templates.py`. Every singleton module has a `reset()` function that clears its `_instance`. All existing tests pass without modification.
- **Criteria covered:** Criterion 2 (circular import eliminated), Criterion 3 (singleton reset), Criterion 5 (tests pass unchanged)
- **Status:** [x] Complete

### Task 3: Constructor injection and mixin documentation

- **Files:** `templatr/ui/main_window.py` (add optional constructor params), `templatr/ui/_template_actions.py` (docstring), `templatr/ui/_generation.py` (docstring), `templatr/ui/_window_state.py` (docstring)
- **Done when:** `MainWindow.__init__` accepts optional `config`, `templates`, `llm` parameters that default to calling the global singletons. Tests can pass mock objects without patching. Each mixin class has a docstring listing every attribute and method it expects on `self`. All existing tests pass without modification.
- **Criteria covered:** Criterion 4 (constructor injection), Criterion 5 (tests pass unchanged), Criterion 6 (mixin docstrings)
- **Status:** [x] Complete

## Test Strategy

| Criterion | Tested in Task |
|-----------|---------------|
| 1. Protocol interfaces | Task 1 (test: verify Protocol classes exist; verify concrete classes satisfy them via runtime_checkable) |
| 2. Circular import eliminated | Task 2 (test: import feedback and templates in fresh interpreter, no ImportError; grep for deferred imports) |
| 3. Singleton reset | Task 2 (test: call get_config_manager(), then reset(), call again — verify fresh instance) |
| 4. Constructor injection | Task 3 (test: instantiate MainWindow with mock deps — verify it uses mocks, not singletons) |
| 5. Existing tests pass | Task 2 + Task 3 (full pytest suite) |
| 6. Mixin docstrings | Task 3 (test: verify each mixin class.__doc__ contains "Expects self to provide") |

## Session Log

<!-- Append after each session: date, completed, blockers -->

### 2026-02-27

- **Completed:** All 3 tasks (Protocol interfaces, circular import fix + reset, constructor injection + mixin docs)
- **Files changed:** `templatr/core/interfaces.py`, `templatr/core/meta_templates.py` (new), `templatr/core/feedback.py`, `templatr/core/templates.py`, `templatr/core/config.py`, `templatr/integrations/llm.py`, `templatr/ui/main_window.py`, `templatr/ui/_template_actions.py`, `templatr/ui/_generation.py`, `templatr/ui/_window_state.py`, `templatr/ui/template_improve.py`, `templatr/ui/template_generate.py`, `tests/test_interfaces.py`, `tests/test_decoupling.py`, `tests/conftest.py`
- **Approach:** Task 1 (Protocol interfaces) was already committed. Task 2 extracted `load_meta_template` and related functions into `meta_templates.py`, updated all import sites in feedback.py and UI files, added `reset()` to all 5 singleton modules, and added autouse conftest fixture for test isolation. Task 3 added optional dependency parameters to `MainWindow.__init__` with singleton defaults, and expanded all 3 mixin docstrings with complete attribute/type listings.
- **Surprises:** Decoupling tests that delete `sys.modules["templatr.core.*"]` to verify no circular imports caused stale module references — `FeedbackManager.__globals__` pointed to the old module dict while `patch()` targeted the new one. Fixed by saving/restoring `sys.modules` in those tests. Pre-existing feedback test failures (singleton leakage) were fixed by the new autouse `_reset_singletons` fixture.
- **Result:** 109 tests pass, zero lint errors, zero new dependencies.
