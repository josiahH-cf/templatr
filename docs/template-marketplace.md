# Template Marketplace

Templatr includes a built-in community catalog of prompt templates you can browse and install without leaving the app.

---

## Browsing the Catalog

In the chat bar, type `/browse` and press Enter.  A dialog opens that lets you:

- **Search** by name, description, author, or tag in real time.
- **Filter by tag** using the tag drop-down.
- **Preview** a template's full details before installing.
- **Install** any template with one click — it is downloaded, validated, and added to your template library immediately.

After install, the template tree on the left refreshes automatically and the template is ready to use.

---

## Contributing a Template

Community templates live in the [templatr-catalog](https://github.com/josiahH-cf/templatr-catalog) repository.

1. **Test locally first** — use `/import` in Templatr to import your `.json` template file and confirm it works.
2. **Fork** `josiahH-cf/templatr-catalog`.
3. Add your template file under `templates/` (lowercase snake_case filename, e.g. `my_great_template.json`).
4. Add an entry to `catalog.json` with the required fields: `name`, `description`, `author`, `tags`, `version`, and `download_url` pointing to the raw file URL.
5. Open a Pull Request — see [CONTRIBUTING](https://github.com/josiahH-cf/templatr-catalog/blob/main/CONTRIBUTING.md) for requirements.

---

## Hosting a Private Catalog

You can point Templatr at any URL that serves a valid catalog JSON array.

1. Fork the catalog repo (or create your own with the same format).
2. In Templatr, open `/settings` and change **Catalog URL** to the raw URL of your `catalog.json`.
3. Use `/browse` as normal — Templatr fetches from your URL.

This works for company-internal libraries, team collections, or curated personal sets.
