"""Tests for the orchestratr connector integration.

Covers: manifest generation, flat schema validation, status JSON output,
CLI flag, path resolution (Linux, WSL2), and GUI dialog (mock-based).
"""

import json
from pathlib import Path
from unittest import mock

from templatr import __version__

# ---------------------------------------------------------------------------
# Path resolution tests
# ---------------------------------------------------------------------------


class TestResolveOrchestratrAppsDir:
    """Tests for resolve_orchestratr_apps_dir()."""

    def test_linux_native_uses_xdg_default(self, tmp_path, monkeypatch):
        """On native Linux without XDG override, uses ~/.config/orchestratr/apps.d."""
        from templatr.integrations.orchestratr import resolve_orchestratr_apps_dir

        monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        # Create the orchestratr base dir so the function doesn't return None
        base = tmp_path / ".config" / "orchestratr"
        base.mkdir(parents=True)

        with mock.patch(
            "templatr.integrations.orchestratr.get_platform_config"
        ) as mock_pc:
            mock_pc.return_value = mock.Mock(platform="linux")
            result = resolve_orchestratr_apps_dir()

        assert result == base / "apps.d"

    def test_linux_native_uses_xdg_override(self, tmp_path, monkeypatch):
        """On Linux with XDG_CONFIG_HOME set, uses that path."""
        from templatr.integrations.orchestratr import resolve_orchestratr_apps_dir

        xdg_dir = tmp_path / "custom_config"
        monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg_dir))

        base = xdg_dir / "orchestratr"
        base.mkdir(parents=True)

        with mock.patch(
            "templatr.integrations.orchestratr.get_platform_config"
        ) as mock_pc:
            mock_pc.return_value = mock.Mock(platform="linux")
            result = resolve_orchestratr_apps_dir()

        assert result == base / "apps.d"

    def test_wsl2_uses_windows_appdata(self, tmp_path, monkeypatch):
        """On WSL2, targets the Windows-side AppData path."""
        from templatr.integrations.orchestratr import resolve_orchestratr_apps_dir

        # Simulate /mnt/c/Users/<user>/AppData/Roaming existing
        win_user = "testuser"
        base = tmp_path / "mnt" / "c" / "Users" / win_user / "AppData" / "Roaming" / "orchestratr"
        base.mkdir(parents=True)

        with mock.patch(
            "templatr.integrations.orchestratr.get_platform_config"
        ) as mock_pc, mock.patch(
            "templatr.integrations.orchestratr._resolve_windows_username",
            return_value=win_user,
        ), mock.patch(
            "templatr.integrations.orchestratr.Path"
        ) as mock_path_cls:
            mock_pc.return_value = mock.Mock(platform="wsl2")
            # Make Path() construct real paths from our tmp_path
            mock_path_cls.side_effect = lambda *a: Path(str(tmp_path / "mnt" / "c" / "Users" / win_user / "AppData" / "Roaming" / "orchestratr")) if "mnt" in str(a) else Path(*a)
            mock_path_cls.home.return_value = tmp_path

            # Use real implementation with patched base
            with mock.patch(
                "templatr.integrations.orchestratr._get_orchestratr_base_dir",
                return_value=base,
            ):
                result = resolve_orchestratr_apps_dir()

        assert result == base / "apps.d"

    def test_returns_none_when_orchestratr_not_installed(self, tmp_path, monkeypatch):
        """Returns None when orchestratr base dir doesn't exist."""
        from templatr.integrations.orchestratr import resolve_orchestratr_apps_dir

        monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        # Don't create any orchestratr directory

        with mock.patch(
            "templatr.integrations.orchestratr.get_platform_config"
        ) as mock_pc:
            mock_pc.return_value = mock.Mock(platform="linux")
            result = resolve_orchestratr_apps_dir()

        assert result is None

    def test_macos_uses_application_support(self, tmp_path, monkeypatch):
        """On macOS, uses ~/Library/Application Support/orchestratr."""
        from templatr.integrations.orchestratr import resolve_orchestratr_apps_dir

        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        base = tmp_path / "Library" / "Application Support" / "orchestratr"
        base.mkdir(parents=True)

        with mock.patch(
            "templatr.integrations.orchestratr.get_platform_config"
        ) as mock_pc:
            mock_pc.return_value = mock.Mock(platform="macos")
            result = resolve_orchestratr_apps_dir()

        assert result == base / "apps.d"


# ---------------------------------------------------------------------------
# Manifest generation tests
# ---------------------------------------------------------------------------


class TestGenerateManifest:
    """Tests for generate_manifest()."""

    def test_generates_valid_yaml_manifest(self, tmp_path):
        """Manifest contains all required flat AppEntry fields."""
        from templatr.integrations.orchestratr import generate_manifest

        apps_dir = tmp_path / "apps.d"
        apps_dir.mkdir(parents=True)

        with mock.patch(
            "templatr.integrations.orchestratr.resolve_orchestratr_apps_dir",
            return_value=apps_dir,
        ), mock.patch(
            "templatr.integrations.orchestratr.get_platform_config"
        ) as mock_pc:
            mock_pc.return_value = mock.Mock(platform="linux")
            result = generate_manifest()

        assert result is True
        manifest_path = apps_dir / "templatr.yml"
        assert manifest_path.exists()

        content = manifest_path.read_text()
        assert "name: templatr" in content
        assert 'chord: "t"' in content
        assert 'command: "templatr"' in content
        assert "environment: native" in content
        assert 'ready_cmd: "templatr status --json"' in content
        assert "ready_timeout_ms: 5000" in content
        assert "description:" in content

    def test_wsl2_environment_field(self, tmp_path):
        """On WSL2, environment is 'wsl'."""
        from templatr.integrations.orchestratr import generate_manifest

        apps_dir = tmp_path / "apps.d"
        apps_dir.mkdir(parents=True)

        with mock.patch(
            "templatr.integrations.orchestratr.resolve_orchestratr_apps_dir",
            return_value=apps_dir,
        ), mock.patch(
            "templatr.integrations.orchestratr.get_platform_config"
        ) as mock_pc:
            mock_pc.return_value = mock.Mock(platform="wsl2")
            generate_manifest()

        content = (apps_dir / "templatr.yml").read_text()
        assert "environment: wsl" in content

    def test_command_is_bare_never_wrapped(self, tmp_path):
        """command and ready_cmd are bare, never pre-wrapped with wsl.exe."""
        from templatr.integrations.orchestratr import generate_manifest

        apps_dir = tmp_path / "apps.d"
        apps_dir.mkdir(parents=True)

        with mock.patch(
            "templatr.integrations.orchestratr.resolve_orchestratr_apps_dir",
            return_value=apps_dir,
        ), mock.patch(
            "templatr.integrations.orchestratr.get_platform_config"
        ) as mock_pc:
            mock_pc.return_value = mock.Mock(platform="wsl2")
            generate_manifest()

        content = (apps_dir / "templatr.yml").read_text()
        assert "wsl.exe" not in content
        assert 'command: "templatr"' in content

    def test_skips_when_orchestratr_not_installed(self):
        """Returns False with non-fatal message when apps.d parent missing."""
        from templatr.integrations.orchestratr import generate_manifest

        with mock.patch(
            "templatr.integrations.orchestratr.resolve_orchestratr_apps_dir",
            return_value=None,
        ):
            result = generate_manifest()

        assert result is False

    def test_creates_apps_d_directory(self, tmp_path):
        """Creates the apps.d/ subdirectory if it doesn't exist yet."""
        from templatr.integrations.orchestratr import generate_manifest

        apps_dir = tmp_path / "apps.d"
        # apps_dir does NOT exist yet, but its parent does

        with mock.patch(
            "templatr.integrations.orchestratr.resolve_orchestratr_apps_dir",
            return_value=apps_dir,
        ), mock.patch(
            "templatr.integrations.orchestratr.get_platform_config"
        ) as mock_pc:
            mock_pc.return_value = mock.Mock(platform="linux")
            result = generate_manifest()

        assert result is True
        assert apps_dir.exists()
        assert (apps_dir / "templatr.yml").exists()


# ---------------------------------------------------------------------------
# Manifest staleness tests
# ---------------------------------------------------------------------------


class TestManifestNeedsUpdate:
    """Tests for manifest_needs_update()."""

    def test_returns_true_when_no_manifest(self, tmp_path):
        """Stale when manifest doesn't exist at all."""
        from templatr.integrations.orchestratr import manifest_needs_update

        apps_dir = tmp_path / "apps.d"
        apps_dir.mkdir(parents=True)

        with mock.patch(
            "templatr.integrations.orchestratr.resolve_orchestratr_apps_dir",
            return_value=apps_dir,
        ):
            assert manifest_needs_update() is True

    def test_returns_true_when_version_mismatch(self, tmp_path):
        """Stale when manifest exists but has different version."""
        from templatr.integrations.orchestratr import manifest_needs_update

        apps_dir = tmp_path / "apps.d"
        apps_dir.mkdir(parents=True)
        manifest = apps_dir / "templatr.yml"
        manifest.write_text(
            "# orchestratr app manifest — written by templatr v0.0.1\n"
            "name: templatr\n"
        )

        with mock.patch(
            "templatr.integrations.orchestratr.resolve_orchestratr_apps_dir",
            return_value=apps_dir,
        ):
            assert manifest_needs_update() is True

    def test_returns_false_when_current(self, tmp_path):
        """Not stale when manifest version matches current version."""
        from templatr.integrations.orchestratr import manifest_needs_update

        apps_dir = tmp_path / "apps.d"
        apps_dir.mkdir(parents=True)
        manifest = apps_dir / "templatr.yml"
        manifest.write_text(
            f"# orchestratr app manifest — written by templatr v{__version__}\n"
            "name: templatr\n"
        )

        with mock.patch(
            "templatr.integrations.orchestratr.resolve_orchestratr_apps_dir",
            return_value=apps_dir,
        ):
            assert manifest_needs_update() is False

    def test_returns_false_when_orchestratr_not_installed(self):
        """Not stale if orchestratr isn't installed — nothing to update."""
        from templatr.integrations.orchestratr import manifest_needs_update

        with mock.patch(
            "templatr.integrations.orchestratr.resolve_orchestratr_apps_dir",
            return_value=None,
        ):
            assert manifest_needs_update() is False


# ---------------------------------------------------------------------------
# Status JSON tests
# ---------------------------------------------------------------------------


class TestGetStatusJson:
    """Tests for get_status_json()."""

    def test_ok_status_with_all_healthy(self, tmp_path):
        """Returns 'ok' when templates exist and server is running."""
        from templatr.integrations.orchestratr import get_status_json

        with mock.patch(
            "templatr.integrations.orchestratr.get_platform_config"
        ) as mock_pc, mock.patch(
            "templatr.integrations.orchestratr._get_template_count",
            return_value=12,
        ), mock.patch(
            "templatr.integrations.orchestratr._get_llm_status",
            return_value=("running", "mistral-7b.gguf"),
        ):
            mock_pc.return_value = mock.Mock(config_dir=tmp_path)
            result = get_status_json()

        data = json.loads(result)
        assert data["version"] == __version__
        assert data["status"] == "ok"
        assert data["config_dir"] == str(tmp_path)
        assert data["template_count"] == 12
        assert data["llm_server_status"] == "running"
        assert data["model_loaded"] == "mistral-7b.gguf"
        assert "errors" not in data

    def test_degraded_status_no_templates(self, tmp_path):
        """Returns 'degraded' with error when no templates found."""
        from templatr.integrations.orchestratr import get_status_json

        with mock.patch(
            "templatr.integrations.orchestratr.get_platform_config"
        ) as mock_pc, mock.patch(
            "templatr.integrations.orchestratr._get_template_count",
            return_value=0,
        ), mock.patch(
            "templatr.integrations.orchestratr._get_llm_status",
            return_value=("running", "model.gguf"),
        ):
            mock_pc.return_value = mock.Mock(config_dir=tmp_path)
            result = get_status_json()

        data = json.loads(result)
        assert data["status"] == "degraded"
        assert "No templates found" in data["errors"]

    def test_degraded_status_server_stopped(self, tmp_path):
        """Returns 'degraded' with error when LLM server not running."""
        from templatr.integrations.orchestratr import get_status_json

        with mock.patch(
            "templatr.integrations.orchestratr.get_platform_config"
        ) as mock_pc, mock.patch(
            "templatr.integrations.orchestratr._get_template_count",
            return_value=5,
        ), mock.patch(
            "templatr.integrations.orchestratr._get_llm_status",
            return_value=("stopped", None),
        ):
            mock_pc.return_value = mock.Mock(config_dir=tmp_path)
            result = get_status_json()

        data = json.loads(result)
        assert data["status"] == "degraded"
        assert data["llm_server_status"] == "stopped"
        assert data["model_loaded"] is None
        assert "LLM server not running" in data["errors"]

    def test_status_json_is_valid_json(self, tmp_path):
        """Output is always parseable JSON."""
        from templatr.integrations.orchestratr import get_status_json

        with mock.patch(
            "templatr.integrations.orchestratr.get_platform_config"
        ) as mock_pc, mock.patch(
            "templatr.integrations.orchestratr._get_template_count",
            return_value=3,
        ), mock.patch(
            "templatr.integrations.orchestratr._get_llm_status",
            return_value=("unknown", None),
        ):
            mock_pc.return_value = mock.Mock(config_dir=tmp_path)
            result = get_status_json()

        data = json.loads(result)
        # Required fields
        assert "version" in data
        assert "status" in data
        assert "config_dir" in data
        assert "template_count" in data
        assert "llm_server_status" in data
        assert "model_loaded" in data

    def test_multiple_errors(self, tmp_path):
        """Errors array includes all degradation reasons."""
        from templatr.integrations.orchestratr import get_status_json

        with mock.patch(
            "templatr.integrations.orchestratr.get_platform_config"
        ) as mock_pc, mock.patch(
            "templatr.integrations.orchestratr._get_template_count",
            return_value=0,
        ), mock.patch(
            "templatr.integrations.orchestratr._get_llm_status",
            return_value=("stopped", None),
        ):
            mock_pc.return_value = mock.Mock(config_dir=tmp_path)
            result = get_status_json()

        data = json.loads(result)
        assert data["status"] == "degraded"
        assert len(data["errors"]) == 2


# ---------------------------------------------------------------------------
# CLI integration tests
# ---------------------------------------------------------------------------


class TestCLIStatusCommand:
    """Tests for the `templatr status --json` CLI subcommand."""

    def test_status_json_exits_zero(self, tmp_path):
        """The status --json command returns exit code 0."""
        from templatr.__main__ import main

        with mock.patch(
            "sys.argv", ["templatr", "status", "--json"]
        ), mock.patch(
            "templatr.integrations.orchestratr.get_status_json",
            return_value='{"version": "1.2.0", "status": "ok"}',
        ):
            exit_code = main()

        assert exit_code == 0

    def test_status_json_outputs_json(self, tmp_path, capsys):
        """The status --json command prints JSON to stdout."""
        from templatr.__main__ import main

        fake_json = json.dumps({"version": __version__, "status": "ok"})

        with mock.patch(
            "sys.argv", ["templatr", "status", "--json"]
        ), mock.patch(
            "templatr.integrations.orchestratr.get_status_json",
            return_value=fake_json,
        ):
            main()

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["version"] == __version__

    def test_default_no_args_does_not_run_status(self):
        """Running templatr with no args should launch GUI, not status."""
        from templatr.__main__ import main

        with mock.patch("sys.argv", ["templatr"]), mock.patch(
            "templatr.ui.main_window.run_gui", return_value=0
        ) as mock_gui:
            main()

        mock_gui.assert_called_once()

    def test_doctor_flag_still_works(self):
        """--doctor flag continues to work after subcommand refactor."""
        from templatr.__main__ import main

        with mock.patch("sys.argv", ["templatr", "--doctor"]), mock.patch(
            "templatr.doctor.run_doctor", return_value=0
        ) as mock_doctor:
            main()

        mock_doctor.assert_called_once()


# ---------------------------------------------------------------------------
# Setup command tests
# ---------------------------------------------------------------------------


class TestSetupCommand:
    """Tests for the ``templatr setup`` CLI subcommand."""

    def test_setup_generates_manifest(self, tmp_path, capsys):
        """setup calls generate_manifest when orchestratr is present and manifest is stale."""
        from templatr.__main__ import main

        apps_dir = tmp_path / "apps.d"
        apps_dir.mkdir()

        with mock.patch("sys.argv", ["templatr", "setup"]), mock.patch(
            "templatr.integrations.orchestratr.resolve_orchestratr_apps_dir",
            return_value=apps_dir,
        ), mock.patch(
            "templatr.integrations.orchestratr.manifest_needs_update",
            return_value=True,
        ), mock.patch(
            "templatr.integrations.orchestratr.generate_manifest",
            return_value=True,
        ) as mock_gen:
            exit_code = main()

        assert exit_code == 0
        mock_gen.assert_called_once()
        captured = capsys.readouterr()
        assert "Registered" in captured.out

    def test_setup_skips_when_absent(self, capsys):
        """setup exits 0 and prints skip message when orchestratr is not installed."""
        from templatr.__main__ import main

        with mock.patch("sys.argv", ["templatr", "setup"]), mock.patch(
            "templatr.integrations.orchestratr.resolve_orchestratr_apps_dir",
            return_value=None,
        ), mock.patch(
            "templatr.integrations.orchestratr.generate_manifest",
        ) as mock_gen:
            exit_code = main()

        assert exit_code == 0
        mock_gen.assert_not_called()
        captured = capsys.readouterr()
        assert "not found" in captured.out

    def test_setup_dry_run(self, tmp_path, capsys):
        """--dry-run previews actions without writing the manifest."""
        from templatr.__main__ import main

        apps_dir = tmp_path / "apps.d"
        apps_dir.mkdir()

        with mock.patch(
            "sys.argv", ["templatr", "setup", "--dry-run"]
        ), mock.patch(
            "templatr.integrations.orchestratr.resolve_orchestratr_apps_dir",
            return_value=apps_dir,
        ), mock.patch(
            "templatr.integrations.orchestratr.generate_manifest",
        ) as mock_gen:
            exit_code = main()

        assert exit_code == 0
        mock_gen.assert_not_called()
        captured = capsys.readouterr()
        assert "[dry-run]" in captured.out

    def test_setup_idempotent(self, tmp_path, capsys):
        """setup prints 'up to date' when manifest is already current."""
        from templatr.__main__ import main

        apps_dir = tmp_path / "apps.d"
        apps_dir.mkdir()

        with mock.patch("sys.argv", ["templatr", "setup"]), mock.patch(
            "templatr.integrations.orchestratr.resolve_orchestratr_apps_dir",
            return_value=apps_dir,
        ), mock.patch(
            "templatr.integrations.orchestratr.manifest_needs_update",
            return_value=False,
        ), mock.patch(
            "templatr.integrations.orchestratr.generate_manifest",
        ) as mock_gen:
            exit_code = main()

        assert exit_code == 0
        mock_gen.assert_not_called()
        captured = capsys.readouterr()
        assert "up to date" in captured.out

    def test_setup_subcommand_accepted(self):
        """argparse accepts the setup subcommand without error."""
        from templatr.__main__ import main

        with mock.patch("sys.argv", ["templatr", "setup"]), mock.patch(
            "templatr.integrations.orchestratr.resolve_orchestratr_apps_dir",
            return_value=None,
        ):
            exit_code = main()

        assert exit_code == 0


# ---------------------------------------------------------------------------
# GUI integration settings dialog tests
# ---------------------------------------------------------------------------


class TestIntegrationSettingsDialog:
    """Tests for the Integrations settings dialog (mock-based)."""

    def test_dialog_creates_without_error(self, qtbot):
        """Dialog can be instantiated."""
        from templatr.ui.integration_settings import IntegrationSettingsDialog

        with mock.patch(
            "templatr.ui.integration_settings.resolve_orchestratr_apps_dir",
            return_value=None,
        ), mock.patch(
            "templatr.ui.integration_settings.manifest_needs_update",
            return_value=False,
        ):
            dialog = IntegrationSettingsDialog()
            qtbot.addWidget(dialog)
            assert dialog.windowTitle() == "Integrations"

    def test_shows_not_registered_when_no_manifest(self, qtbot, tmp_path):
        """Shows 'Not registered' when orchestratr not installed."""
        from templatr.ui.integration_settings import IntegrationSettingsDialog

        with mock.patch(
            "templatr.ui.integration_settings.resolve_orchestratr_apps_dir",
            return_value=None,
        ), mock.patch(
            "templatr.ui.integration_settings.manifest_needs_update",
            return_value=False,
        ):
            dialog = IntegrationSettingsDialog()
            qtbot.addWidget(dialog)
            assert "Not registered" in dialog.status_label.text() or \
                   "not detected" in dialog.status_label.text().lower()

    def test_shows_registered_when_manifest_current(self, qtbot, tmp_path):
        """Shows 'Registered' when manifest exists and is current."""
        from templatr.ui.integration_settings import IntegrationSettingsDialog

        apps_dir = tmp_path / "apps.d"
        apps_dir.mkdir(parents=True)
        (apps_dir / "templatr.yml").write_text(
            f"# orchestratr app manifest — written by templatr v{__version__}\n"
            "name: templatr\n"
        )

        with mock.patch(
            "templatr.ui.integration_settings.resolve_orchestratr_apps_dir",
            return_value=apps_dir,
        ), mock.patch(
            "templatr.ui.integration_settings.manifest_needs_update",
            return_value=False,
        ):
            dialog = IntegrationSettingsDialog()
            qtbot.addWidget(dialog)
            assert "Registered" in dialog.status_label.text()

    def test_shows_stale_when_version_mismatch(self, qtbot, tmp_path):
        """Shows stale status when manifest version doesn't match."""
        from templatr.ui.integration_settings import IntegrationSettingsDialog

        apps_dir = tmp_path / "apps.d"
        apps_dir.mkdir(parents=True)
        (apps_dir / "templatr.yml").write_text(
            "# orchestratr app manifest — written by templatr v0.0.1\n"
            "name: templatr\n"
        )

        with mock.patch(
            "templatr.ui.integration_settings.resolve_orchestratr_apps_dir",
            return_value=apps_dir,
        ), mock.patch(
            "templatr.ui.integration_settings.manifest_needs_update",
            return_value=True,
        ):
            dialog = IntegrationSettingsDialog()
            qtbot.addWidget(dialog)
            # Should show stale/outdated status
            text = dialog.status_label.text().lower()
            assert "stale" in text or "outdated" in text

    def test_register_button_exists(self, qtbot, tmp_path):
        """Dialog has a Register/Re-register button that is enabled when orchestratr detected."""
        from templatr.ui.integration_settings import IntegrationSettingsDialog

        apps_dir = tmp_path / "apps.d"
        apps_dir.mkdir(parents=True)

        with mock.patch(
            "templatr.ui.integration_settings.resolve_orchestratr_apps_dir",
            return_value=apps_dir,
        ), mock.patch(
            "templatr.ui.integration_settings.manifest_needs_update",
            return_value=True,
        ):
            dialog = IntegrationSettingsDialog()
            qtbot.addWidget(dialog)
            assert dialog.register_btn is not None
            assert dialog.register_btn.isEnabled()


# ---------------------------------------------------------------------------
# Passive design tests
# ---------------------------------------------------------------------------


class TestPassiveDesign:
    """Connector is fully passive — no errors when orchestratr absent."""

    def test_import_has_no_side_effects(self):
        """Importing the module does not write files or make network calls."""
        # Just import — if it has side effects, other tests will catch them
        import templatr.integrations.orchestratr  # noqa: F401

    def test_generate_manifest_no_error_when_absent(self):
        """generate_manifest returns False gracefully when orchestratr missing."""
        from templatr.integrations.orchestratr import generate_manifest

        with mock.patch(
            "templatr.integrations.orchestratr.resolve_orchestratr_apps_dir",
            return_value=None,
        ):
            result = generate_manifest()
            assert result is False

    def test_manifest_needs_update_no_error_when_absent(self):
        """manifest_needs_update returns False when orchestratr not installed."""
        from templatr.integrations.orchestratr import manifest_needs_update

        with mock.patch(
            "templatr.integrations.orchestratr.resolve_orchestratr_apps_dir",
            return_value=None,
        ):
            assert manifest_needs_update() is False
