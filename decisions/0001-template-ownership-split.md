# Decision 0001: Template Ownership Split

**Date:** 2026-02-26
**Status:** Accepted
**Feature:** /specs/app-split-refactor.md

## Context

Templatr is being split into two independent repos: `templatr` (local prompt optimizer
with LLM integration) and `templatr-espanso` (Espanso automation GUI). Each repo must know
which bundled templates to ship. The 33 bundled templates (31 user-facing in `templates/` and
2 system templates in `templates/_meta/`) all currently live in the monorepo and need explicit
ownership assigned before the split proceeds (AC-6).

## Classification Criteria

A template belongs to the **prompt app** if any of the following are true:
- It produces an LLM-ready prompt (the user fills in variables, then submits to an LLM)
- It powers an LLM workflow inside the prompt app (e.g. the `_meta/` templates that drive
  the AI template generation / improvement features)
- Its primary value is realized only when combined with an LLM call

A template belongs to the **Espanso app** if:
- It is a static text fragment — no LLM call required — that gains value purely from
  Espanso's trigger-based expansion (e.g. a snippet that inserts a phone number or boilerplate)

A template belongs to **both** if it has independent value as a static snippet (Espanso) *and*
as a prompt template (prompt app). Such templates are handled via duplication: the canonical
copy lives in the prompt app repo; the Espanso app repo receives a copy at repo-creation time.
No symlinks or shared libraries are used.

## Options

1. **All 33 templates to prompt app; Espanso app starts with zero bundled templates** —
   Accurate to actual content. Every template in the repo requires an LLM call to be useful.
   Espanso app can add purely-static snippets later.

2. **All templates to both apps** — Over-inclusive. Shipping prompt-optimization templates
   in an Espanso GUI that has no LLM connection is confusing and misleading.

3. **Split by trigger presence** — The 31 user-facing templates all have a `trigger` field
   but they are not static snippets; the trigger is an Espanso sync passthrough. Using
   trigger presence as the sole criterion would misclassify them.

## Decision

Option 1. All 33 templates are assigned to the prompt app. No template meets the criteria
for the Espanso app (static snippet, no LLM required). The Espanso app repo will start with
an empty `templates/` directory; Espanso-native snippets can be added when the Espanso GUI
is built (separate epic).

## Full Assignment Table

| Filename | Name | Has Trigger | Use Case | Owner |
|----------|------|-------------|----------|-------|
| `8020_rapid_learning_research_prompt.json` | Rapid Learning | yes (`:learn`) | Prompt optimization | Prompt App |
| `bias_callouts.json` | Bias Callouts | yes (`:biases`) | Prompt optimization | Prompt App |
| `bias_checker.json` | Claim Challenger | yes (`:bias`) | Prompt optimization | Prompt App |
| `brain_dump_organizer.json` | Brain Dump Organizer | yes (`:braindump`) | Prompt optimization | Prompt App |
| `code_review.json` | Code Review | yes (`:review`) | Prompt optimization | Prompt App |
| `code_review_with_rag_context.json` | Code Review with RAG Context | yes (`:code_review`) | Prompt optimization | Prompt App |
| `communication_coach_two_versions.json` | Message Polisher | yes (`:message`) | Prompt optimization | Prompt App |
| `comprehensive_bugfix_prompt_builder.json` | Bug Diagnosis | yes (`:bugfix`) | Prompt optimization | Prompt App |
| `comprehensive_feature_prompt_builder.json` | Feature Implementation Plan | yes (`:impl`) | Prompt optimization | Prompt App |
| `context_capture.json` | Context Capture | yes (`:context`) | Prompt optimization | Prompt App |
| `contextaware_troubleshooter.json` | Troubleshooter | yes (`:troubleshoot`) | Prompt optimization | Prompt App |
| `decision_framework_from_book.json` | Book Framework | yes (`:framework`) | Prompt optimization | Prompt App |
| `deep_analysis__decision_matrix.json` | Decision Analyzer | yes (`:decide`) | Prompt optimization | Prompt App |
| `deep_research_summary.json` | Research Summary | yes (`:research`) | Prompt optimization | Prompt App |
| `explain_code.json` | Explain Code | yes (`:explain`) | Prompt optimization | Prompt App |
| `feature_request_intake__analysis.json` | Feature Prioritizer | yes (`:feature_re`) | Prompt optimization | Prompt App |
| `feature_workflow.json` | Feature Checklist | yes (`:feature`) | Prompt optimization | Prompt App |
| `goaloriented_prompt_optimizer.json` | Prompt Optimizer | yes (`:optimize`) | Prompt optimization | Prompt App |
| `how_to_decide_principles_and_best_practices.json` | Decision Helper | yes (`:howtodecide`) | Prompt optimization | Prompt App |
| `lessons_learned.json` | Lessons Learned | yes (`:ll`) | Prompt optimization | Prompt App |
| `metaprompt_creator.json` | Meta-Prompt Creator | yes (`:metaprompt`) | Prompt optimization | Prompt App |
| `next_recommended_action.json` | Next Action | yes (`:next`) | Prompt optimization | Prompt App |
| `ondemand_howto_guide.json` | How-To Guide | yes (`:howto`) | Prompt optimization | Prompt App |
| `principle_extractor.json` | Principle Extractor | yes (`:principles`) | Prompt optimization | Prompt App |
| `project_creator_then_assessor.json` | Project Plan | yes (`:project`) | Prompt optimization | Prompt App |
| `refactorization_metaprompt_builder.json` | Code Improvement Analyzer | yes (`:refactoriz`) | Prompt optimization | Prompt App |
| `summarize__extract_tasks.json` | Summarize & Tasks | yes (`:summarize`) | Prompt optimization | Prompt App |
| `super_quick_research_assistant.json` | Quick Research | yes (`:quickresearch`) | Prompt optimization | Prompt App |
| `think_deeply.json` | Think Deeply | yes (`:td`) | Prompt optimization | Prompt App |
| `think_focus.json` | Think Focus | yes (`:tf`) | Prompt optimization | Prompt App |
| `write_tests.json` | Write Tests | yes (`:tests`) | Prompt optimization | Prompt App |
| `_meta/template_generator.json` | Template Generator | no | System/meta | Prompt App only |
| `_meta/template_improver.json` | Template Improver | no | System/meta | Prompt App only |

## Handling of "Both" Templates

No template in the current set qualifies for both apps. If a future template meets the
criteria for both (valuable as a static Espanso snippet *and* as a prompt template), the
policy is:

- The canonical copy lives in the prompt app repo under `templates/`
- At Espanso app repo creation time, qualifying templates are copied (not symlinked) into
  the Espanso app's `templates/`
- Both copies evolve independently — no coordination mechanism is required

## Schema Compatibility

Both apps read the same `.json` template format. The schema is backward-compatible: both
apps parse the same fields and silently ignore any field they do not recognize. Specifically:

- The `trigger` field is present in all 31 user-facing templates. The prompt app stores
  it in the `Template.trigger` dataclass field but does not act on it (passthrough only).
  This field must not be removed from the JSON files or the dataclass.
- The `_meta/` templates have an empty `trigger` field (`""`); this is intentional.
- Future schema additions (new fields) must remain optional with sensible defaults so
  neither app breaks when reading templates written by the other.

## Future Template Placement Guidelines

| Template type | Where it lives |
|---------------|---------------|
| Prompt-optimization template (requires LLM) | `templates/` in the prompt app repo |
| Espanso static snippet (no LLM, trigger-only) | `templates/` in the Espanso app repo |
| App feature driver (powers an in-app AI feature) | `templates/_meta/` in the owning app repo |
| Template qualifying for both apps | `templates/` in prompt app; copy to Espanso at repo creation |

## Consequences

- The `templates/` directory in the current repo requires no restructuring — all files
  stay in place and ship with the prompt app as-is.
- `install.sh` copies the entire `templates/` directory (including `_meta/`) and needs
  no changes for this decision.
- The Espanso app repo will start with an empty `templates/` directory.
- The `trigger` field is preserved in all template JSON files indefinitely; removing it
  would be a breaking schema change.
