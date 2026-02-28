# Contributing to Templatr

Thank you for your interest in contributing! This guide covers developer setup, testing, and PR expectations.

---

## Developer Setup

### Prerequisites

- Python 3.10 or newer
- Git
- Linux or macOS (native Windows is not supported for development — use [WSL2](https://learn.microsoft.com/en-us/windows/wsl/install))

### Install from Source

```bash
git clone https://github.com/josiahH-cf/templatr.git
cd templatr
pip install -e .[dev]
```

This installs Templatr in editable mode along with development dependencies (pytest, pytest-qt, black, ruff).

> **Known issue:** `pip install -e .` does not seed templates into your config directory. After installing, you need to manually copy the bundled templates:
>
> **Linux / WSL2:**
> ```bash
> mkdir -p ~/.config/templatr/templates
> cp templates/*.json ~/.config/templatr/templates/
> ```
>
> **macOS:**
> ```bash
> mkdir -p ~/Library/Application\ Support/templatr/templates
> cp templates/*.json ~/Library/Application\ Support/templatr/templates/
> ```
>
> This workaround will be removed when first-run template seeding is added (see [platform-config-consolidation](specs/platform-config-consolidation.md)).

Alternatively, `./install.sh` handles template copying automatically but is more opinionated about the Python environment (virtual env in `.venv/`).

---

## Running the App

```bash
# If you used install.sh:
templatr

# If you used pip install -e .:
python -m templatr
```

---

## Testing

Run the full test suite before every commit:

```bash
pytest
```

Run a single test:

```bash
pytest tests/test_config.py::test_get_config_dir
```

### Testing Conventions

- Tests live in `/tests/` using `test_*.py` naming
- Use `pytest-qt` for UI widget tests
- Each acceptance criterion requires at least one test
- Tests must be deterministic — no flaky tests
- Do not modify existing tests to accommodate new code — fix the implementation

---

## Linting and Formatting

```bash
# Lint
ruff check .

# Format
black .
```

Both must pass cleanly before submitting a PR. CI enforces `ruff check .` automatically.

---

## Template Authoring

See [TEMPLATES.md](TEMPLATES.md) for the full guide on creating, importing, and exporting templates. Key points:

- Type `/new` in the chat to quick-create a template
- Use `{{variable_name}}` for fill-in-the-blank placeholders
- Templates are stored as `.json` files
- Right-click a template in the sidebar for import/export options

---

## Pull Request Guidelines

- **One logical change per PR** — keep diffs under 300 lines
- **Link to the spec** in `/specs/` if one exists
- **State what changed, why, and how to verify** in the PR description
- **All CI checks must pass** before requesting review
- **Tests cover every acceptance criterion** in the linked spec
- **No unrelated changes** in the diff

### Branch Naming

```
[type]/[issue-id]-[slug]
```

Examples: `feat/42-user-auth`, `fix/87-null-check`, `docs/readme-update`

---

## Commit Conventions

- Present-tense imperative subject line, under 72 characters
- One logical change per commit
- Reference the spec or task file in the commit body when applicable

Example:
```
Add per-OS troubleshooting guides

Spec: /specs/documentation-overhaul.md
Task: /tasks/documentation-overhaul.md (Task 2)
```

---

## Project Architecture

| Directory | Purpose |
|-----------|---------|
| `templatr/` | Main Python package |
| `templatr/core/` | Config, templates, logging, interfaces |
| `templatr/integrations/` | LLM runtime (llama.cpp) |
| `templatr/ui/` | PyQt6 user interface widgets |
| `templates/` | Built-in prompt template JSON files |
| `tests/` | Test suite |
| `scripts/` | Utility scripts |
| `specs/` | Feature specifications |
| `tasks/` | Execution plans |
| `decisions/` | Architecture decision records |

See [AGENTS.md](AGENTS.md) for the full architecture description and project conventions.

---

## Code of Conduct

Be respectful and constructive. We're building something useful together.
