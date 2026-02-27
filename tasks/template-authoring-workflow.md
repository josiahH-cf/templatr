# Tasks: template-authoring-workflow

**Spec:** /specs/template-authoring-workflow.md

## Status

- Total: 3
- Complete: 0
- Remaining: 3

## Task List

### Task 1: /new quick-create flow with auto-detect variables

- **Files:** `templatr/core/templates.py` (add `auto_detect_variables(content)` function), `templatr/ui/chat_widget.py` (handle `/new` command — conversational flow)
- **Done when:** Typing `/new` starts a conversational flow in the chat: asks for name → asks for content → auto-detects `{{variables}}` → confirms → saves template. Template is immediately available as a `/` command. `auto_detect_variables()` finds all `{{word}}` patterns and returns a list of variable dicts.
- **Criteria covered:** Criterion 1 (/new quick-create with auto-detect)
- **Status:** [ ] Not started

### Task 2: Import/export functionality

- **Files:** `templatr/core/templates.py` (add `export_template(name, path)` and `import_template(path)` methods), `templatr/ui/template_tree.py` (right-click "Export" menu item), `templatr/ui/chat_widget.py` (handle `/import` and `/export` commands), `templatr/ui/main_window.py` (drag-and-drop handler)
- **Done when:** Export writes a clean `.json` file (no internal `_path` field). Import reads, validates (requires `name` + `content` fields), checks for name conflicts (prompt: rename/overwrite/cancel), then saves. Drag-and-drop of `.json` files onto the app window triggers import. `/export <name>` opens a save dialog; `/import` opens a file picker.
- **Criteria covered:** Criterion 2 (export), Criterion 3 (import + drag-and-drop), Criterion 5 (conflict handling)
- **Status:** [ ] Not started

### Task 3: Documentation and advanced edit preservation

- **Files:** `TEMPLATES.md` (new — or new section in README.md), `templatr/ui/template_tree.py` (rename "Edit" to "Advanced Edit" in context menu)
- **Done when:** `TEMPLATES.md` documents the 3-step workflow: (1) type `/new`, (2) name it and paste content with `{{variables}}`, (3) use it with `/<name>`. The full template editor (name, description, folder, variables, refinements) is accessible via right-click → "Advanced Edit" for power users.
- **Criteria covered:** Criterion 4 (documentation), Criterion 6 (advanced edit preserved)
- **Status:** [ ] Not started

## Test Strategy

| Criterion | Tested in Task |
|-----------|---------------|
| 1. /new quick-create | Task 1 (test: simulate /new flow, verify template saved and available) |
| 2. Export | Task 2 (test: export template, verify .json file structure, no _path field) |
| 3. Import + drag-and-drop | Task 2 (test: import valid .json → saved; import invalid → rejected with error; drag-and-drop triggers import) |
| 4. Documentation | Task 3 (test: verify TEMPLATES.md exists and contains the 3-step workflow) |
| 5. Conflict handling | Task 2 (test: import template with existing name → prompt appears with rename/overwrite/cancel) |
| 6. Advanced Edit | Task 3 (test: right-click template → verify "Advanced Edit" menu item exists and opens editor) |

## Session Log

<!-- Append after each session: date, completed, blockers -->
