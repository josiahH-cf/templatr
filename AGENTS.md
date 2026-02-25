# Project

<!-- Replace: project name, one-line description, primary language/framework -->

# Build

<!-- Replace with actual build steps for your project -->

- Install: `[install step]`
- Build: `[build step]`
- Test (all): `[test step]`
- Test (single): `[single test step with placeholder]`
- Lint: `[lint step]`
- Format: `[format step]`
- Type-check: `[type-check step, if applicable]`

# Architecture

<!-- Replace with 5–15 lines mapping key directories to responsibilities -->

# Conventions

- Functions and variables: [naming convention]
- Files and directories: [naming convention]
- Prefer explicit error handling over silent failures
- No dead code — remove unused imports, variables, and functions
- Every public function has a doc comment
- No hardcoded secrets, URLs, or environment-specific values

# Testing

- Write tests before implementation
- Each acceptance criterion requires at least one test
- Do not modify existing tests to accommodate new code — fix the implementation
- Run the full test suite before committing
- Tests must be deterministic — no flaky tests in the main suite

# Planning

- Features with more than 3 implementation steps require a written plan
- Plans go in `/tasks/[feature-name].md` or as an ExecPlan per `/.codex/PLANS.md`
- Plans are living documents — update progress, decisions, and surprises as work proceeds
- A plan that cannot fit in 5 tasks indicates the feature should be split. Call this out.

# Dependencies

- Add dependencies only when standard library cannot solve the problem
- Pin versions explicitly
- Security audit new dependencies before adding

# Commits

- One logical change per commit
- Present-tense imperative subject line, under 72 characters
- Reference the spec or task file in the commit body when applicable
- Commit after each completed task, not after all tasks

# Branches

- Branch from the latest target branch immediately before starting work
- One feature per branch
- Delete after merge
- Never commit directly to the target branch
- Naming: `[type]/[issue-id]-[slug]` (e.g., `feat/42-user-auth`, `fix/87-null-check`)

# Worktrees

- Use git worktrees for concurrent features across agents
- Worktree root: `.trees/[branch-name]/`
- Each worktree is isolated: agents operate only within their assigned worktree
- Artifacts (specs, tasks, decisions) live in the main worktree and are shared read-only
- Never switch branches inside a worktree — create a new one

# Pull Requests

- Link to the spec file
- Diff under 300 lines; if larger, split the feature
- All CI checks pass before requesting review
- PR description states: what changed, why, how to verify

# Review

- Reviewable in under 15 minutes
- Tests cover every acceptance criterion
- No unrelated changes in the diff
- Cross-agent review encouraged: use a different model than the one that wrote the code

# Security

- No secrets in code or instruction files
- Use environment variables for all credentials
- Sanitize all external input
- Log security-relevant events
