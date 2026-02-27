# 🤖 Templatr

[![CI](https://github.com/josiahH-cf/templatr/actions/workflows/ci.yml/badge.svg)](https://github.com/josiahH-cf/templatr/actions/workflows/ci.yml)

**Create reusable AI prompts that run 100% on your computer.**

No cloud. No API keys. No subscriptions. Just you and your local AI.

![Templatr Screenshot](docs/screenshot.png)
<!-- TODO: Add screenshot showing the main window with a template -->

---

## ✨ What is Templatr?

Templatr helps you build **prompt templates** — reusable prompts with fill-in-the-blank variables. Think of them like form letters for AI.

**Example:** Instead of retyping "Review this code for bugs..." every time, create a template once and reuse it forever.

### 🔒 Your Data Stays Private

Everything runs on your computer:
- ✅ No internet connection required (after setup)
- ✅ No accounts or sign-ups
- ✅ Your prompts never leave your machine

---

## 🚀 Getting Started

### Step 1: Install

Open a terminal and run:

```bash
git clone https://github.com/josiahH-cf/templatr.git
cd templatr
./install.sh
```

This takes 5-10 minutes. It downloads and sets up everything automatically.

### Step 2: Get an AI Model

You need a `.gguf` model file — this is the "brain" that generates responses.

1. Launch Templatr: `templatr`
2. Go to **LLM → Download Models (Hugging Face)**
3. Download any model (start small, around 3-8GB)
4. Go to **LLM → Select Model → Add Model from File...**
5. Pick your downloaded `.gguf` file

**💡 Tip:** Smaller models run faster. Larger ones are smarter but slower.

### Step 3: Create Your First Template

1. Click **New Template**
2. Give it a name like "Code Review"
3. Write your prompt using `{{variables}}` for the blanks:
   ```
   Review this {{language}} code for bugs and improvements:
   
   {{code}}
   ```
4. Click **Save**

Now you can reuse this template anytime — just fill in the blanks!

---

## 💻 System Requirements

| Requirement | Minimum |
|-------------|---------|
| **OS** | Linux, macOS, or Windows (via WSL2) |
| **Python** | 3.10 or newer |
| **RAM** | 8GB (16GB recommended) |
| **Storage** | 10GB free for models |

---

## 🗂️ Where Files Are Stored

**Linux / WSL2:**
| What | Location |
|------|----------|
| Settings & Templates | `~/.config/templatr/` |
| LLM Server | `~/.local/share/templatr/` |
| Models | `~/models/` |

**macOS:**
| What | Location |
|------|----------|
| Settings & Templates | `~/Library/Application Support/templatr/` |
| Models | `~/models/` |

**To remove everything:**
```bash
# 1. Uninstall the Python package
cd ~/templatr
source .venv/bin/activate
pip uninstall templatr -y

# 2. Remove the repository and virtual environment
cd ~
rm -rf ~/templatr

# 3. Remove user data (Linux/WSL2)
rm -rf ~/.config/templatr/ ~/.local/share/templatr/

# 3. Remove user data (macOS)
# rm -rf ~/Library/Application\ Support/templatr/

# 4. Remove models (optional — these are large files you downloaded)
# rm -rf ~/models/*.gguf

# 5. Remove the shell alias from your shell config
# Edit ~/.bashrc, ~/.bashrc.d/10-aliases.sh, or ~/.zshrc
# and remove the line: alias templatr='...'
```

### Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `XDG_CONFIG_HOME` | `~/.config` | Override config/templates directory (Linux/WSL) |
| `QT_QPA_PLATFORM` | auto | Force Qt platform (e.g., `offscreen` for headless, `xcb` for X11) |

**Config file:** `~/.config/templatr/config.json` — edit directly or use the Settings dialog.

Key settings:
- `llm.server_port` — llama-server port (default: 8080)
- `llm.gpu_layers` — GPU layers for acceleration (0 = CPU only)
- `llm.context_size` — Token context window (default: 4096)
- `llm.model_dir` — Directory to scan for GGUF models (default: `~/models`)
- `ui.theme` — `"dark"` or `"light"`

**Update llama.cpp:** `./install.sh --update-llama`

---

## ❓ Common Questions

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

## 📄 License

MIT — use it however you want.

---

<p align="center">
  Made with ❤️ for people who value privacy
</p>
