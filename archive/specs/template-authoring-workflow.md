# Feature: Template Authoring Workflow

## Description

Make template creation, editing, sharing, and importing trivially easy. Define and document a clear 3-step user-facing workflow for "I want a new command." Add import/export so users can share templates as files without needing a marketplace or repository.

## Acceptance Criteria

- [ ] A `/new` command in the chat opens an inline quick-create flow: user provides a name → pastes prompt content → variables are auto-detected from `{{placeholder}}` patterns → template is saved and immediately available as a `/` command
- [ ] Templates can be exported as a single `.json` file via right-click → "Export" in the sidebar or via a `/export <name>` command
- [ ] Templates can be imported from a `.json` file via drag-and-drop onto the app window or via a `/import` command that opens a file picker
- [ ] A `TEMPLATES.md` guide (or a README section) documents the 3-step workflow: (1) type `/new`, (2) name it and paste your prompt with `{{variables}}`, (3) use it with `/<name>`
- [ ] Imported templates that conflict with an existing name prompt the user to rename, overwrite, or cancel
- [ ] The existing full template editor (name, description, folder, variables, refinements) remains accessible via right-click → "Advanced Edit" for power users

## Affected Areas

- Modified: `templatr/core/templates.py` (add `import_template()`, `export_template()` methods; add `auto_detect_variables()` utility)
- Modified: `templatr/ui/chat_widget.py` (handle `/new`, `/import`, `/export` commands)
- Modified: `templatr/ui/template_tree.py` (right-click "Export" context menu item)
- Modified: `templatr/ui/main_window.py` (drag-and-drop handler for `.json` files)
- New: `TEMPLATES.md` (or new section in README.md)

## Constraints

- Import must validate JSON structure before saving — reject malformed files with a clear error message
- Export format is the existing template JSON format (no new format to maintain)
- Auto-detect only finds `{{word}}` patterns (regex: `\{\{(\w+)\}\}`) — no nested or conditional template syntax
- Drag-and-drop must filter to `.json` files only

## Out of Scope

- Template marketplace or community hub
- Import from URL (file-only for this spec; URL import is a fast follow-up)
- Bulk import/export of entire folders
- Template versioning on import (versions are created on edit, not on import)
- Syncing templates across devices

## Dependencies

- Spec: `slash-commands` — `/new`, `/import`, `/export` are slash commands

## Notes

- Auto-detect approach: scan content for `\{\{(\w+)\}\}`, deduplicate, create a variable entry for each unique match with the name as both the label and identifier, empty default value, `multiline: false`. This matches the existing simple `{{var}}` substitution engine.
- The `/new` flow can be conversational: the chat shows "What should this command be called?" → user types name → "Paste the prompt content (use {{variable_name}} for placeholders):" → user pastes → "Found variables: topic, context. Saved as /my_template!" → done.
- Export writes the same JSON format that `save_template()` produces, minus internal fields like `_path`.
- Import reads, validates (`name` and `content` fields required), checks for name conflict, then calls `save_template()`.
