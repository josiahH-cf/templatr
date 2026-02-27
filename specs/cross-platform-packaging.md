# Feature: Cross-Platform Packaging

## Description

Package the app as standalone executables for Linux, macOS, and Windows using PyInstaller, bundling pre-built llama-server binaries so users never need to compile anything. Each platform gets a native artifact format. `install.sh` remains for developer setup but is no longer the primary install path for end users.

## Acceptance Criteria

- [ ] A PyInstaller spec file produces a working standalone directory-mode executable for the current platform
- [ ] The Linux build produces an AppImage that launches on Ubuntu 22.04+ without installing any system dependencies
- [ ] The macOS build produces a `.app` bundle (in a `.dmg`) that launches on macOS 12+ (separate builds for Intel and Apple Silicon)
- [ ] The Windows build produces a directory-mode executable that launches on Windows 10+ without Python installed
- [ ] Each platform build bundles a pre-compiled `llama-server` binary (downloaded from llama.cpp GitHub releases, not compiled from source)
- [ ] The bundled app discovers its bundled llama-server binary before searching system paths
- [ ] A `scripts/build.py` script automates the full build-and-package process for the current platform

## Affected Areas

- New: `build.spec` (or `<appname>.spec`), `scripts/build.py`, `scripts/download_llama_server.py`
- Modified: `templatr/integrations/llm.py` (binary search order: bundled first), `templatr/core/config.py` (frozen-app base path detection via `sys._MEIPASS`)

## Constraints

- AppImage must be under 200 MB (CPU-only llama-server)
- `.dmg` must be under 200 MB
- Windows directory must be under 300 MB
- Must detect "am I running from a PyInstaller bundle?" at runtime and adjust resource paths accordingly
- Use CPU-only llama-server binaries for maximum compatibility; GPU variants deferred
- PyInstaller `--onedir` mode (more reliable cross-platform than `--onefile`)

## Out of Scope

- Auto-update mechanism within the app
- Microsoft Store / Mac App Store distribution
- Flatpak, Snap, or Homebrew packaging
- Code signing and notarization (follow-up spec)
- GPU-accelerated llama-server variants

## Dependencies

- Spec: `project-rename` — binary and bundle names depend on the final project name

## Notes

- Pre-built llama-server binaries: available at https://github.com/ggerganov/llama.cpp/releases — download the `llama-server` binary for each platform's CPU build.
- `scripts/download_llama_server.py`: fetches the correct binary for the current platform from llama.cpp releases, verifies checksum, places it in `vendor/llama-server`.
- Frozen-app detection: `getattr(sys, '_MEIPASS', None)` returns the temp extraction dir. Use `sys._MEIPASS / 'vendor' / 'llama-server'` as the first binary search path.
- `install.sh` continues to work for developers who prefer editable installs and building llama.cpp from source.
