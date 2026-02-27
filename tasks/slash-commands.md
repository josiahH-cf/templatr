# Tasks: slash-commands

**Spec:** /specs/slash-commands.md

## Status

- Total: 3
- Complete: 0
- Remaining: 3

## Task List

### Task 1: Command palette widget

- **Files:** `templatr/ui/command_palette.py` (new), `tests/test_command_palette.py` (new)
- **Done when:** `CommandPalette` is a popup widget that displays a filterable list of items (name, description, folder). Supports keyboard navigation (arrow keys, Enter, Escape). Appears anchored above a parent widget. Filters results as text input changes. Appears within 100 ms of activation.
- **Criteria covered:** Criterion 1 (filterable popup), Criterion 2 (real-time filtering)
- **Status:** [ ] Not started

### Task 2: Chat input interception and template search

- **Files:** `templatr/ui/chat_widget.py` (keypress interception), `templatr/core/templates.py` (add `search_templates(query)` method)
- **Done when:** Typing `/` as the first character in the chat input opens the command palette populated with all templates. Subsequent keystrokes filter the list via substring match on template name. `TemplateManager.search_templates(query)` returns matching templates ranked by relevance (exact prefix match first, then substring). The palette dismisses on Escape or clicking outside.
- **Criteria covered:** Criterion 1 (typing `/` opens palette), Criterion 2 (real-time filter), Criterion 6 (trigger shortcuts also work)
- **Status:** [ ] Not started

### Task 3: Variable fill flow and system commands

- **Files:** `templatr/ui/chat_widget.py` (variable form integration), `templatr/ui/variable_form.py` (compact inline variant)
- **Done when:** Selecting a template from the palette displays its variables as a compact inline form in the chat input area (or sequential prompts). Pressing Enter with all fields filled submits the rendered template to the LLM. `/help` shows available system commands. Templates with a `trigger` field can be invoked by that shortcut.
- **Criteria covered:** Criterion 3 (variable fill), Criterion 4 (Enter submits), Criterion 5 (/help command), Criterion 6 (trigger shortcuts)
- **Status:** [ ] Not started

## Test Strategy

| Criterion | Tested in Task |
|-----------|---------------|
| 1. / opens filterable palette | Task 1 + Task 2 (test: type `/`, verify palette visible with template list) |
| 2. Real-time filtering | Task 1 + Task 2 (test: type `/code`, verify only code-related templates shown) |
| 3. Variable fill on selection | Task 3 (test: select template with variables, verify form fields appear) |
| 4. Enter submits | Task 3 (test: fill variables, press Enter, verify generation starts) |
| 5. /help shows commands | Task 3 (test: type `/help`, verify system command list displayed) |
| 6. Trigger shortcuts | Task 2 + Task 3 (test: type `:code_review`, verify same behavior as `/code_review`) |

## Session Log

<!-- Append after each session: date, completed, blockers -->
