"""Diagnostic ``--doctor`` command for Templatr.

Reports platform, paths, templates, models, and llama-server status
with actionable guidance for anything that is missing.
"""

import os
import shutil

from templatr.core.config import get_platform_config


def run_doctor() -> int:
    """Run the --doctor diagnostic and print results to stdout.

    Returns:
        0 if all critical checks pass, 1 otherwise.
    """
    pc = get_platform_config()
    issues: list[str] = []

    # ---- Platform --------------------------------------------------------
    print(f"Platform:     {pc.platform}")
    print(f"Config dir:   {pc.config_dir}")
    print(f"Data dir:     {pc.data_dir}")
    print(f"Models dir:   {pc.models_dir}")
    print()

    # ---- Config dir ------------------------------------------------------
    if pc.config_dir.is_dir():
        print("  [OK] Config directory exists")
    else:
        print(f"  [!!] Config directory not found: {pc.config_dir}")
        print("       Run templatr once to create it automatically.")
        issues.append("config_dir")

    # ---- Templates -------------------------------------------------------
    templates_dir = pc.config_dir / "templates"
    if templates_dir.is_dir():
        templates = list(templates_dir.rglob("*.json"))
        count = len(templates)
        if count:
            print(f"  [OK] Templates found: {count}")
        else:
            print(f"  [!!] Templates directory is empty: {templates_dir}")
            print("       Run templatr once — bundled templates are seeded automatically.")
            issues.append("templates")
    else:
        print(f"  [!!] Templates directory not found: {templates_dir}")
        print("       Run templatr once to create it and seed bundled templates.")
        issues.append("templates")

    # ---- Models ----------------------------------------------------------
    if pc.models_dir.is_dir():
        models = list(pc.models_dir.rglob("*.gguf"))
        count = len(models)
        if count:
            print(f"  [OK] Model files found: {count}")
            for m in models:
                size_mb = m.stat().st_size / (1024 * 1024)
                print(f"       - {m.name} ({size_mb:.0f} MB)")
        else:
            print(f"  [--] No .gguf model files in {pc.models_dir}")
            print(f"       Download a GGUF model and place it in {pc.models_dir}")
    else:
        print(f"  [--] Models directory not found: {pc.models_dir}")
        print("       Create it and add .gguf files to use local LLM generation.")

    # ---- llama-server binary ---------------------------------------------
    binary_path = _find_binary(pc)
    if binary_path:
        print(f"  [OK] llama-server found: {binary_path}")
    else:
        print("  [--] llama-server not found")
        print("       Install via ./install.sh or download from:")
        print("       https://github.com/ggerganov/llama.cpp/releases")

    print()
    if issues:
        print(f"Result: {len(issues)} issue(s) found — see guidance above.")
        return 1
    else:
        print("Result: All checks passed.")
        return 0


def _find_binary(pc) -> str | None:
    """Search for llama-server binary in platform search paths and PATH.

    Args:
        pc: PlatformConfig with binary_name and binary_search_paths.

    Returns:
        Path string if found, None otherwise.
    """
    for search_dir in pc.binary_search_paths:
        candidate = search_dir / pc.binary_name
        if candidate.exists() and os.access(candidate, os.X_OK):
            return str(candidate)

    path_result = shutil.which(pc.binary_name)
    if path_result:
        return path_result

    return None
