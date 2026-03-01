# Tasks: Template Marketplace

**Spec:** /specs/template-marketplace.md

## Status

- Total: 5
- Complete: 5
- Remaining: 0

## Prerequisite

Catalog repository: `josiahH-cf/templatr-catalog`
Default catalog URL: `https://raw.githubusercontent.com/josiahH-cf/templatr-catalog/main/catalog.json`

The catalog repo must be created separately before the feature is end-to-end testable. The app must handle the repo not existing yet (empty-state with guidance).

---

## Task List

### Task 1: Config + slash command registration + `/help` update

- **Files:**
  - `templatr/core/config.py` — add `catalog_url: str` to `AppConfig` with the default URL above
  - `templatr/ui/slash_input.py` — add `/browse` to `SYSTEM_COMMANDS` with payload `cmd:browse`; update the `/help` output string to document `/browse`
  - `templatr/ui/llm_settings.py` — add a catalog URL field to the LLM settings dialog (existing config dialog, not a new one)
- **Done when:** `/browse` appears in the command palette, `catalog_url` persists across restarts, the settings dialog lets users change the URL, and `/help` describes `/browse`.
- **Criteria covered:** AC-10, AC-11
- **Status:** [x] Complete

---

### Task 2: Background fetch worker

- **Files:**
  - `templatr/ui/workers.py` — add `CatalogFetchWorker(QThread)` that takes a URL, fetches it with `urllib.request`, parses JSON, and emits either `catalog_ready(list[dict])` or `error(str)`
- **Done when:** The worker fetches a valid catalog and emits the list; emits a human-readable error on network failure, timeout, non-200 status, invalid JSON, or empty body; entries missing required fields (`name`, `description`, `author`, `tags`, `download_url`, `version`) are skipped with a logged warning rather than crashing.
- **Criteria covered:** AC-2, AC-3, AC-9 (fetch side)
- **Status:** [x] Complete

---

### Task 3: Background install worker

- **Files:**
  - `templatr/ui/workers.py` — add `CatalogInstallWorker(QThread)` that takes a `download_url` and the `TemplateManager`; downloads the template JSON, calls `Template.from_dict`, saves via `TemplateManager`, uses the existing name-conflict resolution flow; emits `installed(template_name)` or `error(str)`
- **Done when:** The worker downloads a well-formed template and saves it to the user's template directory; name conflicts are resolved the same way `/import` resolves them; network and validation errors emit a readable message.
- **Criteria covered:** AC-7, AC-9 (install side)
- **Status:** [x] Complete

---

### Task 4: Catalog browser dialog

- **Files:**
  - `templatr/ui/catalog_browser.py` — new file; `CatalogBrowserDialog(QDialog)` with:
    - Loading spinner / status label while fetch runs
    - Search `QLineEdit` filtering by name, description, author, tags (case-insensitive, real-time)
    - Tag filter `QComboBox` (populated from fetched catalog)
    - `QListWidget` of matching entries
    - Detail/preview pane (name, description, author, tags, version)
    - Install `QPushButton`; disabled until an entry is selected and not already installing
    - Empty-state message when catalog is unreachable or has no entries, with text directing to catalog repo setup guidance
    - Emits `template_installed(str)` signal after a successful install
- **Done when:** All UI controls work correctly against a sample catalog JSON; search and tag filter reduce the list in real-time; install triggers the worker and shows in-progress state; completion emits the signal; errors show in a `QMessageBox`; dialog closes cleanly.
- **Criteria covered:** AC-1, AC-2, AC-4, AC-5, AC-6, AC-8, AC-9 (UI)
- **Status:** [x] Complete

---

### Task 5: Main-window wiring + README

- **Files:**
  - `templatr/ui/_template_actions.py` — handle `cmd:browse` in the command dispatch; open `CatalogBrowserDialog`; connect `template_installed` signal to `template_tree_widget.refresh()` and a `status_bar.showMessage()` confirmation
  - `README.md` — add a "Template Marketplace" section covering: what the catalog is, how to use `/browse`, how to contribute a template (fork + PR to the catalog repo), and how to host a private catalog (point the catalog URL to any raw JSON endpoint)
- **Done when:** Typing `/browse` and executing it opens the dialog from the main window; after install the tree refreshes and a status message confirms; README section is accurate and complete.
- **Criteria covered:** AC-1, AC-8, AC-12
- **Status:** [x] Complete

---

## Test Strategy

| Criterion | Task | Test approach |
|-----------|------|---------------|
| AC-1 `/browse` opens dialog | 5 | `pytest-qt`: dispatch `cmd:browse`, assert `CatalogBrowserDialog` visible |
| AC-2 Background fetch | 2 | Unit: mock `urlopen`, assert worker signals |
| AC-3 Catalog schema | 2 | Unit: feed worker entries with/without required fields, assert skips |
| AC-4 Search filter | 4 | Widget test: set search text, assert list row count |
| AC-5 Tag filter | 4 | Widget test: select tag, assert filtered entries |
| AC-6 Preview pane | 4 | Widget test: click entry, assert detail pane text |
| AC-7 Install action | 3 | Unit: mock download + manager, assert template saved |
| AC-8 Tree refresh | 5 | `pytest-qt`: mock worker complete, assert `refresh()` called |
| AC-9 Error messages | 2,3 | Unit: mock failures, assert error signal text is non-empty |
| AC-10 Config URL | 1 | Unit: change config URL, assert `CatalogFetchWorker` receives it |
| AC-11 `/help` | 1 | Unit: assert `/browse` in help output string |

---

## Catalog Repo Checklist (separate from app code)

These are not app-code tasks; track them separately once work begins:

- [x] Create `josiahH-cf/templatr-catalog` on GitHub
- [x] Add `catalog.json` (initially an empty array `[]`)
- [x] Add individual template JSON files (3 starter templates)
- [x] Add `README.md` (catalog format, how to submit, how to validate)
- [x] Add `CONTRIBUTING.md`
- [x] Add a GitHub Action or script to regenerate `catalog.json` from the template files directory

---

## Deferred: Catalog Content Seeding

The app feature is complete. Seeding the catalog with 10–15 quality templates is a
separate, deferred task — **not a code task, not tracked on the roadmap**.

When you're ready:
- See [tasks/seed-catalog-meta-prompt.md](seed-catalog-meta-prompt.md) for the meta-prompt and end-to-end testing checklist.
- That file is self-contained. Open the `templatr-catalog` repo in VS Code, paste the prompt, follow the checklist.

---

## Session Log

<!-- Append after each session: date, completed, blockers -->

- 2026-03-01: Task plan created. Branch: `feat/template-marketplace`. Catalog repo confirmed: `josiahH-cf/templatr-catalog`.
- 2026-03-01: All 5 tasks implemented. Catalog repo scaffolded and pushed to GitHub with 3 starter templates, CI, README, CONTRIBUTING, and generation script. App changes: `Config.catalog_url`, `/browse` slash command, `LLMSettingsDialog` catalog URL field, `CatalogFetchWorker`, `CatalogInstallWorker`, `CatalogBrowserDialog`, main-window wiring via `TemplateActionsMixin._open_catalog_browser`, README marketplace section. 28 new tests — all passing (412/413 full suite pass; 1 pre-existing doc-link failure unrelated to this feature).
