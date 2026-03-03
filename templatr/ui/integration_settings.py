"""Integrations settings dialog for Templatr.

Shows orchestratr registration status with Register/Re-register controls.
"""

import logging

from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from templatr import __version__
from templatr.integrations.orchestratr import (
    generate_manifest,
    manifest_needs_update,
    resolve_orchestratr_apps_dir,
)

logger = logging.getLogger(__name__)


class IntegrationSettingsDialog(QDialog):
    """Dialog for viewing and managing external integrations."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Integrations")
        self.setMinimumWidth(480)
        self._setup_ui()
        self._refresh_status()

    def _setup_ui(self):
        """Build the dialog layout."""
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("Integrations")
        header.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(header)
        layout.addSpacing(10)

        # orchestratr group
        orch_group = QGroupBox("orchestratr")
        orch_layout = QVBoxLayout(orch_group)

        # Status row
        status_row = QHBoxLayout()
        status_label_prefix = QLabel("Status:")
        status_label_prefix.setStyleSheet("font-weight: bold;")
        self.status_label = QLabel("")
        status_row.addWidget(status_label_prefix)
        status_row.addWidget(self.status_label)
        status_row.addStretch()
        orch_layout.addLayout(status_row)

        # Manifest path
        self.manifest_path_label = QLabel("")
        self.manifest_path_label.setWordWrap(True)
        self.manifest_path_label.setStyleSheet("color: #888; font-size: 11px;")
        orch_layout.addWidget(self.manifest_path_label)

        # Chord info
        self.chord_label = QLabel("Chord: t")
        self.chord_label.setStyleSheet("color: #888; font-size: 11px;")
        orch_layout.addWidget(self.chord_label)

        orch_layout.addSpacing(10)

        # Register button
        self.register_btn = QPushButton("Register")
        self.register_btn.setFixedWidth(160)
        self.register_btn.clicked.connect(self._on_register)
        orch_layout.addWidget(self.register_btn)

        # Description
        desc_label = QLabel(
            "orchestratr discovers, launches, and focuses templatr\n"
            "via a hotkey chord. Registration writes a small manifest file\n"
            "that orchestratr reads on startup."
        )
        desc_label.setStyleSheet("color: #888; font-size: 11px;")
        desc_label.setWordWrap(True)
        orch_layout.addWidget(desc_label)

        layout.addWidget(orch_group)
        layout.addStretch()

        # Close button
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _refresh_status(self):
        """Update the status display based on current state."""
        apps_dir = resolve_orchestratr_apps_dir()

        if apps_dir is None:
            # orchestratr not installed
            self.status_label.setText("\u25cb Not registered")
            self.status_label.setStyleSheet("color: #888;")
            self.manifest_path_label.setText("orchestratr not detected.")
            self.register_btn.setText("Register")
            self.register_btn.setEnabled(False)
            self.register_btn.setToolTip(
                "Install orchestratr to enable hotkey integration."
            )
            return

        manifest_path = apps_dir / "templatr.yml"

        if not manifest_path.exists():
            # orchestratr installed but not registered
            self.status_label.setText("\u25cb Not registered")
            self.status_label.setStyleSheet("color: #cc8800;")
            self.manifest_path_label.setText(f"Manifest: {manifest_path}")
            self.register_btn.setText("Register")
            self.register_btn.setEnabled(True)
            self.register_btn.setToolTip("")
        elif manifest_needs_update():
            # Registered but stale
            self.status_label.setText("\u25cb Stale (outdated version)")
            self.status_label.setStyleSheet("color: #cc8800;")
            self.manifest_path_label.setText(f"Manifest: {manifest_path}")
            self.register_btn.setText("Re-register")
            self.register_btn.setEnabled(True)
            self.register_btn.setToolTip("")
        else:
            # Registered and current
            self.status_label.setText(f"\u25cf Registered (v{__version__})")
            self.status_label.setStyleSheet("color: #00aa00;")
            self.manifest_path_label.setText(f"Manifest: {manifest_path}")
            self.register_btn.setText("Re-register")
            self.register_btn.setEnabled(True)
            self.register_btn.setToolTip("")

    def _on_register(self):
        """Handle Register/Re-register button click."""
        success = generate_manifest()
        if success:
            logger.info("orchestratr manifest registered successfully")
        else:
            logger.warning("orchestratr manifest registration failed")
        self._refresh_status()
