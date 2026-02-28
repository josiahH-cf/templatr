# Templatr

[![CI](https://github.com/josiahH-cf/templatr/actions/workflows/ci.yml/badge.svg)](https://github.com/josiahH-cf/templatr/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/josiahH-cf/templatr)](https://github.com/josiahH-cf/templatr/releases/latest)
![Platforms](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows-blue)

**Create reusable AI prompts that run 100% on your computer.**

No cloud. No API keys. No subscriptions. Just you and your local AI.

![Main Chat View](docs/images/main-chat-view.png)

---

## What is Templatr?

Templatr helps you build **prompt templates** — reusable prompts with fill-in-the-blank variables. Think of them like form letters for AI.

**Example:** Instead of retyping "Review this code for bugs..." every time, create a template once and reuse it forever.

### Your Data Stays Private

Everything runs on your computer:

- No internet connection required (after initial setup)
- No accounts or sign-ups
- Your prompts never leave your machine

---

## Quick Start

### Linux (x86_64)

Pre-built binaries are available for x86_64 Linux. ARM64 is not yet supported for pre-built releases.

1. Go to the [Releases page](https://github.com/josiahH-cf/templatr/releases/latest)
2. Download `templatr-linux.AppImage` (or the `.AppDir` fallback)
3. Make it executable:
   ```bash
   chmod +x templatr-linux.AppImage
   ```
4. Run it:
   ```bash
   ./templatr-linux.AppImage
   ```

**Developer install (from source):**
```bash
git clone https://github.com/josiahH-cf/templatr.git
cd templatr
./install.sh
```

### macOS

1. Go to the [Releases page](https://github.com/josiahH-cf/templatr/releases/latest)
2. Download the `.dmg` for your architecture:
   - **Apple Silicon (M1/M2/M3):** `templatr-macos-latest.dmg`
   - **Intel:** `templatr-macos-13.dmg`
3. Open the `.dmg` and drag **Templatr** to Applications
4. Launch Templatr from Applications

**Developer install (from source):**
```bash
git clone https://github.com/josiahH-cf/templatr.git
cd templatr
./install.sh
```

### Windows

> **Note:** Native Windows development builds are not yet supported. For development, use WSL2 (see [CONTRIBUTING.md](CONTRIBUTING.md)).

1. Go to the [Releases page](https://github.com/josiahH-cf/templatr/releases/latest)
2. Download the `templatr-windows.zip`
3. Extract the zip to a folder of your choice
4. Run `templatr.exe` from the extracted folder

---

## Getting an AI Model

You need a `.gguf` model file — this is the "brain" that generates responses.

1. Launch Templatr
2. Go to **LLM → Download Models (Hugging Face)**
3. Download any model (start small, around 3–8 GB)
4. Go to **LLM → Select Model → Add Model from File...**
5. Pick your downloaded `.gguf` file

**Tip:** Smaller models run faster. Larger ones are smarter but slower. Any `.gguf` format model works — browse [Hugging Face](https://huggingface.co/models?search=gguf) for options.

---

## Creating Your First Template

1. Open the chat and type `/new`
2. Give your template a name (e.g., "Code Review")
3. Write your prompt using `{{variables}}` for the blanks:
   ```
   Review this {{language}} code for bugs and improvements:

   {{code}}
   ```
4. Your template is saved and immediately available as a `/` command

See [TEMPLATES.md](TEMPLATES.md) for the full template authoring guide, including import/export and advanced editing.

---

## System Requirements

| Requirement | Minimum |
|-------------|---------|
| **OS** | Linux (x86_64), macOS (Intel or Apple Silicon), or Windows 10+ |
| **Python** | 3.10 or newer (source install only; not needed for pre-built binaries) |
| **RAM** | 8 GB (16 GB recommended) |
| **Storage** | 10 GB free for models |

---

## Where Files Are Stored

### Linux / WSL2

| What | Location |
|------|----------|
| Settings & Templates | `~/.config/templatr/` (or `$XDG_CONFIG_HOME/templatr/`) |
| LLM Server | `~/.local/share/templatr/` (or `$XDG_DATA_HOME/templatr/`) |
| Models | `~/models/` |

### macOS

| What | Location |
|------|----------|
| Settings & Templates | `~/Library/Application Support/templatr/` |
| Models | `~/models/` |

### Windows (pre-built binary)

| What | Location |
|------|----------|
| Settings & Templates | `%APPDATA%\templatr\` |
| Data | `%LOCALAPPDATA%\templatr\` |
| Models | `%USERPROFILE%\models\` |

> **Tip:** Run `templatr --doctor` to see your exact platform-specific paths and check for missing dependencies.

**To remove everything:**
```bash
# Linux / WSL2
rm -rf ~/.config/templatr/ ~/.local/share/templatr/ ~/models/*.gguf

# macOS
rm -rf ~/Library/Application\ Support/templatr/ ~/models/*.gguf

# Windows (PowerShell)
Remove-Item -Recurse "$env:APPDATA\templatr", "$env:LOCALAPPDATA\templatr"
```

---

## Common Questions

**Q: Do I need internet?**
A: Only to download the app and a model. After that, everything works offline.

**Q: Is it free?**
A: Yes, completely free and open source (MIT license).

**Q: What models work?**
A: Any `.gguf` format model. Browse [Hugging Face](https://huggingface.co/models?search=gguf) for options.

**Q: It's slow. What can I do?**
A: Use a smaller model, or upgrade your hardware. A GPU helps significantly.

**Q: Is there an Espanso integration?**
A: Espanso support lives in a separate project: [templatr-espanso](https://github.com/josiahH-cf/templatr-espanso).

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for developer setup, testing, and PR guidelines.

---

## License

MIT — see [LICENSE](LICENSE) for details.

---

<p align="center">
  Made with care for people who value privacy
</p>
