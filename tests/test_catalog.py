"""Tests for the template catalog feature.

Covers:
- AC-2/3/9  CatalogFetchWorker: fetch success, field validation, network errors
- AC-7/9    CatalogInstallWorker: install success, conflict detection, errors
- AC-4/5/6  CatalogBrowserDialog: search filter, tag filter, detail pane
- AC-10     Config: catalog_url persists and defaults correctly
- AC-11     /help output includes /browse

Worker signal tests use QSignalSpy with a short event-loop spin.
Dialog tests use pytest-qt's qtbot fixture.
"""

import json
import tempfile
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from templatr.core.config import DEFAULT_CATALOG_URL, Config, ConfigManager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_entry(**overrides) -> dict:
    """Return a minimally valid catalog entry, with optional field overrides."""
    base = {
        "name": "Test Template",
        "description": "A test template.",
        "author": "tester",
        "tags": ["test"],
        "version": "1.0.0",
        "download_url": "https://example.com/test.json",
    }
    base.update(overrides)
    return base


def _fake_urlopen(content: bytes, status: int = 200):
    """Return a context-manager mock for urllib.request.urlopen."""
    resp = MagicMock()
    resp.status = status
    resp.read.return_value = content
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


def _spin(worker, timeout_ms: int = 3000) -> None:
    """Wait for a QThread worker to finish, pumping the event loop."""
    from PyQt6.QtCore import QCoreApplication
    import time

    deadline = time.monotonic() + timeout_ms / 1000
    worker.start()
    while worker.isRunning() and time.monotonic() < deadline:
        QCoreApplication.processEvents()
        time.sleep(0.01)


# ---------------------------------------------------------------------------
# AC-10 Config: catalog_url field
# ---------------------------------------------------------------------------


class TestCatalogUrlConfig:
    """catalog_url is present on Config with the correct default."""

    def test_default_catalog_url(self):
        """Config() carries the expected default catalog URL."""
        config = Config()
        assert config.catalog_url == DEFAULT_CATALOG_URL

    def test_catalog_url_persists_round_trip(self, tmp_path: Path):
        """catalog_url survives a save/load cycle."""
        custom_url = "https://my-org.example.com/catalog.json"
        mgr = ConfigManager(config_path=tmp_path / "config.json")
        mgr.config.catalog_url = custom_url
        mgr.save()

        mgr2 = ConfigManager(config_path=tmp_path / "config.json")
        assert mgr2.load().catalog_url == custom_url

    def test_from_dict_uses_default_when_key_absent(self):
        """Config.from_dict() fills catalog_url with the default when absent."""
        config = Config.from_dict({"llm": {}, "ui": {}})
        assert config.catalog_url == DEFAULT_CATALOG_URL

    def test_from_dict_reads_custom_url(self):
        """Config.from_dict() reads an explicit catalog_url from the dict."""
        custom_url = "https://internal.example.com/catalog.json"
        config = Config.from_dict({"catalog_url": custom_url})
        assert config.catalog_url == custom_url

    def test_update_catalog_url(self, tmp_path: Path):
        """ConfigManager.update() can change catalog_url."""
        custom_url = "https://private.example.com/catalog.json"
        mgr = ConfigManager(config_path=tmp_path / "config.json")
        mgr.update(catalog_url=custom_url)
        assert mgr.config.catalog_url == custom_url


# ---------------------------------------------------------------------------
# AC-11 /help includes /browse
# ---------------------------------------------------------------------------


class TestHelpIncludesBrowse:
    """/browse appears in the slash-command list."""

    def test_browse_in_system_commands(self):
        """/browse is registered as a system command."""
        from templatr.ui.slash_input import SYSTEM_COMMANDS

        names = [item.name for item in SYSTEM_COMMANDS]
        assert "/browse" in names

    def test_browse_payload(self):
        """/browse has payload cmd:browse."""
        from templatr.ui.slash_input import SYSTEM_COMMANDS

        browse = next(item for item in SYSTEM_COMMANDS if item.name == "/browse")
        assert browse.payload == "cmd:browse"


# ---------------------------------------------------------------------------
# AC-2/3  CatalogFetchWorker: success and field validation
# ---------------------------------------------------------------------------


class TestCatalogFetchWorkerSuccess:
    """CatalogFetchWorker emits catalog_ready with valid entries."""

    def test_emits_catalog_ready_on_success(self, qtbot):
        """Worker emits catalog_ready with the full entry list on HTTP 200."""
        from templatr.ui.workers import CatalogFetchWorker

        entries = [_make_entry(name="Alpha"), _make_entry(name="Beta")]
        body = json.dumps(entries).encode()

        with patch("urllib.request.urlopen", return_value=_fake_urlopen(body)):
            worker = CatalogFetchWorker("https://example.com/catalog.json")
            with qtbot.waitSignal(worker.catalog_ready, timeout=3000) as blocker:
                worker.start()
            worker.wait(2000)

        received = blocker.args[0]
        assert len(received) == 2
        assert received[0]["name"] == "Alpha"

    def test_skips_entries_missing_required_fields(self, qtbot):
        """Entries missing required fields are silently dropped."""
        from templatr.ui.workers import CatalogFetchWorker

        incomplete = {"name": "Missing Fields"}  # missing most required fields
        complete = _make_entry(name="Complete")
        body = json.dumps([incomplete, complete]).encode()

        with patch("urllib.request.urlopen", return_value=_fake_urlopen(body)):
            worker = CatalogFetchWorker("https://example.com/catalog.json")
            with qtbot.waitSignal(worker.catalog_ready, timeout=3000) as blocker:
                worker.start()
            worker.wait(2000)

        received = blocker.args[0]
        assert len(received) == 1
        assert received[0]["name"] == "Complete"

    def test_emits_empty_list_when_no_valid_entries(self, qtbot):
        """catalog_ready is emitted with [] when every entry is invalid."""
        from templatr.ui.workers import CatalogFetchWorker

        body = json.dumps([{"name": "bad"}]).encode()

        with patch("urllib.request.urlopen", return_value=_fake_urlopen(body)):
            worker = CatalogFetchWorker("https://example.com/catalog.json")
            with qtbot.waitSignal(worker.catalog_ready, timeout=3000) as blocker:
                worker.start()
            worker.wait(2000)

        assert blocker.args[0] == []


# ---------------------------------------------------------------------------
# AC-9  CatalogFetchWorker: error paths
# ---------------------------------------------------------------------------


class TestCatalogFetchWorkerErrors:
    """CatalogFetchWorker emits a non-empty error string on all failure modes."""

    def _assert_error_emitted(self, qtbot, side_effect=None, body=None, status=200):
        from templatr.ui.workers import CatalogFetchWorker

        if side_effect is not None:
            with patch("urllib.request.urlopen", side_effect=side_effect):
                worker = CatalogFetchWorker("https://example.com/catalog.json")
                with qtbot.waitSignal(worker.error, timeout=3000) as blocker:
                    worker.start()
                worker.wait(2000)
        else:
            resp = _fake_urlopen(body or b"", status=status)
            with patch("urllib.request.urlopen", return_value=resp):
                worker = CatalogFetchWorker("https://example.com/catalog.json")
                with qtbot.waitSignal(worker.error, timeout=3000) as blocker:
                    worker.start()
                worker.wait(2000)

        msg = blocker.args[0]
        assert msg, "error signal must carry a non-empty message"
        assert isinstance(msg, str)

    def test_url_error_emits_error(self, qtbot):
        """URLError (network) produces a human-readable error."""
        import urllib.error
        self._assert_error_emitted(
            qtbot, side_effect=urllib.error.URLError("name resolution failed")
        )

    def test_http_error_emits_error(self, qtbot):
        """HTTPError (e.g. 404) produces a human-readable error."""
        import urllib.error
        self._assert_error_emitted(
            qtbot, side_effect=urllib.error.HTTPError(
                url="http://x", code=404, msg="Not Found", hdrs={}, fp=None
            )
        )

    def test_non_200_status_emits_error(self, qtbot):
        """A non-200 HTTP status produces a human-readable error."""
        self._assert_error_emitted(qtbot, body=b"{}", status=503)

    def test_empty_body_emits_error(self, qtbot):
        """An empty response body produces a human-readable error."""
        self._assert_error_emitted(qtbot, body=b"")

    def test_invalid_json_emits_error(self, qtbot):
        """Malformed JSON in the response produces a human-readable error."""
        self._assert_error_emitted(qtbot, body=b"{not json}")

    def test_non_array_json_emits_error(self, qtbot):
        """A JSON object (instead of array) produces a human-readable error."""
        self._assert_error_emitted(qtbot, body=json.dumps({"key": "val"}).encode())


# ---------------------------------------------------------------------------
# AC-7  CatalogInstallWorker: install success
# ---------------------------------------------------------------------------


_VALID_TEMPLATE_JSON = json.dumps(
    {"name": "Catalog Template", "content": "Do {{task}}", "description": "desc"}
).encode()


class TestCatalogInstallWorkerSuccess:
    """CatalogInstallWorker downloads, validates, and saves the template."""

    def test_installs_template_and_emits_installed(self, qtbot):
        """Worker saves template and emits installed(template_name)."""
        from templatr.ui.workers import CatalogInstallWorker

        fake_template = MagicMock()
        fake_template.name = "Catalog Template"  # set as attr, not MagicMock kwarg

        mock_manager = MagicMock()
        mock_manager.import_template.return_value = (fake_template, False)
        mock_manager.save.return_value = True

        with patch(
            "urllib.request.urlopen",
            return_value=_fake_urlopen(_VALID_TEMPLATE_JSON),
        ):
            worker = CatalogInstallWorker("https://example.com/t.json", mock_manager)
            with qtbot.waitSignal(worker.installed, timeout=3000) as blocker:
                worker.start()
            worker.wait(2000)

        mock_manager.save.assert_called_once()
        assert blocker.args[0] == "Catalog Template"

    def test_emits_conflict_when_name_exists(self, qtbot):
        """Worker emits conflict(template) when import_template returns conflict=True."""
        from templatr.ui.workers import CatalogInstallWorker

        fake_template = MagicMock()
        mock_manager = MagicMock()
        mock_manager.import_template.return_value = (fake_template, True)

        with patch(
            "urllib.request.urlopen",
            return_value=_fake_urlopen(_VALID_TEMPLATE_JSON),
        ):
            worker = CatalogInstallWorker("https://example.com/t.json", mock_manager)
            with qtbot.waitSignal(worker.conflict, timeout=3000) as blocker:
                worker.start()
            worker.wait(2000)

        assert blocker.args[0] is fake_template
        mock_manager.save.assert_not_called()


# ---------------------------------------------------------------------------
# AC-9  CatalogInstallWorker: error paths
# ---------------------------------------------------------------------------


class TestCatalogInstallWorkerErrors:
    """CatalogInstallWorker emits a non-empty error string on all failure modes."""

    def test_network_error_emits_error(self, qtbot):
        """URLError during download emits a non-empty error."""
        import urllib.error
        from templatr.ui.workers import CatalogInstallWorker

        mock_manager = MagicMock()
        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("timeout"),
        ):
            worker = CatalogInstallWorker("https://example.com/t.json", mock_manager)
            with qtbot.waitSignal(worker.error, timeout=3000) as blocker:
                worker.start()
            worker.wait(2000)

        assert blocker.args[0]

    def test_invalid_template_json_emits_error(self, qtbot):
        """Validation error from import_template emits a non-empty error."""
        from templatr.ui.workers import CatalogInstallWorker

        mock_manager = MagicMock()
        mock_manager.import_template.side_effect = ValueError("missing 'content'")

        with patch(
            "urllib.request.urlopen",
            return_value=_fake_urlopen(_VALID_TEMPLATE_JSON),
        ):
            worker = CatalogInstallWorker("https://example.com/t.json", mock_manager)
            with qtbot.waitSignal(worker.error, timeout=3000) as blocker:
                worker.start()
            worker.wait(2000)

        assert blocker.args[0]


# ---------------------------------------------------------------------------
# AC-4/5/6  CatalogBrowserDialog: search, tag filter, detail pane
# ---------------------------------------------------------------------------


_CATALOG_ENTRIES = [
    _make_entry(name="Alpha Research", description="Research tool", author="alice", tags=["research", "productivity"]),
    _make_entry(name="Beta Code Review", description="Review PRs", author="bob", tags=["code", "review"]),
    _make_entry(name="Gamma Decision", description="Make decisions", author="alice", tags=["decision-making"]),
]


def _open_dialog_with_entries(qtbot, entries):
    """Open CatalogBrowserDialog pre-populated with entries (no real HTTP)."""
    from templatr.ui.catalog_browser import CatalogBrowserDialog

    catalog_json = json.dumps(entries).encode()
    mock_manager = MagicMock()

    with patch(
        "urllib.request.urlopen",
        return_value=_fake_urlopen(catalog_json),
    ):
        dialog = CatalogBrowserDialog(
            catalog_url="https://example.com/catalog.json",
            manager=mock_manager,
        )
        qtbot.addWidget(dialog)
        # Wait for the fetch worker to complete
        from PyQt6.QtCore import QCoreApplication
        import time
        deadline = time.monotonic() + 3.0
        while time.monotonic() < deadline:
            QCoreApplication.processEvents()
            time.sleep(0.02)
            if dialog._stack.currentIndex() != 0:  # past loading page
                break

    return dialog, mock_manager


class TestCatalogBrowserDialogFilter:
    """CatalogBrowserDialog filters the list correctly (AC-4, AC-5)."""

    def test_all_entries_shown_initially(self, qtbot):
        """All entries appear before any filter is applied."""
        dialog, _ = _open_dialog_with_entries(qtbot, _CATALOG_ENTRIES)
        assert dialog._list_widget.count() == len(_CATALOG_ENTRIES)

    def test_search_by_name_filters_list(self, qtbot):
        """Typing in the search box filters entries by name."""
        dialog, _ = _open_dialog_with_entries(qtbot, _CATALOG_ENTRIES)
        dialog._search_edit.setText("alpha")
        assert dialog._list_widget.count() == 1
        assert dialog._list_widget.item(0).text() == "Alpha Research"

    def test_search_by_author_filters_list(self, qtbot):
        """Search by author name works correctly."""
        dialog, _ = _open_dialog_with_entries(qtbot, _CATALOG_ENTRIES)
        dialog._search_edit.setText("alice")
        # Alice authored Alpha Research and Gamma Decision
        assert dialog._list_widget.count() == 2

    def test_search_is_case_insensitive(self, qtbot):
        """Search is case-insensitive."""
        dialog, _ = _open_dialog_with_entries(qtbot, _CATALOG_ENTRIES)
        dialog._search_edit.setText("BETA")
        assert dialog._list_widget.count() == 1

    def test_tag_filter_narrows_entries(self, qtbot):
        """Selecting a specific tag only shows matching entries."""
        from PyQt6.QtCore import QCoreApplication

        dialog, _ = _open_dialog_with_entries(qtbot, _CATALOG_ENTRIES)

        # Find the "code" tag in the combo
        idx = dialog._tag_combo.findText("code")
        assert idx >= 0, "Tag 'code' should be in the combo"
        dialog._tag_combo.setCurrentIndex(idx)
        QCoreApplication.processEvents()

        assert dialog._list_widget.count() == 1
        assert dialog._list_widget.item(0).text() == "Beta Code Review"

    def test_clearing_search_restores_all_entries(self, qtbot):
        """Clearing the search field shows all entries again."""
        dialog, _ = _open_dialog_with_entries(qtbot, _CATALOG_ENTRIES)
        dialog._search_edit.setText("alpha")
        dialog._search_edit.clear()
        assert dialog._list_widget.count() == len(_CATALOG_ENTRIES)


class TestCatalogBrowserDialogDetailPane:
    """CatalogBrowserDialog populates the detail pane on selection (AC-6)."""

    def test_selecting_entry_populates_detail_pane(self, qtbot):
        """Clicking an entry fills name, description, author, version, tags."""
        from PyQt6.QtCore import QCoreApplication

        dialog, _ = _open_dialog_with_entries(qtbot, _CATALOG_ENTRIES)
        dialog._list_widget.setCurrentRow(0)
        QCoreApplication.processEvents()

        entry = _CATALOG_ENTRIES[0]
        assert entry["name"] in dialog._detail_name.text()
        assert entry["author"] in dialog._detail_author.text()
        assert entry["version"] in dialog._detail_version.text()
        assert entry["description"] in dialog._detail_desc.text()

    def test_install_button_enabled_after_selection(self, qtbot):
        """Install button becomes enabled when an entry is selected."""
        from PyQt6.QtCore import QCoreApplication

        dialog, _ = _open_dialog_with_entries(qtbot, _CATALOG_ENTRIES)
        assert not dialog._install_btn.isEnabled()
        dialog._list_widget.setCurrentRow(1)
        QCoreApplication.processEvents()
        assert dialog._install_btn.isEnabled()
