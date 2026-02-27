# Tasks: release-automation

**Spec:** /specs/release-automation.md

## Status

- Total: 3
- Complete: 0
- Remaining: 3

## Task List

### Task 1: Release workflow with build matrix

- **Files:** `.github/workflows/release.yml` (new)
- **Done when:** Workflow triggers on `v*` tag push. Build matrix covers Ubuntu (latest), macOS (latest + macos-13 for Intel), and Windows (latest). Each matrix job runs `scripts/build.py` and uploads the artifact. All artifacts appear on the GitHub Release.
- **Criteria covered:** Criterion 1 (workflow triggers on tags), Criterion 2 (matrix builds), Criterion 3 (artifacts on release)
- **Status:** [ ] Not started

### Task 2: CI gating and workflow reuse

- **Files:** `.github/workflows/ci.yml` (add `workflow_call` trigger), `.github/workflows/release.yml` (call CI as a prerequisite job)
- **Done when:** Release workflow calls CI workflow as a required first job. If CI fails (tests or lint), no artifacts are published. Release job depends on CI job passing.
- **Criteria covered:** Criterion 5 (CI must pass before publish)
- **Status:** [ ] Not started

### Task 3: Changelog generation and version management

- **Files:** `.github/workflows/release.yml` (add changelog step), `pyproject.toml` (document version bump convention)
- **Done when:** Release body includes auto-generated changelog from commits since previous tag. Version in `pyproject.toml` is the source of truth — tag name and package version must match. Workflow completes in under 30 minutes across all platforms.
- **Criteria covered:** Criterion 4 (changelog), Criterion 6 (under 30 min)
- **Status:** [ ] Not started

## Test Strategy

| Criterion | Tested in Task |
|-----------|---------------|
| 1. Triggers on v* tags | Task 1 (test: push a test tag, verify workflow starts) |
| 2. Matrix builds all platforms | Task 1 (test: verify matrix includes 4 OS configurations) |
| 3. Artifacts on release | Task 1 (test: verify release assets after tag push) |
| 4. Changelog in release body | Task 3 (test: verify release body contains commit summaries) |
| 5. CI must pass first | Task 2 (test: introduce failing test, push tag, verify no release created) |
| 6. Under 30 minutes | Task 3 (test: measure workflow duration in Actions tab) |

## Session Log

<!-- Append after each session: date, completed, blockers -->
