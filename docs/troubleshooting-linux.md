# Linux Troubleshooting

Common issues and fixes when running Templatr on Linux.

---

## 1. `libEGL.so.1: cannot open shared object file`

**Cause:** Missing Qt system dependency.

**Fix:**
```bash
# Debian / Ubuntu
sudo apt-get install -y libegl1 libxkbcommon0 libxcb-cursor0

# Fedora
sudo dnf install mesa-libEGL libxkbcommon xcb-util-cursor
```

---

## 2. AppImage won't run: `dlopen(): error loading libfuse.so.2`

**Cause:** FUSE 2 is required for AppImage but not installed by default on newer distros.

**Fix:**
```bash
# Debian / Ubuntu
sudo apt-get install -y libfuse2

# Fedora
sudo dnf install fuse-libs
```

---

## 3. `ModuleNotFoundError: No module named 'PyQt6'`

**Cause:** The Python dependencies are not installed, or you're using the wrong Python environment.

**Fix:**
```bash
# If using install.sh:
source .venv/bin/activate

# If using pip install:
pip install -e .[dev]
```

---

## 4. No templates appear after `pip install -e .`

**Cause:** `pip install` does not copy bundled templates into the config directory. This is a known gap that will be fixed in a future release.

**Workaround:**
```bash
mkdir -p ~/.config/templatr/templates
cp templates/*.json ~/.config/templatr/templates/
```

---

## 5. LLM server fails to start

**Cause:** The llama-server binary may not be downloaded or may lack execute permissions.

**Fix:**
```bash
# Check if the binary exists
ls -la ~/.local/share/templatr/llama.cpp/

# Re-download via the app: LLM → Download Server
# Or run the download script:
python scripts/download_llama_server.py
```

---

## File Locations

| What | Default Path |
|------|-------------|
| Config & Templates | `~/.config/templatr/` (or `$XDG_CONFIG_HOME/templatr/`) |
| LLM Server | `~/.local/share/templatr/` (or `$XDG_DATA_HOME/templatr/`) |
| Logs | `~/.config/templatr/logs/` |
| Models | `~/models/` |
