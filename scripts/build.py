#!/usr/bin/env python3
"""Build automation for Templatr.

Orchestrates the full build-and-package pipeline for the current platform:

1. Download pre-built ``llama-server`` if not already present.
2. Run PyInstaller with ``build.spec``.
3. Package the result into a platform-appropriate artifact:
   - Linux  → AppImage
   - macOS  → ``.app`` bundle in a ``.dmg``
   - Windows → directory-mode executable (zipped)

Usage::

    python scripts/build.py              # default: download + build + package
    python scripts/build.py --skip-download   # skip llama-server download
    python scripts/build.py --tag b8175       # pin llama-server release

"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = ROOT / "dist"
SPEC_FILE = ROOT / "build.spec"
VENDOR_DIR = ROOT / "vendor" / "llama-server"

APP_NAME = "templatr"
VERSION = None  # set lazily


def _get_version() -> str:
    """Read the version string from ``templatr/__init__.py``."""
    global VERSION
    if VERSION is None:
        init = ROOT / "templatr" / "__init__.py"
        for line in init.read_text().splitlines():
            if line.startswith("__version__"):
                VERSION = line.split("=")[1].strip().strip('"').strip("'")
                break
        else:
            VERSION = "0.0.0"
    return VERSION


def _run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    """Run a command, printing it first."""
    print(f"  → {' '.join(cmd)}")
    return subprocess.run(cmd, check=True, **kwargs)


# ------------------------------------------------------------------
# Step 1: download llama-server
# ------------------------------------------------------------------

def step_download(tag: str | None = None) -> None:
    """Download the llama-server binary if not present."""
    print("\n[1/3] Downloading llama-server binary...")
    sys.path.insert(0, str(ROOT / "scripts"))
    from download_llama_server import download_llama_server

    download_llama_server(tag=tag)


# ------------------------------------------------------------------
# Step 2: PyInstaller
# ------------------------------------------------------------------

def step_pyinstaller() -> None:
    """Run PyInstaller to produce the onedir bundle."""
    print("\n[2/3] Running PyInstaller...")
    _run([
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        str(SPEC_FILE),
    ])
    bundle_dir = DIST_DIR / APP_NAME
    if not bundle_dir.exists():
        raise SystemExit(f"PyInstaller did not produce {bundle_dir}")
    print(f"  Bundle: {bundle_dir}")


# ------------------------------------------------------------------
# Step 3: Platform packaging
# ------------------------------------------------------------------

def _package_linux() -> Path:
    """Create an AppImage from the PyInstaller output.

    Requires ``appimagetool`` on PATH (download from
    https://github.com/AppImage/appimagetool/releases).
    """
    version = _get_version()
    appdir = DIST_DIR / f"{APP_NAME}.AppDir"

    # Clean previous
    if appdir.exists():
        shutil.rmtree(appdir)
    appdir.mkdir(parents=True)

    # Copy bundle into AppDir/usr/bin/
    usr_bin = appdir / "usr" / "bin"
    usr_bin.mkdir(parents=True)
    shutil.copytree(DIST_DIR / APP_NAME, usr_bin / APP_NAME)

    # Create AppRun
    apprun = appdir / "AppRun"
    apprun.write_text(
        "#!/bin/bash\n"
        'SELF=$(readlink -f "$0")\n'
        'HERE=${SELF%/*}\n'
        f'exec "$HERE/usr/bin/{APP_NAME}/{APP_NAME}" "$@"\n'
    )
    apprun.chmod(0o755)

    # Desktop entry
    desktop = appdir / f"{APP_NAME}.desktop"
    desktop.write_text(
        f"[Desktop Entry]\n"
        f"Name=Templatr\n"
        f"Exec={APP_NAME}\n"
        f"Icon={APP_NAME}\n"
        f"Type=Application\n"
        f"Categories=Utility;\n"
    )

    # Placeholder icon (1×1 PNG — real icon can replace later)
    icon_path = appdir / f"{APP_NAME}.png"
    if not icon_path.exists():
        # Minimal 1×1 transparent PNG
        import base64
        icon_bytes = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVQI12NgAAIABQAB"
            "Nl7BcQAAAABJRU5ErkJggg=="
        )
        icon_path.write_bytes(icon_bytes)

    # Run appimagetool
    appimage_name = f"Templatr-{version}-x86_64.AppImage"
    output_path = DIST_DIR / appimage_name

    appimagetool = shutil.which("appimagetool")
    if appimagetool is None:
        print("  ⚠ appimagetool not found — AppDir created but AppImage not produced.")
        print("  Install from https://github.com/AppImage/appimagetool/releases")
        print(f"  Then run: appimagetool {appdir} {output_path}")
        return appdir

    env = os.environ.copy()
    env["ARCH"] = "x86_64"
    _run([appimagetool, str(appdir), str(output_path)], env=env)
    print(f"  AppImage: {output_path}")
    return output_path


def _package_macos() -> Path:
    """Create a .app bundle in a .dmg."""
    version = _get_version()
    machine = platform.machine()
    arch_label = "arm64" if machine == "arm64" else "x64"

    app_bundle = DIST_DIR / "Templatr.app"
    contents = app_bundle / "Contents"
    macos_dir = contents / "MacOS"
    resources = contents / "Resources"

    # Clean previous
    if app_bundle.exists():
        shutil.rmtree(app_bundle)

    macos_dir.mkdir(parents=True)
    resources.mkdir(parents=True)

    # Copy bundle into MacOS/
    shutil.copytree(DIST_DIR / APP_NAME, macos_dir / APP_NAME)

    # Launcher script
    launcher = macos_dir / "templatr-launcher"
    launcher.write_text(
        "#!/bin/bash\n"
        'DIR="$(cd "$(dirname "$0")" && pwd)"\n'
        f'exec "$DIR/{APP_NAME}/{APP_NAME}" "$@"\n'
    )
    launcher.chmod(0o755)

    # Info.plist
    plist = contents / "Info.plist"
    plist.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
        '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
        '<plist version="1.0">\n'
        '<dict>\n'
        f'  <key>CFBundleName</key><string>Templatr</string>\n'
        f'  <key>CFBundleDisplayName</key><string>Templatr</string>\n'
        f'  <key>CFBundleIdentifier</key><string>com.templatr.app</string>\n'
        f'  <key>CFBundleVersion</key><string>{version}</string>\n'
        f'  <key>CFBundleShortVersionString</key><string>{version}</string>\n'
        f'  <key>CFBundleExecutable</key><string>templatr-launcher</string>\n'
        f'  <key>CFBundlePackageType</key><string>APPL</string>\n'
        f'  <key>LSMinimumSystemVersion</key><string>12.0</string>\n'
        '</dict>\n'
        '</plist>\n'
    )

    # Create DMG
    dmg_name = f"Templatr-{version}-macos-{arch_label}.dmg"
    dmg_path = DIST_DIR / dmg_name

    if dmg_path.exists():
        dmg_path.unlink()

    hdiutil = shutil.which("hdiutil")
    if hdiutil is None:
        print("  ⚠ hdiutil not found — .app created but .dmg not produced.")
        return app_bundle

    _run([
        "hdiutil", "create",
        "-volname", "Templatr",
        "-srcfolder", str(app_bundle),
        "-ov",
        "-format", "UDZO",
        str(dmg_path),
    ])
    print(f"  DMG: {dmg_path}")
    return dmg_path


def _package_windows() -> Path:
    """Zip the Windows onedir bundle."""
    version = _get_version()
    zip_name = f"Templatr-{version}-win-x64"
    zip_path = DIST_DIR / zip_name

    if Path(f"{zip_path}.zip").exists():
        Path(f"{zip_path}.zip").unlink()

    shutil.make_archive(str(zip_path), "zip", str(DIST_DIR), APP_NAME)
    result = Path(f"{zip_path}.zip")
    print(f"  Archive: {result}")
    return result


def step_package() -> Path:
    """Package the build artifact for the current platform."""
    print("\n[3/3] Packaging platform artifact...")
    system = platform.system()

    if system == "Linux":
        return _package_linux()
    elif system == "Darwin":
        return _package_macos()
    elif system == "Windows":
        return _package_windows()
    else:
        print(f"  ⚠ No packaging step for {system} — raw bundle at dist/{APP_NAME}/")
        return DIST_DIR / APP_NAME


# ------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------

def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Build and package Templatr for the current platform.",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip the llama-server download step.",
    )
    parser.add_argument(
        "--tag",
        default=None,
        help="Pin the llama-server release tag (e.g. b8175).",
    )
    parser.add_argument(
        "--skip-package",
        action="store_true",
        help="Skip the platform packaging step (produce only the PyInstaller bundle).",
    )
    args = parser.parse_args()

    print(f"Building Templatr v{_get_version()} for {platform.system()} ({platform.machine()})")

    try:
        if not args.skip_download:
            step_download(tag=args.tag)

        step_pyinstaller()

        if not args.skip_package:
            artifact = step_package()
            print(f"\n✓ Build complete: {artifact}")
        else:
            print(f"\n✓ Build complete: {DIST_DIR / APP_NAME}")

    except subprocess.CalledProcessError as exc:
        print(f"\n✗ Build failed at command: {exc.cmd}", file=sys.stderr)
        return 1
    except SystemExit as exc:
        print(f"\n✗ {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
