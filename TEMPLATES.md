# Template Authoring Guide

Templatr makes it easy to create, share, and reuse prompt templates. This guide covers the 3-step quick-create workflow, import/export, and advanced editing.

---

## Quick-Create: 3 Steps to a New Template

### 1. Type `/new`

Open the chat and type `/new` to start the template creation flow.

### 2. Name it and paste your prompt

When prompted, provide a name for your template, then paste your prompt content. Use `{{variable_name}}` placeholders for any parts you want to fill in each time you use the template.

**Example:**

```
Summarize {{topic}} in {{num_sentences}} sentences, focusing on {{focus_area}}.
```

Templatr automatically detects `{{variables}}` in your content and creates input fields for them.

### 3. Use it with `/<name>`

Your new template is immediately available as a `/` command. Type `/` and start typing the template name to find it. If it has variables, an inline form will appear for you to fill in before sending.

---

## Import & Export

### Exporting Templates

Share your templates with others by exporting them as `.json` files:

- **Right-click** a template in the sidebar → **Export...**
- Or type `/export` in the chat to export the currently selected template

The exported file contains the template name, content, variables, and description — everything needed to recreate it.

### Importing Templates

Bring in templates from others:

- **Drag and drop** a `.json` template file onto the Templatr window
- Or type `/import` in the chat to open a file picker

If an imported template has the same name as an existing one, you'll be prompted to **rename**, **overwrite**, or **cancel**.

---

## Advanced Editing

For full control over template properties (name, description, folder, variables, refinements), right-click a template in the sidebar and choose **Advanced Edit**. This opens the complete template editor dialog.

The Advanced Edit dialog lets you:

- Set a description and trigger shortcut
- Organize templates into folders
- Define variables with custom labels, defaults, and multiline options
- Add refinement notes for AI-powered template improvement

---

## Template Format

Templates are stored as `.json` files with this structure:

```json
{
  "name": "My Template",
  "content": "Your prompt with {{variable}} placeholders",
  "description": "What this template does",
  "variables": [
    {
      "name": "variable",
      "label": "Variable",
      "default": "",
      "multiline": false
    }
  ]
}
```

The `name` and `content` fields are required. All other fields are optional.
