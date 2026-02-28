# Feature: Slash Commands

## Description

Add a `/` command system to the chat input so users can discover and invoke templates by typing `/` followed by a search term. This replaces the need to browse the template tree for common interactions and makes template discovery natural — like Discord, Slack, or ChatGPT's interface.

## Acceptance Criteria

- [ ] Typing `/` in the chat input opens a filterable popup palette listing all available templates by name and folder
- [ ] The palette filters results in real-time as the user continues typing after `/` (fuzzy or substring match on template name)
- [ ] Selecting a template from the palette displays the template's variables as fillable fields (inline compact form or sequential prompts in the chat)
- [ ] Pressing Enter (or a "Submit" button) with all variables filled submits the rendered template to the LLM and shows the response in the chat thread
- [ ] `/help` displays available system commands: `/help`, `/new`, `/import`, `/export`, `/settings`
- [ ] Templates with a `trigger` field (e.g., `:code_review`) are also invocable by their trigger shortcut (typing `:code_review` triggers the same as `/code_review`)

## Affected Areas

- New: `templatr/ui/command_palette.py`
- Modified: `templatr/ui/chat_widget.py` (input interception for `/` prefix)
- Modified: `templatr/core/templates.py` (add a search/filter method returning ranked matches)
- Modified: `templatr/ui/variable_form.py` (create a compact inline variant for use within chat flow)

## Constraints

- Palette must appear within 100 ms of typing `/`
- Filtering must handle 50+ templates without visible lag
- Must be fully keyboard-navigable (arrow keys to select, Enter to confirm, Escape to dismiss)
- Palette positioning: anchored above the input area, not floating at screen center

## Out of Scope

- Custom user-defined system commands beyond the built-in set (`/help`, `/new`, `/import`, `/export`, `/settings`)
- Plugin system for third-party commands
- Natural language template matching (e.g., "review my code" auto-selecting the code_review template)
- Command aliases or remapping

## Dependencies

- Spec: `chat-ui-core` — slash commands operate within the chat input widget

## Note: Partial implementation in chat-ui-core

The core slash-command mechanism (typing `/` to open a filterable template palette,
inline variable form, keyboard navigation) was implemented as part of `chat-ui-core`
in `templatr/ui/slash_input.py`. The remaining work for this spec is:

- `/help` system command showing available commands
- Template `trigger` field shortcut (`:code_review` syntax)
- Enhanced palette UI: description, folder badge, recently-used at top

## Notes

- UX reference: VSCode's command palette (`Ctrl+Shift+P`) — compact, filterable, keyboard-driven.
- The palette should display: template name (bold), description (truncated, gray), and folder (badge/tag).
- Consider showing recently-used templates at the top of the unfiltered list for quick access.
- The `trigger` field on templates (e.g., `:shortcut`) maps naturally to this system — typing the trigger with the `:` prefix acts identically to the `/` prefix version.
- Implementation approach: intercept `keyPressEvent` on the chat input. When `/` is the first character (or follows a newline), show the palette. On each subsequent keystroke, filter. On Enter, insert the selected template's variable form.
