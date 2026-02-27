# Decision 0002: Project Name — templatr

## Status

Accepted

## Context

The project needed a memorable, shareable name before other downstream features (crash-logging, cross-platform-packaging, release-automation, documentation-overhaul) could proceed. The name affects the GitHub repo URL, Python package name, import paths, config directories, and all documentation.

Requirements:
- Valid Python package identifier (lowercase, no hyphens)
- Available on PyPI (not taken)
- Minimal GitHub presence (no popular repos with the same name)
- Clearly communicates what the tool does

## Alternatives Considered

| Name | PyPI | GitHub | Notes |
|------|------|--------|-------|
| automatr (keep) | — | Current | Generic; doesn't communicate prompt/template purpose |
| tinkerprompt | Available | 0 repos | Good, but long |
| promptanvil | Available | 0 repos | Evocative but niche metaphor |
| localsmith | Available | 2 repos, 0★ | Doesn't mention prompts or templates |
| promptloom | Available | 5 repos, max 1★ | Decent but "loom" metaphor is weak |
| promptmint | Available | 7 repos, max 1★ | Playful but slightly confusing |
| promptsmith | Taken | — | Eliminated |
| promptforge | Taken | — | Eliminated |
| promptbox | Not checked | — | Generic container metaphor |

## Decision

**templatr** — a contraction of "template" + the "-r" agent suffix.

- PyPI: Available
- GitHub: ~75 results, no dominant project (max 3★, unrelated templating tools)
- Clearly communicates the core concept: reusable prompt **templates**
- Short, memorable, easy to type
- Valid Python package name: `templatr`
- Config dir: `~/.config/templatr/`

## Consequences

- All `automatr` references in source, tests, docs, and config paths must be updated
- Existing users' config at `~/.config/automatr/` needs auto-migration to `~/.config/templatr/`
- The `install.sh` alias changes from `automatr` to `templatr`
- GitHub repo rename (manual, post-merge) from `automatr-prompt` to `templatr`
