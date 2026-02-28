"""Tests for release automation workflow configuration."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _read(path: Path) -> str:
    """Read a UTF-8 text file."""
    return path.read_text(encoding="utf-8")


def test_release_workflow_exists() -> None:
    """release.yml exists in GitHub Actions workflows."""
    assert (ROOT / ".github" / "workflows" / "release.yml").exists()


def test_release_workflow_triggers_on_version_tags() -> None:
    """Release workflow is triggered by version tags that start with v."""
    content = _read(ROOT / ".github" / "workflows" / "release.yml")
    assert "push:" in content
    assert "tags:" in content
    assert '"v*"' in content or "'v*'" in content


def test_release_workflow_builds_all_target_platforms() -> None:
    """Release workflow matrix includes Linux, macOS (ARM+Intel), and Windows."""
    content = _read(ROOT / ".github" / "workflows" / "release.yml")
    assert "ubuntu-latest" in content
    assert "macos-latest" in content
    assert "macos-13" in content
    assert "windows-latest" in content


def test_release_workflow_reuses_ci_workflow() -> None:
    """Release workflow calls ci.yml as a required gate job."""
    content = _read(ROOT / ".github" / "workflows" / "release.yml")
    assert "uses: ./.github/workflows/ci.yml" in content


def test_release_workflow_release_job_depends_on_ci_gate() -> None:
    """Release publish step depends on CI gate and build jobs."""
    content = _read(ROOT / ".github" / "workflows" / "release.yml")
    assert "needs: [ci_gate, build]" in content


def test_release_workflow_generates_release_notes() -> None:
    """Release action is configured to auto-generate changelog notes."""
    content = _read(ROOT / ".github" / "workflows" / "release.yml")
    assert "softprops/action-gh-release" in content
    assert "generate_release_notes: true" in content
    assert "name: ${{ github.ref_name }}" in content


def test_release_workflow_validates_tag_matches_pyproject_version() -> None:
    """Release workflow validates tag version against pyproject version."""
    content = _read(ROOT / ".github" / "workflows" / "release.yml")
    assert "pyproject.toml" in content
    assert "github.ref_name" in content
    assert "Version mismatch" in content


def test_release_workflow_attaches_artifacts_to_release() -> None:
    """Release action is configured to attach built artifacts as release assets."""
    content = _read(ROOT / ".github" / "workflows" / "release.yml")
    assert "files: release-artifacts/**" in content


def test_release_workflow_ci_gate_has_timeout() -> None:
    """CI gate job declares a timeout to bound total release pipeline duration."""
    content = _read(ROOT / ".github" / "workflows" / "release.yml")
    # Inspect only the ci_gate job section (before the build job starts)
    ci_gate_section = content.split("  build:")[0]
    assert "timeout-minutes:" in ci_gate_section


def test_ci_workflow_supports_workflow_call() -> None:
    """CI workflow can be called as a reusable workflow."""
    content = _read(ROOT / ".github" / "workflows" / "ci.yml")
    assert "workflow_call:" in content
