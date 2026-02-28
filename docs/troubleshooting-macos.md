# macOS Troubleshooting

Common issues and fixes when running Templatr on macOS.

---

## 1. "Templatr can't be opened because it is from an unidentified developer"

**Cause:** macOS Gatekeeper blocks unsigned apps by default.

**Fix:**
1. Open **System Settings → Privacy & Security**
2. Scroll down to the security section
3. Click **Open Anyway** next to the Templatr message

Or from the terminal:
```bash
xattr -cr /Applications/Templatr.app
```

---

## 2. Error messages reference `~/.config/templatr`

**Cause:** Some error messages in the app incorrectly reference the Linux config path. On macOS, the actual path is different.

**Correct path:** `~/Library/Application Support/templatr/`

This is a known issue that will be fixed in a future release (see [platform-config-consolidation](../specs/platform-config-consolidation.md)). When you see `~/.config/templatr` in an error message, mentally replace it with `~/Library/Application Support/templatr/`.

---

## 3. No templates appear after `pip install -e .`

**Cause:** `pip install` does not copy bundled templates into the config directory.

**Workaround:**
```bash
mkdir -p ~/Library/Application\ Support/templatr/templates
cp templates/*.json ~/Library/Application\ Support/templatr/templates/
```

This will be fixed when first-run template seeding is added (see [platform-config-consolidation](../specs/platform-config-consolidation.md)).

---

## 4. `ModuleNotFoundError: No module named 'PyQt6'`

**Cause:** The Python dependencies are not installed.

**Fix:**
```bash
# If using install.sh:
source .venv/bin/activate

# If using pip install:
pip install -e .[dev]
```

---

## 5. LLM server fails to start

**Cause:** The llama-server binary may not be downloaded or macOS may quarantine it.

**Fix:**
```bash
# Check the binary
ls -la ~/Library/Application\ Support/templatr/llama.cpp/

# Remove quarantine attribute if needed
xattr -cr ~/Library/Application\ Support/templatr/llama.cpp/llama-server

# Or re-download via: LLM → Download Server
```

---

## File Locations

| What | Default Path |
|------|-------------|
| Config & Templates | `~/Library/Application Support/templatr/` |
| Logs | `~/Library/Application Support/templatr/logs/` |
| Models | `~/models/` |
