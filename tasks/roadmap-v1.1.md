# Roadmap — Automatr Prompt v1.1

## Backlog

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

## Active

_No active work — ready for v1.1 planning._

## Completed

### v1.0.0 — Initial Release
- Template CRUD with JSON storage
- Variable substitution and prompt rendering
- llama.cpp integration (server lifecycle, model management)
- Decomposed UI (14 widgets extracted from monolithic MainWindow)
- 68 tests passing, zero lint errors
- CI/CD with GitHub Actions (Python 3.10–3.12)
- Dark/light theme support
