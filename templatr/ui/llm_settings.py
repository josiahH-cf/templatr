"""LLM Settings dialog for Templatr.

Simplified GUI for max token length setting.
Advanced settings available in llama.cpp web UI.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from templatr.core.config import DEFAULT_CATALOG_URL, get_config_manager

# Default value (must match LLMConfig dataclass default)
DEFAULT_MAX_TOKENS = 4096


class LLMSettingsDialog(QDialog):
    """Dialog for editing LLM generation settings."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("LLM Settings")
        self.setMinimumWidth(400)
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("Generation Settings")
        header.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(header)

        layout.addSpacing(10)

        # Form with max tokens and catalog URL settings
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Max tokens (1 - 8192)
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(1, 8192)
        self.max_tokens_spin.setSingleStep(256)
        self.max_tokens_spin.setToolTip(
            "Maximum tokens to generate per response.\n"
            "Cannot exceed the server's context size (default 4096)."
        )
        form.addRow("Max Token Length:", self.max_tokens_spin)

        # Catalog URL
        self.catalog_url_edit = QLineEdit()
        self.catalog_url_edit.setPlaceholderText(DEFAULT_CATALOG_URL)
        self.catalog_url_edit.setToolTip(
            "URL of the catalog index JSON file.\n"
            "Change this to point to a private or forked catalog.\n"
            "Leave blank to restore the default community catalog."
        )
        form.addRow("Catalog URL:", self.catalog_url_edit)

        layout.addLayout(form)
        layout.addSpacing(15)

        # Reset button
        reset_btn = QPushButton("Reset to Default")
        reset_btn.clicked.connect(self._reset_to_defaults)
        layout.addWidget(reset_btn)

        layout.addSpacing(20)

        # Help text for advanced settings
        advanced_label = QLabel("Advanced Settings")
        advanced_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(advanced_label)

        help_text = QLabel(
            "For temperature, top-p, top-k, and other generation parameters:\n\n"
            "1. Open http://localhost:8080 in your browser\n"
            "2. Adjust settings in the llama.cpp web interface\n"
            "3. Settings apply per-session while the server runs\n\n"
            "Context size requires a server restart (LLM → Stop, then Start)."
        )
        help_text.setStyleSheet("color: #888; font-size: 11px;")
        help_text.setWordWrap(True)
        layout.addWidget(help_text)

        layout.addStretch()

        # Dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save_settings)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_settings(self):
        """Load current settings from config."""
        config = get_config_manager().config
        self.max_tokens_spin.setValue(config.llm.max_tokens)
        self.catalog_url_edit.setText(config.catalog_url)

    def _reset_to_defaults(self):
        """Reset to default values."""
        self.max_tokens_spin.setValue(DEFAULT_MAX_TOKENS)
        self.catalog_url_edit.setText(DEFAULT_CATALOG_URL)

    def _save_settings(self):
        """Save settings to config and close."""
        config_manager = get_config_manager()
        url = self.catalog_url_edit.text().strip() or DEFAULT_CATALOG_URL
        config_manager.update(
            **{
                "llm.max_tokens": self.max_tokens_spin.value(),
                "catalog_url": url,
            }
        )
        self.accept()
