# Windows Troubleshooting

Common issues and fixes when running Templatr on Windows.

---

## 1. "Run the PowerShell installer" message from `install.sh`

**Cause:** If you run `install.sh` on native Windows (Git Bash, MSYS2, Cygwin), it detects Windows and suggests using a PowerShell installer. **This PowerShell installer does not exist.** The message is a known bug.

**What to do instead:**
- **Recommended:** Download the pre-built binary from the [Releases page](https://github.com/josiahH-cf/templatr/releases/latest) — no installer needed
- **For development:** Use [WSL2](https://learn.microsoft.com/en-us/windows/wsl/install) and follow the Linux setup instructions

This will be fixed in a future release (see [platform-config-consolidation](../specs/platform-config-consolidation.md)).

---

## 2. Native Windows development is not supported

**Cause:** The development toolchain (install.sh, llama-server binary management) is designed for Unix-like systems. Native Windows dev builds do not work.

**What to do:**
- For **using** Templatr: download the pre-built `.zip` from [Releases](https://github.com/josiahH-cf/templatr/releases/latest), extract, and run `templatr.exe`
- For **developing** Templatr: install [WSL2](https://learn.microsoft.com/en-us/windows/wsl/install), then follow the standard Linux setup in [CONTRIBUTING.md](../CONTRIBUTING.md)

---

## 3. `templatr.exe` won't start or crashes immediately

**Possible causes:**
- Missing Visual C++ Redistributable — install [vc_redist.x64.exe](https://aka.ms/vs/17/release/vc_redist.x64.exe) from Microsoft
- Antivirus quarantined the binary — add an exception for the Templatr folder
- Corrupted download — re-download the zip from Releases

---

## 4. Windows Defender SmartScreen warning

**Cause:** The binary is not code-signed.

**Fix:** Click **More info** → **Run anyway**. The app is open source — you can verify the source at [github.com/josiahH-cf/templatr](https://github.com/josiahH-cf/templatr).

---

## 5. Models not found

**Cause:** The app looks for models in `~/models/` by default.

**Fix:** Ensure your `.gguf` model files are in your user home's `models` folder (e.g., `C:\Users\YourName\models\`). Or use **LLM → Select Model → Add Model from File...** to point to any location.

---

## File Locations (Pre-built Binary)

| What | Default Path |
|------|-------------|
| Settings & Templates | Stored alongside the extracted application |
| Models | `%USERPROFILE%\models\` |

> **Note:** Windows file paths are only standardized for the pre-built binary. If you're developing via WSL2, Linux paths apply instead. See [platform-config-consolidation](../specs/platform-config-consolidation.md) for planned improvements to Windows path handling.
