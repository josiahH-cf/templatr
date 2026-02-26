"""Variable form widget for editing template variables."""

from typing import Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QKeySequence
from PyQt6.QtWidgets import (
    QFormLayout,
    QFrame,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from automatr.core.config import get_config
from automatr.core.templates import Template


class _VariableScrollArea(QScrollArea):
    """Internal scroll area that holds the dynamic form fields."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.container = QWidget()
        self.form_layout = QFormLayout(self.container)
        self.form_layout.setContentsMargins(0, 0, 10, 0)
        self.form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        self.form_layout.setVerticalSpacing(12)
        self.setWidget(self.container)
        self.inputs: dict[str, QWidget] = {}


class VariableFormWidget(QWidget):
    """Widget for displaying template variables with generate/render buttons.

    Provides a dynamic form generated from Template.variables, along with
    action buttons that emit signals for generating or copying output.
    """

    generate_requested = pyqtSignal()
    render_template_requested = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the variable form widget."""
        super().__init__(parent)
        self._template: Optional[Template] = None
        self._setup_ui()

    def _setup_ui(self):
        """Build the form layout with label, scroll area, and buttons."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 10, 5, 10)

        config = get_config()
        label_size = config.ui.font_size + 1
        self._label = QLabel("Variables")
        self._label.setStyleSheet(
            f"font-weight: bold; font-size: {label_size}pt;"
        )
        layout.addWidget(self._label)

        self._scroll = _VariableScrollArea()
        layout.addWidget(self._scroll)

        self.generate_btn = QPushButton("Render with AI (Ctrl+G)")
        self.generate_btn.setEnabled(False)
        self.generate_btn.setShortcut(QKeySequence("Ctrl+G"))
        self.generate_btn.clicked.connect(self.generate_requested.emit)
        layout.addWidget(self.generate_btn)

        self.render_template_btn = QPushButton("Copy Template (Ctrl+Shift+G)")
        self.render_template_btn.setEnabled(False)
        self.render_template_btn.setShortcut(QKeySequence("Ctrl+Shift+G"))
        self.render_template_btn.clicked.connect(
            self.render_template_requested.emit
        )
        layout.addWidget(self.render_template_btn)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_template(self, template: Template):
        """Set the template and create input fields for its variables."""
        self._template = template
        self._scroll.inputs.clear()
        form = self._scroll.form_layout

        while form.count():
            item = form.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not template.variables:
            label = QLabel("No variables in this template.")
            label.setStyleSheet("color: #808080; font-style: italic;")
            label.setWordWrap(True)
            form.addRow(label)
            return

        for var in template.variables:
            label = QLabel(f"{var.label}:")
            label.setWordWrap(True)
            default_value = (
                var.default
                if isinstance(var.default, str)
                else str(var.default) if var.default is not None else ""
            )
            if var.multiline:
                widget = QPlainTextEdit()
                widget.setPlaceholderText(
                    default_value or f"Enter {var.label.lower()}..."
                )
                widget.setMaximumHeight(100)
                if default_value:
                    widget.setPlainText(default_value)
            else:
                widget = QLineEdit()
                widget.setPlaceholderText(
                    default_value or f"Enter {var.label.lower()}..."
                )
                if default_value:
                    widget.setText(default_value)
            self._scroll.inputs[var.name] = widget
            form.addRow(label, widget)

    def get_values(self) -> dict[str, str]:
        """Get the current values from all input fields."""
        values = {}
        for name, widget in self._scroll.inputs.items():
            if isinstance(widget, QPlainTextEdit):
                values[name] = widget.toPlainText()
            else:
                values[name] = widget.text()
        return values

    def clear(self):
        """Clear all input fields."""
        for widget in self._scroll.inputs.values():
            if isinstance(widget, QPlainTextEdit):
                widget.clear()
            else:
                widget.clear()

    def set_buttons_enabled(self, enabled: bool):
        """Enable or disable the generate and render buttons."""
        self.generate_btn.setEnabled(enabled)
        self.render_template_btn.setEnabled(enabled)
