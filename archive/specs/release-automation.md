# Feature: Release Automation

## Description

Automate the build-and-publish pipeline so that pushing a version tag triggers GitHub Actions to build platform artifacts for all three OSes and publish them as a GitHub Release. Manual releases are error-prone and don't scale — this makes shipping a one-command operation (`git tag v1.2.0 && git push --tags`).

## Acceptance Criteria

- [ ] A GitHub Actions workflow at `.github/workflows/release.yml` triggers on `v*` tag pushes
- [ ] The workflow builds artifacts for Linux (Ubuntu), macOS (Intel + ARM), and Windows using a build matrix
- [ ] Built artifacts are uploaded as assets on a GitHub Release with the tag name as the release title
- [ ] The release body includes auto-generated changelog content from commits since the last tag
- [ ] The CI pipeline (from `ci-pipeline` spec) must pass before the release workflow publishes any artifacts
- [ ] The full release workflow completes in under 30 minutes across all platforms

## Affected Areas

- New: `.github/workflows/release.yml`
- Modified: `.github/workflows/ci.yml` (add `workflow_call` trigger so release workflow can reuse it as a gate)
- Modified: `pyproject.toml` (version bump convention — version is the source of truth)

## Constraints

- All runners are GitHub-hosted (no self-hosted runners)
- macOS builds require `macos-latest` runners; Windows requires `windows-latest`
- No secrets required for initial setup (signing is deferred)
- Release must not publish if any CI check fails

## Out of Scope

- Code signing or notarization
- Auto-update notifications within the app
- PyPI publishing
- Nightly or pre-release builds

## Dependencies

- Spec: `ci-pipeline` — must have CI passing first
- Spec: `cross-platform-packaging` — must have build scripts before automating them

## Notes

- Use `softprops/action-gh-release` or `ncipollo/release-action` for GitHub Release creation.
- For changelog: GitHub's "auto-generate release notes" feature is sufficient initially. `git-cliff` or `conventional-changelog` can be added later.
- Version is read from `pyproject.toml` to avoid duplication — the tag and the package version should match.
- Build matrix example: `{os: [ubuntu-latest, macos-latest, macos-13, windows-latest], python: [3.10]}` where `macos-latest` is ARM and `macos-13` is Intel.
