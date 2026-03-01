# Roadmap — Templatr v1.2

## Execution Order

Specs are ordered by dependency chain. Performance-dashboard benefits from
prompt-ab-testing but can land independently.

1. **multi-turn-chat** — Conversation memory with sliding-window context buffer (no deps beyond v1.1)
2. **prompt-ab-testing** — Run same prompt N times, compare outputs, pick winner (no deps beyond v1.1)
3. **performance-dashboard** — Latency/token/model usage metrics from history (soft dep: prompt-ab-testing for richer data)
4. **template-marketplace** — Browse and install community templates from GitHub catalog (no deps beyond v1.1)

## Spec Index

| Feature | Spec | Size Estimate | Key Deliverables |
|---|---|---|---|
| Multi-Turn Chat | `/specs/multi-turn-chat.md` | Medium (3–4 tasks) | `ConversationBuffer`, config fields, buffer reset on switch/clear |
| Prompt A/B Testing | `/specs/prompt-ab-testing.md` | Medium (3–4 tasks) | `/test` command, `ABTestWorker`, `ABTestResultsDialog` |
| Performance Dashboard | `/specs/performance-dashboard.md` | Medium (3–4 tasks) | History schema extension, `PerformanceDashboardDialog`, `/performance` |
| Template Marketplace | `/specs/template-marketplace.md` | Medium (3–4 tasks) | `TemplateCatalogDialog`, catalog fetch worker, `/browse` command |

## Active

_No active work yet. Begin with multi-turn-chat._

## Completed

See [archive/tasks/roadmap-v1.1.md](../archive/tasks/roadmap-v1.1.md) for v1.1 history.
