# Tasks: Phase 4 — Template Ownership Decision

**Spec:** /specs/app-split-refactor.md

## Status

- Total: 3
- Complete: 1
- Remaining: 2

## Prerequisites

- Phase 1 complete (prompt app exists and runs)

## Task List

### Task 1: Audit all 31 bundled templates for app affinity

- **Files:** All files in `templates/` (read-only audit)
- **Done when:** A table exists listing every template with columns: name, has trigger, primary use case (prompt optimization / text expansion / both), recommended owner (prompt app / espanso app / both). No template is unclassified
- **Criteria covered:** AC-6
- **Status:** [x] Complete — all 33 templates audited; full table in `decisions/0001-template-ownership-split.md`

#### Audit Table (33 templates: 31 regular + 2 meta)

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

### Task 2: Define ownership criteria and write decision record

- **Files:** New: `decisions/0001-template-ownership-split.md`
- **Done when:** Decision record exists with: (1) classification criteria (what makes a template belong to prompt app vs espanso app), (2) the full assignment table from Task 1, (3) handling of templates that belong to both (duplicate vs shared reference), (4) schema compatibility statement (both apps read the same JSON format, ignore unknown fields), (5) guidelines for where future templates should be placed
- **Criteria covered:** AC-6
- **Status:** [ ] Not started

### Task 3: Move templates into app-specific bundles

- **Files:** `templates/` directory restructuring
- **Done when:** Templates are organized into clear ownership groups. The prompt app's `install.sh` or setup only copies prompt-app templates. A manifest or directory convention makes ownership obvious (e.g., templates stay as-is for prompt app; espanso-specific templates are tagged or listed in the decision doc for later extraction). App still loads all templates correctly
- **Criteria covered:** AC-6
- **Status:** [ ] Not started

## Test Strategy

| Criterion | Verified by |
|-----------|-------------|
| AC-6 | Task 2: decision record file exists and is complete |
| AC-6 | Task 3: app launches, template count matches expected |

## Definition of Done

- Decision record committed at `decisions/0001-template-ownership-split.md`
- Every bundled template has a clear owner
- Template loading still works — no regressions

## Notes

- Most templates are prompt-optimization focused (code review, research, analysis). The likely outcome is: all or nearly all stay with the prompt app, and the espanso app either bundles a small subset or starts with zero bundled templates (user creates their own).
- The `_meta/` templates (`template_generator.json`, `template_improver.json`) are exclusively prompt-app assets — they power the AI generation/improvement features.
- This phase can run in parallel with Phase 2 or Phase 3 since it's primarily a documentation task.

## Session Log

<!-- Append after each session: date, completed, blockers -->

### 2026-02-26

- Completed Task 1: audited all 33 templates; full table added above and in decision record
- No blockers
