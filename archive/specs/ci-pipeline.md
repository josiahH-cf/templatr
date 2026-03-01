# Feature: CI Pipeline

## Description

Set up GitHub Actions CI to run the test suite and linter on every push and pull request, establishing a quality gate that prevents regressions as features are added. This is the cheapest high-leverage improvement available — roughly 30 minutes of work that protects every future change from silently breaking things.

## Acceptance Criteria

- [x] A GitHub Actions workflow file exists at `.github/workflows/ci.yml`
- [x] The workflow runs `pytest` with `QT_QPA_PLATFORM=offscreen` on push to `main` and on all pull requests
- [x] The workflow runs `ruff check .` and fails the build on any lint error
- [x] The workflow runs on Ubuntu (latest) with Python 3.10+
- [x] The workflow installs dev dependencies (not llama.cpp) and completes in under 5 minutes
- [x] A CI status badge in `README.md` shows passing/failing state

## Affected Areas

- `.github/workflows/ci.yml` (new)
- `README.md` (badge)
- `pyproject.toml` (verify dev deps are complete — e.g., `psutil` should be in dev deps if tests need it)

## Constraints

- Must work with offscreen Qt (no display server on CI runners)
- Must not require llama.cpp binary, GPU, or model files
- Must not require network access beyond package installation

## Out of Scope

- macOS/Windows CI runners (handled in `release-automation` spec)
- Code coverage reporting
- Deployment or publishing steps
- Security scanning (can be added later)

## Dependencies

None — can be done immediately, in parallel with spec 1 (project-rename).

## Notes

- `psutil` is imported in `integrations/llm.py` with a `try/except` fallback — ensure tests don't fail if `psutil` isn't installed, or add it to dev dependencies.
- Tests already set `QT_QPA_PLATFORM=offscreen` in `conftest.py` — the workflow just needs to export the env var as well.
- Consider caching pip dependencies between runs (`actions/cache` or `setup-python` cache) to speed up workflow.
