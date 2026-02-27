# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Templatr.

Produces a directory-mode (--onedir) bundle including:
- The ``templatr`` Python package
- Bundled ``templates/`` (including ``_meta/``)
- Vendored ``llama-server`` binary (``vendor/llama-server/``)

Run via ``pyinstaller build.spec`` or through ``scripts/build.py``.
"""

import os
import sys
from pathlib import Path

# Paths are relative to the repo root (where this spec lives)
ROOT = Path(SPECPATH)
VENDOR_BIN = ROOT / "vendor" / "llama-server"
TEMPLATES_DIR = ROOT / "templates"

# ------------------------------------------------------------------
# Collect data files
# ------------------------------------------------------------------
datas = []

# Bundled templates (shipped with the app)
if TEMPLATES_DIR.exists():
    datas.append((str(TEMPLATES_DIR), "templates"))

# Vendored llama-server binary
if VENDOR_BIN.exists():
    datas.append((str(VENDOR_BIN), os.path.join("vendor", "llama-server")))

# ------------------------------------------------------------------
# Analysis
# ------------------------------------------------------------------
a = Analysis(
    [str(ROOT / "templatr" / "__main__.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "templatr",
        "templatr.core",
        "templatr.core.config",
        "templatr.core.templates",
        "templatr.core.meta_templates",
        "templatr.core.feedback",
        "templatr.core.interfaces",
        "templatr.core.logging_setup",
        "templatr.integrations",
        "templatr.integrations.llm",
        "templatr.ui",
        "templatr.ui.main_window",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "unittest",
        "test",
        "pytest",
        "black",
        "ruff",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="templatr",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUI app — no console window
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="templatr",
)
