# Roadmap — Templatr v1.2

## UI Principles

All v1.2 features must preserve the app's clean chat-first interface:

- **No new permanent UI elements.** No new menu items, toolbar buttons, or sidebar panels unless replacing an existing one.
- **Slash commands are the entry point.** New features are accessed via `/` commands, consistent with the existing interaction model.
- **Settings live in existing dialogs.** New configuration goes into the existing LLM settings or config file — no new settings panels.
- **Dialogs are transient.** Feature dialogs open on demand and close when done. Nothing persists on screen beyond the chat thread.
- **If it isn't used weekly, it's a setting toggle, not a UI element.**

## Execution Order

Features are independent but ordered by user-value and data dependencies.
Performance-dashboard benefits from timing data introduced by earlier features
but can land standalone.

1. ~~**multi-turn-chat**~~ — ✅ Complete. See [specs/multi-turn-chat.md](../specs/multi-turn-chat.md).
2. ~~**prompt-ab-testing**~~ — ✅ Complete. See [specs/prompt-ab-testing.md](../specs/prompt-ab-testing.md).
3. ~~**performance-dashboard**~~ — ✅ Complete. See [specs/performance-dashboard.md](../specs/performance-dashboard.md).
4. ~~**template-marketplace**~~ — ✅ Complete. See [tasks/template-marketplace.md](template-marketplace.md).

## Spec Index

| # | Feature | Spec | Entry Point | New UI Surface |
|---|---------|------|-------------|----------------|
| 1 | Multi-Turn Chat | [specs/multi-turn-chat.md](../specs/multi-turn-chat.md) | Transparent (just keep typing) | None — settings in LLM dialog |
| 2 | Prompt A/B Testing | [specs/prompt-ab-testing.md](../specs/prompt-ab-testing.md) | `/test` command | On-demand results dialog |
| 3 | Performance Dashboard | [specs/performance-dashboard.md](../specs/performance-dashboard.md) | `/performance` command | On-demand dashboard dialog |
| 4 | Template Marketplace | [specs/template-marketplace.md](../specs/template-marketplace.md) | `/browse` command | On-demand catalog dialog |

## Documentation Updates

Each spec includes acceptance criteria for updating:
- **README** — new feature descriptions and usage examples.
- **`/help` output** — new command documentation visible in-app.
- **Troubleshooting docs** — updated if the feature introduces new error paths (e.g., network errors in marketplace).

## Completed

- **template-marketplace** — `/browse` catalog browser, fully implemented and merged. Catalog seeding is a separate deferred content task; see [tasks/seed-catalog-meta-prompt.md](seed-catalog-meta-prompt.md) — **do not treat as a code feature**.
- **multi-turn-chat** — Conversation memory with ChatML formatting, configurable turn count and char limit, `/compare` integration. All 21 tests pass.
- **prompt-ab-testing** — `/test [N] [| prompt]` runs prompt N times, summary in chat thread, `/test view` detail dialog, pick-as-winner favouriting, stop cancellation. All 21 tests pass.
- **performance-dashboard** — `/performance` generation metrics dashboard with per-model and per-template breakdowns, date-range filter, sortable columns. All 24 tests pass.

## Active

_All v1.2 features complete._

## Archive

All v1.1 specs, tasks, and the v1.1 roadmap are archived in [archive/](../archive/):
- [archive/tasks/roadmap-v1.1.md](../archive/tasks/roadmap-v1.1.md)
- [archive/specs/](../archive/specs/) — 16 completed spec files
- [archive/tasks/](../archive/tasks/) — 16 completed task files
