# Feature: Template Marketplace (Community Sharing)

## Description

Add a discoverable template catalog so users can browse, preview, and install community-contributed templates without leaving the app. The catalog is a static JSON index hosted on GitHub (no server infrastructure). Users can also publish their own templates by exporting and submitting a PR to the catalog repo. Inside the app, a new `/browse` command and "Browse Templates…" menu action open a dialog for searching and one-click installing catalog entries.

## Acceptance Criteria

- [ ] AC-1: A "Browse Templates…" action in the File menu opens the `TemplateCatalogDialog`.
- [ ] AC-2: The dialog fetches a JSON catalog index from a configurable URL (default: a raw GitHub URL under `josiahH-cf/templatr-catalog`). The fetch runs in a background `QThread`; a spinner or "Loading…" label is shown until complete.
- [ ] AC-3: The catalog index contains an array of entries, each with: `name`, `description`, `author`, `tags` (list of strings), `download_url` (raw JSON URL), and `version` (semver string).
- [ ] AC-4: A search field filters catalog entries in real-time by matching name, description, author, or tags (case-insensitive).
- [ ] AC-5: A tag filter dropdown lists all unique tags from the catalog. Selecting a tag restricts visible entries to those with that tag. "All Tags" shows everything.
- [ ] AC-6: Selecting a catalog entry shows its name, description, author, tags, and version in a detail pane.
- [ ] AC-7: An "Install" button downloads the template JSON from `download_url`, validates it via `TemplateManager.import_template()`, and saves it to the user's template directory. If a name conflict exists, the user is prompted to overwrite or rename (reusing the existing import-conflict flow in `_template_actions.py`).
- [ ] AC-8: After successful install, the template tree refreshes and a status message confirms the install.
- [ ] AC-9: A `/browse` slash command opens the same dialog.
- [ ] AC-10: If the catalog fetch fails (network error, invalid JSON), the dialog shows a human-readable error message with guidance ("Check your internet connection" or "Catalog format error") instead of crashing.
- [ ] AC-11: The catalog URL is configurable in `config.json` under `ui.catalog_url` so users can point to a private/forked catalog.
- [ ] AC-12: The dialog is ≤ 300 lines.

## Affected Areas

### Source files modified
- `templatr/core/config.py` — Add `catalog_url` field to `UIConfig` with default URL.
- `templatr/ui/main_window.py` — Add "Browse Templates…" menu action, wire `/browse` command, connect install signal to tree refresh.
- `templatr/ui/slash_input.py` — Register `/browse` in the command palette entries list.
- `templatr/ui/_template_actions.py` — Reuse `_handle_import_file` for catalog installs (may need a variant that accepts raw bytes/dict instead of a file path).

### New files
- `templatr/ui/template_catalog.py` — `TemplateCatalogDialog` (QDialog): search, tag filter, detail pane, install button. ≤ 300 lines.
- `templatr/ui/workers.py` — Add `CatalogFetchWorker(QThread)` that GETs the catalog index URL and emits the parsed list or an error string.
- `tests/test_template_catalog.py` — Unit tests covering AC-1 through AC-12 with mocked HTTP responses.

### External (not in this repo)
- New GitHub repo `josiahH-cf/templatr-catalog` with a `catalog.json` index and individual template JSON files. This is outside the scope of this spec but must exist before the feature is usable.

## Constraints

- Network requests use `requests` (already a dependency via llama.cpp client). No new HTTP dependencies.
- The catalog fetch must not block the UI thread — must run in a `QThread`.
- The catalog index is read-only from the app's perspective. Publishing is a manual PR workflow (documented in the catalog repo README), not an in-app feature.
- Catalog entries are validated client-side: missing required fields are skipped with a warning, not a crash.
- The dialog must gracefully handle an empty catalog (show "No templates available yet").
- Backward compatible: existing `config.json` without `catalog_url` uses the default.

## Out of Scope

- In-app template publishing or upload.
- Template ratings, reviews, or download counts (future work — requires a backend).
- Automatic template updates or version checking.
- Private/authenticated catalog URLs (HTTPS basic auth may work transparently via `requests`, but is not explicitly supported or tested).
- Creating the catalog repo itself (separate setup task).

## Dependencies

- `template-authoring-workflow` (complete) — `TemplateManager.import_template()` and the conflict-resolution UI in `_template_actions.py`.
- Network access to the catalog URL at runtime.

## Notes

- The catalog index format is intentionally simple (flat JSON array) to avoid needing a database or API server. Example:
  ```json
  [
    {
      "name": "Code Review",
      "description": "Thorough code review prompt with RAG context support",
      "author": "josiahH-cf",
      "tags": ["code", "review", "engineering"],
      "download_url": "https://raw.githubusercontent.com/josiahH-cf/templatr-catalog/main/templates/code_review.json",
      "version": "1.0.0"
    }
  ]
  ```
- The existing `_handle_import_file` in `_template_actions.py` expects a `Path`. For catalog installs, we'll either write to a temp file first or add a `_handle_import_data(data: dict)` variant that skips the file-read step.
- The `/browse` command follows the pattern established by `/history`, `/compare`, and other dialog-opening commands.
