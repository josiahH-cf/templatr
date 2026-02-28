#!/usr/bin/env python3
"""Download pre-built llama-server binary from llama.cpp GitHub releases.

Detects the current platform, downloads the correct CPU-only binary archive
from https://github.com/ggml-org/llama.cpp/releases, extracts the
``llama-server`` executable, and places it in ``vendor/llama-server/``.

Idempotent: skips download if the binary already exists and a ``.version``
marker matches the requested release tag.

Usage::

    python scripts/download_llama_server.py          # latest release
    python scripts/download_llama_server.py b8175     # specific tag

"""

import io
import json
import os
import platform
import shutil
import stat
import sys
import tarfile
import zipfile
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REPO = "ggml-org/llama.cpp"
API_BASE = f"https://api.github.com/repos/{REPO}"
RELEASE_BASE = f"https://github.com/{REPO}/releases/download"

VENDOR_DIR = Path(__file__).resolve().parent.parent / "vendor" / "llama-server"
VERSION_MARKER = VENDOR_DIR / ".version"

BINARY_NAME = "llama-server.exe" if sys.platform == "win32" else "llama-server"


# ---------------------------------------------------------------------------
# Platform detection
# ---------------------------------------------------------------------------


def _detect_platform_key() -> str:
    """Return the llama.cpp release asset suffix for this platform.

    Raises:
        SystemExit: if the platform is unsupported.
    """
    system = platform.system()
    machine = platform.machine().lower()

    if system == "Linux":
        if machine in ("x86_64", "amd64"):
            return "ubuntu-x64"
        raise SystemExit(f"Unsupported Linux architecture: {machine}")

    if system == "Darwin":
        if machine == "arm64":
            return "macos-arm64"
        if machine in ("x86_64", "amd64"):
            return "macos-x64"
        raise SystemExit(f"Unsupported macOS architecture: {machine}")

    if system == "Windows":
        if machine in ("amd64", "x86_64"):
            return "win-cpu-x64"
        if machine == "arm64":
            return "win-cpu-arm64"
        raise SystemExit(f"Unsupported Windows architecture: {machine}")

    raise SystemExit(f"Unsupported platform: {system}")


def _archive_ext(platform_key: str) -> str:
    """Return the archive extension for the platform key."""
    return ".zip" if platform_key.startswith("win-") else ".tar.gz"


# ---------------------------------------------------------------------------
# GitHub helpers
# ---------------------------------------------------------------------------


def _github_get(url: str) -> dict:
    """Fetch JSON from the GitHub API (unauthenticated)."""
    token = os.environ.get("GITHUB_TOKEN", "")
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except HTTPError as exc:
        raise SystemExit(
            f"GitHub API request failed ({exc.code}): {url}\n{exc.read().decode()}"
        ) from exc


def get_latest_tag() -> str:
    """Fetch the latest release tag name from GitHub."""
    data = _github_get(f"{API_BASE}/releases/latest")
    return data["tag_name"]


# ---------------------------------------------------------------------------
# Download & extract
# ---------------------------------------------------------------------------


def _download(url: str) -> bytes:
    """Download a URL and return raw bytes, printing progress."""
    print(f"  Downloading {url}")
    req = Request(url)
    token = os.environ.get("GITHUB_TOKEN", "")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urlopen(req, timeout=300) as resp:
        total = resp.headers.get("Content-Length")
        data = bytearray()
        chunk_size = 1024 * 256
        while True:
            chunk = resp.read(chunk_size)
            if not chunk:
                break
            data.extend(chunk)
            if total:
                pct = len(data) * 100 // int(total)
                print(
                    f"\r  {len(data) // 1024:,} KB / {int(total) // 1024:,} KB ({pct}%)",
                    end="",
                    flush=True,
                )
        if total:
            print()
    return bytes(data)


def _extract_binary(archive_bytes: bytes, platform_key: str, dest_dir: Path) -> Path:
    """Extract llama-server binary from archive bytes into *dest_dir*.

    Returns:
        Path to the extracted binary.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / BINARY_NAME

    ext = _archive_ext(platform_key)

    if ext == ".tar.gz":
        with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz") as tf:
            # Find the llama-server binary inside the archive
            target = None
            for member in tf.getmembers():
                basename = os.path.basename(member.name)
                if basename == BINARY_NAME and member.isfile():
                    target = member
                    break
            if target is None:
                raise SystemExit(
                    f"Could not find {BINARY_NAME} in archive. "
                    f"Members: {[m.name for m in tf.getmembers()[:20]]}"
                )
            with tf.extractfile(target) as src:
                with open(dest_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)
    else:
        with zipfile.ZipFile(io.BytesIO(archive_bytes)) as zf:
            target = None
            for name in zf.namelist():
                basename = os.path.basename(name)
                if basename == BINARY_NAME:
                    target = name
                    break
            if target is None:
                raise SystemExit(
                    f"Could not find {BINARY_NAME} in archive. "
                    f"Members: {zf.namelist()[:20]}"
                )
            with zf.open(target) as src:
                with open(dest_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)

    # Ensure executable on Unix
    if sys.platform != "win32":
        dest_path.chmod(
            dest_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
        )

    return dest_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def download_llama_server(tag: str | None = None, dest_dir: Path | None = None) -> Path:
    """Download and extract the llama-server binary.

    Args:
        tag: Release tag (e.g. ``b8175``). Defaults to latest.
        dest_dir: Destination directory. Defaults to ``vendor/llama-server/``.

    Returns:
        Path to the extracted binary.
    """
    dest = dest_dir or VENDOR_DIR
    version_marker = dest / ".version"

    # Resolve tag
    if tag is None:
        print("Fetching latest release tag...")
        tag = get_latest_tag()
    print(f"Release: {tag}")

    # Check idempotence
    binary_path = dest / BINARY_NAME
    if binary_path.exists() and version_marker.exists():
        existing = version_marker.read_text().strip()
        if existing == tag:
            print(f"llama-server {tag} already present at {binary_path}")
            return binary_path

    # Build URL
    pk = _detect_platform_key()
    ext = _archive_ext(pk)
    asset_name = f"llama-{tag}-bin-{pk}{ext}"
    url = f"{RELEASE_BASE}/{tag}/{asset_name}"

    # Download
    archive_bytes = _download(url)

    # Extract
    print(f"  Extracting {BINARY_NAME}...")
    result = _extract_binary(archive_bytes, pk, dest)

    # Write version marker
    version_marker.write_text(tag)

    print(f"  Installed: {result}")
    return result


def main() -> int:
    """CLI entry point."""
    tag = sys.argv[1] if len(sys.argv) > 1 else None
    try:
        download_llama_server(tag=tag)
    except SystemExit as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
