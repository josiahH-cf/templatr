"""orchestratr connector for Templatr.

Generates a drop-in manifest for orchestratr's ``apps.d/`` directory,
provides a JSON status endpoint for health-checking, and resolves
platform-specific paths (native Linux, macOS, WSL2).

All functions are explicit — this module has zero side effects on import.
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional, Tuple

from templatr import __version__
from templatr.core.config import get_platform_config

logger = logging.getLogger(__name__)

# Manifest template — flat YAML, no library needed
_MANIFEST_TEMPLATE = """\
# orchestratr app manifest — written by templatr v{version}
name: templatr
chord: "t"
command: "templatr"
environment: {environment}
description: "Local-model prompt optimizer"
ready_cmd: "templatr status --json"
ready_timeout_ms: 5000
"""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _resolve_windows_username() -> Optional[str]:
    """Resolve the Windows username from inside WSL2.

    Returns:
        The Windows username string, or None if detection fails.
    """
    import subprocess

    try:
        result = subprocess.run(
            ["cmd.exe", "/C", "echo", "%USERNAME%"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        username = result.stdout.strip()
        if username and username != "%USERNAME%":
            return username
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass

    # Fallback: scan /mnt/c/Users for non-system directories
    users_dir = Path("/mnt/c/Users")
    if users_dir.is_dir():
        system_dirs = {"Default", "Public", "Default User", "All Users"}
        for entry in users_dir.iterdir():
            if entry.is_dir() and entry.name not in system_dirs:
                return entry.name

    return None


def _get_orchestratr_base_dir() -> Optional[Path]:
    """Return the orchestratr base config directory for the current platform.

    Returns:
        Path to the orchestratr config dir, or None if it doesn't exist.
    """
    pc = get_platform_config()

    if pc.platform == "wsl2":
        win_user = _resolve_windows_username()
        if not win_user:
            logger.info("Could not determine Windows username for WSL2 path resolution")
            return None
        base = Path(f"/mnt/c/Users/{win_user}/AppData/Roaming/orchestratr")
    elif pc.platform == "macos":
        base = Path.home() / "Library" / "Application Support" / "orchestratr"
    else:  # linux (native)
        xdg = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
        base = Path(xdg) / "orchestratr"

    if not base.exists():
        return None

    return base


def _get_template_count() -> int:
    """Return the number of user-visible templates.

    Returns:
        Integer count of loaded templates, or 0 on error.
    """
    try:
        from templatr.core.templates import get_template_manager

        tm = get_template_manager()
        return len(tm.list_all())
    except Exception:
        logger.debug("Could not count templates", exc_info=True)
        return 0


def _get_llm_status() -> Tuple[str, Optional[str]]:
    """Return the LLM server status and loaded model name.

    Returns:
        Tuple of (status_string, model_name_or_none).
        status_string is one of: "running", "stopped", "unknown".
    """
    try:
        from templatr.integrations.llm import get_llm_server

        server = get_llm_server()
        if server.is_running():
            # Get model name from config
            model = server.config.model_path
            model_name = Path(model).name if model else None
            return "running", model_name
        return "stopped", None
    except Exception:
        logger.debug("Could not determine LLM status", exc_info=True)
        return "unknown", None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def resolve_orchestratr_apps_dir() -> Optional[Path]:
    """Resolve the orchestratr ``apps.d/`` directory path.

    Uses platform detection to determine the correct path:
    - Linux: ``~/.config/orchestratr/apps.d/`` (or ``$XDG_CONFIG_HOME``)
    - macOS: ``~/Library/Application Support/orchestratr/apps.d/``
    - WSL2: ``/mnt/c/Users/<user>/AppData/Roaming/orchestratr/apps.d/``

    Returns:
        Path to the ``apps.d/`` directory, or None if orchestratr is not
        installed (base directory doesn't exist).
    """
    base = _get_orchestratr_base_dir()
    if base is None:
        return None
    return base / "apps.d"


def generate_manifest() -> bool:
    """Generate the orchestratr app manifest for templatr.

    Writes a flat YAML manifest to ``apps.d/templatr.yml``. Creates the
    ``apps.d/`` subdirectory if it doesn't exist.

    Returns:
        True if manifest was written successfully, False if skipped
        (orchestratr not installed).
    """
    apps_dir = resolve_orchestratr_apps_dir()
    if apps_dir is None:
        logger.info(
            "orchestratr not detected — skipping manifest generation. "
            "Install orchestratr to enable hotkey integration."
        )
        return False

    pc = get_platform_config()
    environment = "wsl" if pc.platform == "wsl2" else "native"

    content = _MANIFEST_TEMPLATE.format(
        version=__version__,
        environment=environment,
    )

    # Ensure apps.d/ exists
    apps_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = apps_dir / "templatr.yml"
    manifest_path.write_text(content, encoding="utf-8")
    logger.info("Wrote orchestratr manifest to %s", manifest_path)
    return True


def manifest_needs_update() -> bool:
    """Check whether the orchestratr manifest is stale or missing.

    A manifest is stale when:
    - It doesn't exist but orchestratr is installed
    - Its version header doesn't match the current templatr version

    Returns:
        True if the manifest should be regenerated, False if current
        or if orchestratr is not installed.
    """
    apps_dir = resolve_orchestratr_apps_dir()
    if apps_dir is None:
        return False

    manifest_path = apps_dir / "templatr.yml"
    if not manifest_path.exists():
        return True

    try:
        content = manifest_path.read_text(encoding="utf-8")
        expected_header = f"written by templatr v{__version__}"
        return expected_header not in content
    except OSError:
        logger.debug("Could not read manifest for staleness check", exc_info=True)
        return True


def get_status_json() -> str:
    """Generate the status JSON for the ``templatr status --json`` command.

    Returns:
        JSON string with fields: version, status, config_dir,
        template_count, llm_server_status, model_loaded.
        When degraded, includes an errors array.
    """
    pc = get_platform_config()
    template_count = _get_template_count()
    llm_status, model_loaded = _get_llm_status()

    errors: list[str] = []
    if template_count == 0:
        errors.append("No templates found")
    if llm_status != "running":
        errors.append("LLM server not running")

    status = "degraded" if errors else "ok"

    data: dict = {
        "version": __version__,
        "status": status,
        "config_dir": str(pc.config_dir),
        "template_count": template_count,
        "llm_server_status": llm_status,
        "model_loaded": model_loaded,
    }

    if errors:
        data["errors"] = errors

    return json.dumps(data, indent=2)
