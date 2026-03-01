# Feature: Template Marketplace (Community Sharing)

## Description

Users can create excellent templates locally but have no way to discover what others have built or share their own. The built-in template library is static and only grows via app updates. This feature connects Templatr to a community template catalog — a simple, static JSON index hosted on GitHub — so users can browse, preview, and install community-contributed templates without leaving the app.

## Problem

- Discovery: new users don't know what good templates look like.
- Sharing: experienced users can't distribute their templates easily.
- Growth: the template ecosystem is limited to what ships with the app.

## Acceptance Criteria

- [x] AC-1: A `/browse` slash command opens a catalog browsing dialog.
- [x] AC-2: The dialog fetches a catalog index from a configurable URL. The fetch runs in the background; a loading state is shown until complete.
- [x] AC-3: The catalog is a JSON array where each entry has at minimum: `name`, `description`, `author`, `tags`, `download_url`, and `version`.
- [x] AC-4: A search field filters catalog entries in real-time by name, description, author, or tags (case-insensitive).
- [x] AC-5: A tag filter narrows entries to a selected tag or shows all.
- [x] AC-6: Selecting an entry shows its details in a preview pane.
- [x] AC-7: An install action downloads the template, validates it using the existing template import logic, saves it to the user's template directory, and handles name conflicts using the existing conflict-resolution flow.
- [x] AC-8: After install, the template tree refreshes and a confirmation message appears.
- [x] AC-9: Network errors and invalid catalog data produce human-readable error messages, not crashes.
- [x] AC-10: The catalog URL is user-configurable so users can point to their own catalog (e.g., a fork, a company-internal repo, or a personal collection).
- [x] AC-11: `/help` output is updated to document the `/browse` command.
- [x] AC-12: README is updated with: what the catalog is, how to browse, how to contribute a template, and how to host a private catalog.

## Prerequisite: Catalog Repository Setup

Before this feature is usable, a catalog repository must exist. This is a separate setup step, not part of the app code:

1. **The implementer must ask the user** for the GitHub org/user and repo name to use for the catalog (do not assume a hardcoded default). The app's default URL should point to wherever the user decides to host it.
2. The catalog repo should contain:
   - A `catalog.json` index file (flat JSON array of entries).
   - Individual template `.json` files matching the app's template format.
   - A `README.md` explaining: the catalog format, how to submit a template (fork + PR), and how to validate entries.
   - A `CONTRIBUTING.md` for the catalog repo.
3. The catalog repo structure should make it easy for contributors to add templates via PR: one JSON file per template, auto-generation of `catalog.json` from the directory listing (a simple script or GitHub Action).
4. The app should gracefully handle the catalog repo not existing yet (show an empty state with setup guidance).

## Constraints

- Network requests use the HTTP library already in the project — no new HTTP dependencies.
- The catalog fetch must not block the UI thread.
- The catalog is read-only from the app's perspective. Publishing is done via the catalog repo's PR process.
- Catalog entries with missing required fields are skipped with a warning, not a crash.
- Empty catalog and unreachable URL both show helpful guidance messages.
- Backward compatible: existing configs without the catalog URL field use a sensible default.
- **UI principle:** `/browse` is the only entry point — no new menu items or toolbar additions. The browsing dialog opens on demand and closes when done. The primary chat interface stays uncluttered.

## Out of Scope

- In-app template publishing or upload.
- Template ratings, reviews, or download counts (requires a backend).
- Automatic template updates or installed-version checking.
- Authenticated/private catalog URLs (may work transparently, but not explicitly tested).

## Dependencies

- All v1.1 features (complete) — particularly the template import/export and conflict-resolution flows.
- A catalog repository (see Prerequisite section above).

## Notes

- The catalog format is intentionally minimal (flat JSON array, raw GitHub URLs) to avoid infrastructure. A more sophisticated registry is future work.
- Template validation should reuse the existing import path entirely — the catalog install is conceptually "import from URL" rather than "import from local file."
- Contributors to the catalog should be able to test their template locally (via `/import`) before submitting to the catalog.
