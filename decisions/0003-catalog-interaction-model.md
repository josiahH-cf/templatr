# Decision: Catalog Repository Interaction Model

**Status:** Accepted  
**Date:** 2026-03-01  
**Feature:** Template Marketplace (specs/template-marketplace.md)

---

## Context

The catalog feature requires two separate systems to work together: the Templatr app (this repo) and an independently managed catalog repository (`josiahH-cf/templatr-catalog`). This record documents how they interact, what each side owns, and what must be true for each to function correctly.

---

## The Two Sides

### App side (this repo)

Reads the catalog. Never writes to it.

Key touchpoints:
- `Config.catalog_url` — the URL the app fetches from. Defaults to the community catalog. User-overridable in `/settings`.
- `CatalogFetchWorker` — downloads `catalog.json`, validates entries (skips incomplete ones), emits the list.
- `CatalogInstallWorker` — downloads a single template JSON from `download_url`, runs it through `TemplateManager.import_template` for validation, saves it.
- `CatalogBrowserDialog` — the UI. Opens on `/browse`. Stateless: closes and re-fetches on next open.

**The app has no awareness of the catalog repo's internals.** It only cares about:
1. A URL that returns a valid JSON array.
2. `download_url` fields that return valid template JSON.

### Catalog repo (`josiahH-cf/templatr-catalog`)

Owns the content. The app is just a client.

Required to be functional:

| File/Path | Purpose | Critical? |
|---|---|---|
| `catalog.json` | The index the app fetches. Must be a valid JSON array at the raw GitHub URL. | Yes — without this, `/browse` shows an empty state. |
| `templates/*.json` | Individual template files. Must be valid Templatr templates (`name` + `content` required). | Yes — broken `download_url` causes per-entry install errors. |
| `templates/*.meta.json` | Catalog metadata sidecars (description, author, tags, version). Used by the generation script only. | Only needed if you use the CI auto-generation. |
| `scripts/generate_catalog.py` | Regenerates `catalog.json` from template + meta files. | Recommended — keeps the index in sync automatically. |
| `.github/workflows/update-catalog.yml` | Validates on PR; regenerates on push to `main`. | Recommended — automation of the above. |
| `README.md` | Explains the catalog format, contribution process, and private hosting. | Yes — this is the contributor's onboarding doc. |
| `CONTRIBUTING.md` | PR checklist and quality standards. | Yes |

---

## Contribution Flow (catalog repo)

```
contributor
  └─ forks josiahH-cf/templatr-catalog
  └─ adds templates/my_template.json       (clean template — this is what users download)
  └─ adds templates/my_template.meta.json  (catalog metadata — stays in the repo, never downloaded by users)
  └─ opens PR
        └─ CI validates catalog.json schema
  └─ merged to main
        └─ CI regenerates catalog.json automatically
```

**Why the sidecar pattern?**  
The template JSON that users download via `/browse` should be clean — identical to what they'd get with `/import`. Catalog metadata (author, tags, version) doesn't belong in the template itself. The `.meta.json` sidecar keeps concerns separated: the template file is portable and self-contained; the catalog metadata only lives in the catalog repo.

**Manual catalog.json edits will be overwritten by CI.** Do not maintain catalog.json by hand — use the sidecar pattern and let CI regenerate it.

---

## What Can Break (and How It's Handled)

| Failure | User experience |
|---|---|
| catalog repo doesn't exist / URL 404 | Empty state with setup guidance text + URL to catalog repo |
| catalog.json is malformed JSON | Error message in the dialog (non-crash) |
| An entry is missing required fields | Entry silently skipped; rest of catalog loads |
| A `download_url` 404s at install time | Install error message in a `QMessageBox` |
| No internet connection | URLError → readable message in dialog |
| Name collision on install | Standard conflict-resolution dialog (same as `/import`) |

---

## What Is NOT in Scope for the App

- Writing to the catalog repo from within the app (publishing is always via PR).
- Checking if an installed template is out of date vs the catalog version.
- Rating, reviewing, or tracking download counts (requires a backend).
- Authenticated catalog URLs (may work transparently but not tested).

These are intentionally deferred. The current design is deliberately minimal — a static JSON file over raw GitHub is zero infrastructure.

---

## Private / Internal Catalogs

Any URL that serves a valid JSON array in the catalog format works. To host a private catalog:

1. Fork `josiahH-cf/templatr-catalog` (or create a repo with the same structure).
2. Change the Catalog URL in `/settings` to the raw URL of your `catalog.json`.
3. The repo can be private if the raw URL is accessible with appropriate auth — though this isn't explicitly tested.

Typical use cases: company-internal prompt libraries, team collections, curated personal sets.

---

## Open Questions / Future Work

- **Caching:** Currently, `/browse` always refetches. A TTL cache (e.g., 10 minutes, persisted to disk) would improve responsiveness for users on slow connections.
- **Version awareness:** The app installs the latest version from the catalog but doesn't track which version is installed. Adding installed-version tracking would enable "update available" notifications.
- **Contributor tooling:** A `validate_template.py` script in the catalog repo that contributors can run locally before opening a PR would reduce CI round-trips.
