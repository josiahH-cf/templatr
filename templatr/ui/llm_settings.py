"""LLM Settings dialog for Automatr.

Simplified GUI for max token length setting.
Advanced settings available in llama.cpp web UI.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from templatr.core.config import get_config_manager

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

        # Form with max tokens setting
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
        config = get_config_manager().config.llm
        self.max_tokens_spin.setValue(config.max_tokens)

    def _reset_to_defaults(self):
        """Reset to default value."""
        self.max_tokens_spin.setValue(DEFAULT_MAX_TOKENS)

    def _save_settings(self):
        """Save settings to config and close."""
        config_manager = get_config_manager()
        config_manager.update(**{"llm.max_tokens": self.max_tokens_spin.value()})
        self.accept()
