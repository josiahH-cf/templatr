# Tasks: incremental-decoupling

**Spec:** /specs/incremental-decoupling.md

## Status

- Total: 3
- Complete: 0
- Remaining: 3

## Task List

### Task 1: Protocol interfaces

- **Files:** `templatr/core/interfaces.py` (new)
- **Done when:** Protocol classes exist for `ConfigManagerProtocol`, `TemplateManagerProtocol`, `LLMClientProtocol`, and `LLMServerProtocol`. Each Protocol documents the public methods and their signatures. All existing concrete classes satisfy their Protocol (verified by type checker or runtime test with `isinstance` + `runtime_checkable`).
- **Criteria covered:** Criterion 1 (Protocol interfaces)
- **Status:** [ ] Not started

### Task 2: Circular import fix and singleton reset

- **Files:** `templatr/core/meta_templates.py` (new — extracted from templates.py), `templatr/core/feedback.py` (import from meta_templates instead of templates), `templatr/core/templates.py` (remove load_meta_template or re-export from meta_templates), `templatr/core/config.py` (add reset), `templatr/integrations/llm.py` (add reset)
- **Done when:** No function-level or deferred imports exist between `feedback.py` and `templates.py`. `load_meta_template()` lives in `meta_templates.py`. Every singleton module has a `reset()` function that clears its `_instance`. All existing tests pass without modification.
- **Criteria covered:** Criterion 2 (circular import eliminated), Criterion 3 (singleton reset), Criterion 5 (tests pass unchanged)
- **Status:** [ ] Not started

### Task 3: Constructor injection and mixin documentation

- **Files:** `templatr/ui/main_window.py` (add optional constructor params), `templatr/ui/_template_actions.py` (docstring), `templatr/ui/_generation.py` (docstring), `templatr/ui/_window_state.py` (docstring)
- **Done when:** `MainWindow.__init__` accepts optional `config`, `templates`, `llm` parameters that default to calling the global singletons. Tests can pass mock objects without patching. Each mixin class has a docstring listing every attribute and method it expects on `self`. All existing tests pass without modification.
- **Criteria covered:** Criterion 4 (constructor injection), Criterion 5 (tests pass unchanged), Criterion 6 (mixin docstrings)
- **Status:** [ ] Not started

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
