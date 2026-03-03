# Feature: orchestratr Connector

**Status:** Implemented (install.sh integration pending)
**Project:** templatr

## Description

templatr has no orchestratr integration. This spec builds the full connector — matching the pattern established by espansr — so orchestratr can discover, launch, health-check, and focus templatr via a hotkey chord. The implementation adds a CLI `status --json` command, a connector module that generates a drop-in manifest for orchestratr's `apps.d/` directory, GUI integration via a new Integrations settings dialog, and WSL2-aware path resolution.

### Reference Implementation

espansr's connector (`espansr/integrations/orchestratr.py`) is the reference implementation. After the schema alignment spec is applied to espansr, the connector pattern is:

1. **Manifest generation**: Write a flat YAML file to `~/.config/orchestratr/apps.d/<appname>.yml` (or the Windows-side path from WSL2) with fields: `name`, `chord`, `command`, `environment`, `description`, `ready_cmd`, `ready_timeout_ms`
2. **Status JSON**: CLI command that outputs `{"version": "...", "status": "ok"|"degraded", ...}` with app-specific health fields
3. **Setup integration**: App's setup/install flow writes the manifest; re-runs on version change
4. **Passive design**: If orchestratr isn't installed, the connector does nothing. No imports, no runtime dependency.

### Current State (Context for Implementation)

- **Entry point** (`templatr/__main__.py`): `main()` uses `argparse` with `--version` and `--doctor` flags. No subcommands. Default action launches the GUI.
- **UI**: PyQt6 app with menu bar (File, LLM, Help), template tree, chat widget, LLM toolbar in status bar. Settings dialog exists for LLM (`ui/llm_settings.py`). No integrations/connector UI.
- **Integrations package** (`templatr/integrations/`): Contains only `llm.py` (llama.cpp server integration). No `__init__.py` module-level orchestratr references.
- **Platform detection**: `templatr/core/platform.py` handles platform-specific paths. Uses `XDG_CONFIG_HOME` on Linux, `~/Library/Application Support` on macOS, `%APPDATA%` on Windows.
- **Version**: `1.2.0` in `pyproject.toml`, `1.1.0` in `__init__.py` (mismatch to reconcile).
- **PyYAML**: Listed in dependencies already (`pyyaml` in `pyproject.toml`).

### Target Behavior

After this spec:
- `templatr` — launches GUI (unchanged)
- `templatr status --json` — outputs health JSON, exits 0
- `templatr --doctor` — existing diagnostics (unchanged)
- `templatr --version` — prints version (unchanged)
- First GUI launch after install/update shows a status bar hint if orchestratr manifest is stale
- Integrations dialog (menu: File → Integrations) shows orchestratr registration status with Register/Re-register button

## Acceptance Criteria

- [ ] `templatr status --json` outputs valid JSON with: `version`, `status` ("ok" or "degraded"), `config_dir`, `template_count`, `llm_server_status` ("running", "stopped", or "unknown"), `model_loaded` (string or null)
- [ ] `templatr status --json` returns exit code 0 on success
- [ ] When `status` is "degraded", JSON includes an `errors` array with human-readable strings (e.g., "No templates found", "LLM server not running")
- [ ] `templatr/integrations/orchestratr.py` exists with `generate_manifest()`, `manifest_needs_update()`, `get_status_json()`, `resolve_orchestratr_apps_dir()`
- [ ] Manifest is written to orchestratr's `apps.d/templatr.yml` with flat `AppEntry` schema: `name: templatr`, `chord: "t"`, `command: "templatr"`, `environment`, `description`, `ready_cmd: "templatr status --json"`, `ready_timeout_ms: 5000`
- [ ] On native Linux: manifest targets `~/.config/orchestratr/apps.d/templatr.yml`, `environment: native`
- [ ] On WSL2: manifest targets `/mnt/c/Users/<username>/AppData/Roaming/orchestratr/apps.d/templatr.yml`, `environment: wsl`
- [ ] `command` and `ready_cmd` are bare commands (never pre-wrapped with `wsl.exe`)
- [ ] If orchestratr's `apps.d/` parent directory doesn't exist, manifest generation is skipped with a non-fatal info message
- [ ] GUI Integrations dialog (File → Integrations) shows: orchestratr registration status (registered/not registered/stale), manifest path, suggested chord, Register/Re-register button
- [ ] On app startup, if manifest is stale (version mismatch or missing), a dismissible status bar hint appears: "orchestratr registration is outdated. Update via File → Integrations."
- [ ] Connector is fully passive — if orchestratr is not installed, all behavior is unchanged, no errors
- [ ] Tests cover: manifest generation, flat schema validation, status JSON output, CLI flag, path resolution (Linux, WSL2), GUI dialog (mock-based)

## Affected Areas

| Area | Files |
|------|-------|
| **Create** | `templatr/integrations/orchestratr.py` — manifest generation, status JSON, path resolution |
| **Create** | `templatr/ui/integration_settings.py` — Integrations settings dialog (PyQt6) |
| **Create** | `tests/test_orchestratr_connector.py` — connector tests |
| **Modify** | `templatr/__main__.py` — add `status` subcommand with `--json` flag, refactor argparse for subcommands |
| **Modify** | `templatr/ui/main_window.py` — add File → Integrations menu item, startup manifest staleness check + status bar hint |
| **Modify** | `templatr/integrations/__init__.py` — export orchestratr module (if `__init__.py` manages imports) |

## Constraints

- No new dependencies — PyYAML is already in `templatr`'s dependencies
- The `status` subcommand must not launch the GUI — it's a headless CLI operation
- CLI refactor: `templatr` (no args) must continue to launch the GUI for backward compatibility. Use `argparse` subcommands with a default action.
- `status --json` output is a machine-readable contract — fields and types must be stable
- Integrations dialog must not block application startup
- Status bar hint must be non-intrusive (auto-dismiss after 10s or manual dismiss)
- The connector module must have zero side effects on import — all actions triggered by explicit function calls

## Out of Scope

- Modifying orchestratr code (handled by orchestratr's own specs)
- Modifying espansr code (handled by espansr's own spec)
- Auto-registration on `pip install` (registration happens on first GUI launch or explicit CLI call)
- Continuous health reporting to orchestratr (orchestratr polls `ready_cmd`; templatr doesn't push)

## Dependencies

- **orchestratr `drop-in-app-discovery.md`** — defines the `apps.d/` directory and manifest schema. Can be developed in parallel (schema is agreed), but manifests won't be discovered until orchestratr implements scanning.

## Notes

### CLI subcommand refactor

Current argparse:
```python
parser = argparse.ArgumentParser(...)
parser.add_argument("--version", ...)
parser.add_argument("--doctor", ...)
```

Refactored:
```python
parser = argparse.ArgumentParser(...)
parser.add_argument("--version", action="version", ...)
subparsers = parser.add_subparsers(dest="command")

# templatr status --json
status_parser = subparsers.add_parser("status", help="Show app status")
status_parser.add_argument("--json", action="store_true", help="Output as JSON")

# templatr gui (explicit, optional)
subparsers.add_parser("gui", help="Launch the GUI")

# templatr --doctor (keep as top-level flag for backward compat)
parser.add_argument("--doctor", action="store_true", ...)

args = parser.parse_args()
if args.command == "status":
    cmd_status(args)
elif args.command == "gui" or args.command is None:
    run_gui()  # default action
```

### Status JSON format

```json
{
  "version": "1.2.0",
  "status": "ok",
  "config_dir": "/home/user/.config/templatr",
  "template_count": 12,
  "llm_server_status": "running",
  "model_loaded": "mistral-7b-instruct-v0.3.Q4_K_M.gguf"
}
```

Degraded example:
```json
{
  "version": "1.2.0",
  "status": "degraded",
  "config_dir": "/home/user/.config/templatr",
  "template_count": 0,
  "llm_server_status": "stopped",
  "model_loaded": null,
  "errors": ["No templates found", "LLM server not running"]
}
```

### Manifest format

```yaml
# orchestratr app manifest — written by templatr
name: templatr
chord: "t"
command: "templatr"
environment: native  # or "wsl" on WSL2
description: "Local-model prompt optimizer"
ready_cmd: "templatr status --json"
ready_timeout_ms: 5000
```

### Cross-platform path resolution

Reuse the same algorithm as espansr (defined in the workspace connector protocol doc):

```python
def resolve_orchestratr_apps_dir() -> Optional[Path]:
    platform = detect_platform()
    if platform == "wsl2":
        win_user = _resolve_windows_username()
        base = Path(f"/mnt/c/Users/{win_user}/AppData/Roaming/orchestratr")
    elif platform == "macos":
        base = Path.home() / "Library" / "Application Support" / "orchestratr"
    else:  # linux
        xdg = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
        base = Path(xdg) / "orchestratr"
    
    if not base.exists():
        return None  # orchestratr not installed
    return base / "apps.d"
```

### Integrations dialog design

```
╔══════════════════════════════════════════════╗
║  Integrations                         [ x ]  ║
╠══════════════════════════════════════════════╣
║                                              ║
║  orchestratr                                 ║
║  ─────────────────────────────────           ║
║  Status: ● Registered (v1.2.0)              ║
║  Manifest: ~/.config/orchestratr/apps.d/     ║
║            templatr.yml                      ║
║  Chord: t                                    ║
║                                              ║
║  [ Re-register ]                             ║
║                                              ║
║  ─── or if not registered ───                ║
║                                              ║
║  Status: ○ Not registered                    ║
║  orchestratr not detected.                   ║
║  Install orchestratr to enable hotkey        ║
║  launching.                                  ║
║                                              ║
╠══════════════════════════════════════════════╣
║                          [ Close ]           ║
╚══════════════════════════════════════════════╝
```

### Version mismatch detection

`manifest_needs_update()` checks:
1. Manifest file exists at expected path
2. YAML is parseable
3. `name` field matches "templatr"
4. Manifest version indicator (can use a comment or compare `command`/`ready_cmd` fields)
5. App version from `templatr.__version__` hasn't changed since last write (store version as a YAML comment or dedicated field that orchestratr ignores)

Practical approach: write a `# templatr_version: 1.2.0` comment in the manifest. On update check, read the comment. If version differs or comment missing, manifest is stale.
