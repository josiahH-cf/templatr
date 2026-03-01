# Deferred Task: Seed templatr-catalog with Templates

> **STATUS: DEFERRED — do not surface as active development work**
>
> This is a content seeding task, not a code task. It has no bearing on the
> app's implementation status. The `/browse` feature is fully implemented and
> tested. This task only becomes relevant when you decide to populate the
> catalog with enough templates to make the feature compelling.
>
> **Do not include this in active sprint planning, roadmaps, or feature work.**
> Pick it up manually when you're ready to seed content.

---

## What This Is

The Templatr app's `/browse` command fetches its template list from the
`josiahH-cf/templatr-catalog` GitHub repo. The repo currently has 3 starter
templates. Before promoting the feature to users, seed it with 10–15 templates.

This task has two parts:

1. **Use the meta-prompt below** (in a Copilot session inside the catalog repo)
   to scaffold the template files — Copilot writes the prompts, you supply the ideas.
2. **Test the integration** end-to-end using the steps in "Testing Checklist" below.

---

## Prerequisites

- The `josiahH-cf/templatr-catalog` repo is live and accessible.
- The Templatr app is installed and runnable (`python -m templatr` or via the launcher).
- The 3 existing starter templates are already in the catalog:
  `Code Review Checklist`, `Decision Framework`, `Quick Research Summary`.

---

## Testing Checklist (run after seeding and pushing templates)

Work through these in order. Every step must pass before the feature is
considered ready to promote.

- [ ] **Catalog is live:** `curl -s "https://raw.githubusercontent.com/josiahH-cf/templatr-catalog/main/catalog.json" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d), 'entries')"` — should print 10 or more.
- [ ] **App opens:** `python -m templatr` launches without errors.
- [ ] **`/browse` opens dialog:** Type `/browse` in the command palette, press Enter — the catalog browser dialog should appear within ~2 seconds.
- [ ] **Templates load:** The list pane shows all seeded templates (not a spinner or empty state).
- [ ] **Search works:** Type a word in the search box — the list narrows correctly.
- [ ] **Tag filter works:** Select a tag from the dropdown — only matching templates remain.
- [ ] **Detail pane works:** Click any template — name, description, author, tags appear in the right pane.
- [ ] **Install works:** Click Install on any template — it appears in the sidebar tree and is selectable.
- [ ] **Name conflict works:** Install a template that already exists — the rename/overwrite dialog appears.
- [ ] **Custom catalog URL works:** Open `/settings`, change the Catalog URL to `https://example.com/nonexistent.json`, reopen `/browse` — an error message appears (not a crash).
- [ ] **Restore default URL:** Change the Catalog URL back to the default in `/settings`.

---

## Meta-Prompt (paste into Copilot inside the `templatr-catalog` repo)

Open the `templatr-catalog` repo in VS Code, open a Copilot Chat session, and
paste everything below the horizontal rule. Fill in your template list at the
bottom before pasting.

---

You are working in the `templatr-catalog` repository. This is a **community prompt template catalog** for the Templatr desktop app — an open-source local-model prompt optimizer. Your job is to scaffold new prompt templates into this repository using the exact file structure and formats described below.

---

### Repository file structure

```
catalog.json               ← the index file the app downloads; must stay valid JSON
templates/
  my_template.json         ← the template the user actually installs (portable, clean)
  my_template.meta.json    ← catalog metadata sidecar (stays in repo, never downloaded by users)
scripts/
  generate_catalog.py      ← regenerates catalog.json from all template + meta pairs
```

---

### File formats (use these exactly)

#### `templates/<slug>.json` — the installable template

```json
{
  "name": "Human-readable Template Name",
  "description": "One-sentence description of what this prompt does.",
  "trigger": ":optional_shortcut",
  "content": "The full prompt text. Use {{variable_name}} for user-fillable values.\nMultiple lines are fine — use \\n in JSON strings.",
  "variables": [
    {"name": "variable_name", "label": "Label shown in the UI", "multiline": false},
    {"name": "long_input",    "label": "Paste your text here",  "multiline": true}
  ]
}
```

Rules:
- `name` and `content` are **required**. All other fields are optional.
- `trigger` must start with `:` and be lowercase with no spaces (e.g. `:codereview`).
- `variables` is an array of objects with `name`, `label`, and `multiline` (boolean). Only include this key if the template actually uses `{{...}}` substitutions.
- `content` is a single JSON string. Use `\n` for line breaks. Markdown inside the content is fine.
- File slug (filename without `.json`) must be `snake_case`, all lowercase, no spaces.

#### `templates/<slug>.meta.json` — catalog sidecar (never downloaded by users)

```json
{
  "description": "One-sentence description (same as in the template file).",
  "author": "your-github-username",
  "tags": ["tag1", "tag2", "tag3"],
  "version": "1.0.0"
}
```

Rules:
- `tags` should be 2–4 lowercase strings from this suggested set:
  `research`, `writing`, `code`, `review`, `engineering`, `productivity`, `decision-making`,
  `strategy`, `planning`, `learning`, `analysis`, `communication`, `summarization`,
  `debugging`, `documentation`, `creativity`, `business`, `refactoring`
- Use your GitHub username for `author`, or `templatr-team` if contributing on behalf of the project.

#### `catalog.json` — the index (append new entries, keep array valid)

```json
[
  {
    "name": "Human-readable Template Name",
    "description": "One-sentence description.",
    "author": "github-username",
    "tags": ["tag1", "tag2"],
    "version": "1.0.0",
    "download_url": "https://raw.githubusercontent.com/josiahH-cf/templatr-catalog/main/templates/<slug>.json"
  }
]
```

Rules:
- `download_url` must point to the raw GitHub URL of the corresponding `.json` file (NOT the `.meta.json`).
- Append new entries to the existing array — do **not** overwrite existing entries.
- The array must remain valid JSON after your edits.

---

### What you must produce for each template

For each template the user gives you, create:

1. `templates/<slug>.json` — the full, well-written prompt template
2. `templates/<slug>.meta.json` — the catalog sidecar
3. An additional entry appended to `catalog.json`

The prompt content inside each template should be **immediately usable** — well-structured, specific enough to produce good LLM output, and clearly formatted with headings or steps where appropriate.

---

### Your process

1. **Read the user's template list below.**
2. **Before writing any files**, ask follow-up questions for any template where:
   - The name is ambiguous or could mean multiple different things
   - You are unsure what variables the user wants
   - The intended audience or use case is unclear
   - There aren't enough templates — the target is **10–15 total entries in `catalog.json`** (counting the 3 that already exist: `Code Review Checklist`, `Decision Framework`, `Quick Research Summary`). If the user provides fewer than 7 new ones, tell them how many more are needed and ask for suggestions.
3. **After questions are resolved**, scaffold all files in a single pass.
4. **Confirm** by listing every file you created and showing the final `catalog.json` array.

---

### Template list (fill this in before pasting)

```
<!-- Replace this block with your template names/ideas. One per line. -->
<!-- Examples of the format that works best:
     - "Lessons Learned" — extract key learnings from a project post-mortem
     - "Cold Email Draft" — write a concise outreach email given role + company + goal
     - "PR Description Writer" — given a git diff, write a clear PR title + body
     You don't need to write the full prompt — just the name + a sentence of intent.
     Copilot will write the actual prompt content.
-->
```

---

### Constraints

- Do **not** modify any file outside of `templates/` and `catalog.json`.
- Do **not** delete or overwrite existing template files.
- All template content must be in English.
- No prompt should be under 150 words — shallow prompts are not useful.
- No prompt should require external tools, APIs, or plugins to work — they must run with any text-based LLM.
