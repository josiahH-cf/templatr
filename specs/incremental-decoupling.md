# Feature: Incremental Decoupling

## Description

Incrementally decouple the codebase by extracting Protocol interfaces, breaking the circular import between `feedback` and `templates`, and adding constructor injection with a testing reset mechanism. This is **not** a big-bang rewrite — it's targeted surgery on the 3 specific coupling points that make the code hardest to test and extend: circular imports, untestable singletons, and undocumented mixin contracts.

## Acceptance Criteria

- [ ] Protocol classes (abstract interfaces) exist for `ConfigManager`, `TemplateManager`, `LLMClient`, and `LLMServer` in a new `templatr/core/interfaces.py`, each documenting the public contract
- [ ] The circular import between `templatr/core/feedback.py` and `templatr/core/templates.py` is eliminated — no function-level or deferred imports between them
- [ ] Each global singleton (`get_config_manager`, `get_template_manager`, `get_llm_client`, `get_llm_server`, `get_feedback_manager`) supports a `reset()` call that clears the cached instance, enabling clean test isolation
- [ ] `MainWindow.__init__` accepts optional dependency parameters (config, templates, LLM) with defaults that call the current singletons — preserving backward-compatible construction
- [ ] All existing tests pass without modification after the refactor (no test changes to accommodate structural changes)
- [ ] Each mixin class (`TemplateActionsMixin`, `GenerationMixin`, `WindowStateMixin`) has a docstring listing the attributes and methods it expects on `self`

## Affected Areas

- New: `templatr/core/interfaces.py`
- Modified: `templatr/core/config.py`, `templatr/core/templates.py`, `templatr/core/feedback.py` (singleton reset, circular import fix)
- Modified: `templatr/integrations/llm.py` (singleton reset for client and server)
- Modified: `templatr/ui/main_window.py` (constructor injection with defaults)
- Modified: `templatr/ui/_template_actions.py`, `templatr/ui/_generation.py`, `templatr/ui/_window_state.py` (mixin docstrings)

## Constraints

- **All changes must be backward-compatible** — existing code calling `get_config_manager()` works identically
- No new dependencies — Protocol classes use `typing.Protocol` (stdlib since Python 3.8)
- No behavior changes — this is a structural refactor only, no feature additions
- The `reset()` functions are for testing only — document this clearly

## Out of Scope

- Full dependency injection framework (e.g., `injector`, `python-inject`)
- Plugin system or dynamic component loading
- Microservices decomposition
- Breaking the package into multiple packages
- Event bus or message broker patterns

## Dependencies

- Should be scheduled after Phase C (UI work) to avoid merge conflicts, or before Phase C if UI work is delayed. The ordering is flexible — this spec has no hard blockers.

## Notes

- Protocol classes are `typing.Protocol` — zero runtime cost, used for type checking and as living documentation of the public contract. They don't require implementations to inherit from them.
- Circular import fix strategy: extract `load_meta_template()` from `templates.py` into a small `templatr/core/meta_templates.py` module that both `feedback.py` and `templates.py` can import without cycles.
- Singleton reset is trivial: each module already has `_instance: Optional[T] = None`; add a `def reset() -> None: global _instance; _instance = None` function.
- Constructor injection for `MainWindow`: `def __init__(self, config=None, templates=None, llm=None)` where `None` means "use the global singleton." This lets tests pass mocks without patching.
- The mixin docstring format: `"""Expects self to provide: self.template_tree (TemplateTreeWidget), self.output_pane (OutputPaneWidget), ..."""`
