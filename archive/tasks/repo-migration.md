# Tasks: repo-migration

**Spec:** /specs/repo-migration.md

## Status

- Total: 5
- Complete: 0
- Remaining: 5

## Task List

### Task 1: Delete legacy `automatr/` and fix all in-tree references

- **Files:** Delete `automatr/` (23 files). Edit `templatr/integrations/llm.py`, `templatr/core/feedback.py`, `templatr/core/templates.py`, `templatr/core/__init__.py`, `templatr/ui/__init__.py`, `templatr/ui/main_window.py`, `templatr/ui/template_improve.py`, `templatr/ui/template_generate.py`, `templatr/ui/theme.py`, `templatr/ui/llm_settings.py`, `templatr/ui/template_editor.py`, `templatr/integrations/__init__.py` (docstring `Automatr` → `Templatr`). Edit `templatr/ui/main_window.py` (window title, about menu, app name → `Templatr`). Edit `tests/test_responsive_layout.py` (hardcoded path `automatr-prompt` → relative or `templatr`).
- **Done when:** `automatr/` directory does not exist. `grep -ri 'automatr' templatr/` returns only the intentional migration code in `config.py` (2 lines). `grep -ri 'automatr' tests/` returns only intentional migration tests in `test_config.py`. All tests pass.
- **Criteria covered:** Criterion 3 (automatr/ deleted), Criterion 9 (source docstrings), Criterion 10 (test imports)
- **Status:** [ ] Not started

### Task 2: Update project metadata and build config

- **Files:** `pyproject.toml` (name → `templatr`, entry point → `templatr = "templatr.__main__:main"`, remove `automatr` entry point, URLs → `github.com/josiahH-cf/templatr`, authors → `Templatr Contributors`, packages include → `templatr*` only). Verify `build.spec` already correct.
- **Done when:** `grep 'automatr' pyproject.toml` returns zero matches. `pip install -e .` succeeds. `templatr` command works. `automatr` entry point no longer exists.
- **Criteria covered:** Criterion 4 (pyproject.toml)
- **Status:** [ ] Not started

### Task 3: Update install.sh, README, AGENTS.md, GOVERNANCE.md, decisions/

- **Files:** `install.sh` (~12 references: aliases, paths, messages, verification). `README.md` (~9 references). `AGENTS.md` (architecture section, ~4 references). `GOVERNANCE.md` (~1 reference). `decisions/0001-template-ownership-split.md` (import references). `scripts/dedupe_templates.py` (any references).
- **Done when:** `grep -i 'automatr' install.sh README.md AGENTS.md GOVERNANCE.md decisions/ scripts/` returns zero matches (except intentional historical context, if any, marked with a comment).
- **Criteria covered:** Criterion 5 (install.sh), Criterion 6 (README), Criterion 7 (AGENTS.md), Criterion 8 (GOVERNANCE.md)
- **Status:** [ ] Not started

### Task 4: Create new GitHub repo, copy project, fix remotes

- **Files:** Git configuration, remotes. New directory `~/templatr`.
- **Steps:**
  1. `gh repo create josiahH-cf/templatr --public --description "Local-model prompt optimizer with templates and llama.cpp integration"`
  2. `cp -a ~/automatr-prompt ~/templatr`
  3. `cd ~/templatr && git remote remove legacy`
  4. `cd ~/templatr && git remote set-url origin https://github.com/josiahH-cf/templatr.git`
  5. `cd ~/templatr && git push -u origin main --tags`
  6. `cd ~/templatr && git push origin --all`
- **Done when:** `~/templatr` exists. `git remote -v` in `~/templatr` shows only `origin → github.com/josiahH-cf/templatr.git`. All branches pushed. `gh repo view josiahH-cf/templatr` succeeds.
- **Criteria covered:** Criterion 1 (new repo), Criterion 2 (workspace dir), Criterion 11 (remotes)
- **Status:** [ ] Not started

### Task 5: Final validation and open VS Code in new workspace

- **Files:** None (verification only).
- **Steps:**
  1. `cd ~/templatr && ruff check .`
  2. `cd ~/templatr && python -m pytest -q`
  3. `cd ~/templatr && pip install -e .`
  4. `cd ~/templatr && templatr --version`
  5. Verify: `grep -ri 'automatr' ~/templatr/ --include='*.py' --include='*.md' --include='*.toml' --include='*.sh' --include='*.yml'` returns only intentional config migration references
  6. `code ~/templatr` — open a new VS Code window
- **Done when:** Lint clean, all tests pass, no stale references, VS Code open in `~/templatr`.
- **Criteria covered:** Criterion 12 (lint), Criterion 13 (tests), Criterion 14 (no new deps), Criterion 15 (VS Code window)
- **Status:** [ ] Not started

## Test Strategy

| Criterion | Tested in Task |
|-----------|---------------|
| 1. New GitHub repo | Task 4 (manual: `gh repo view`) |
| 2. Workspace dir ~/templatr | Task 4 (verify directory exists) |
| 3. automatr/ deleted | Task 1 (verify dir gone, grep clean) |
| 4. pyproject.toml | Task 2 (grep, pip install, entry point) |
| 5. install.sh | Task 3 (grep for automatr = 0 matches) |
| 6. README.md | Task 3 (grep) |
| 7. AGENTS.md | Task 3 (grep) |
| 8. GOVERNANCE.md | Task 3 (grep) |
| 9. Source docstrings | Task 1 (grep templatr/) |
| 10. Test imports | Task 1 (grep tests/) |
| 11. Git remotes | Task 4 (git remote -v) |
| 12. Lint | Task 5 (ruff check) |
| 13. Tests | Task 5 (pytest) |
| 14. No new deps | Task 5 (pyproject.toml diff) |
| 15. VS Code window | Task 5 (code ~/templatr) |

## Session Log

<!-- Append after each session: date, completed, blockers -->
