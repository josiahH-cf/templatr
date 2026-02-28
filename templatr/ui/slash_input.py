"""Slash input bar with template command palette and inline variable form.

Provides SlashInputWidget, a compound input area that:
- Intercepts '/' to show a filterable template palette
- Shows a compact inline variable form when a template with variables is selected
- Emits rendered prompts for LLM generation or plain text for pass-through
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from templatr.core.templates import Template


class _TemplatePalette(QFrame):
    """Filterable template list anchored above the input bar.

    Positioned as a child of SlashInputWidget, not a floating dialog,
    to avoid z-order issues. Keyboard navigation: Up/Down to move,
    Enter to confirm, Escape to dismiss.

    Attributes:
        template_chosen: Signal emitted with the selected Template.
        dismissed: Signal emitted when the palette is closed without selection.
    """

    template_chosen = pyqtSignal(object)  # emits Template
    dismissed = pyqtSignal()

    def __init__(self, parent: QWidget) -> None:
        """Initialize the palette as a hidden child of parent."""
        super().__init__(parent)
        self.setObjectName("template_palette")
        self._templates: list[Template] = []
        self._setup_ui()
        self.hide()

    def populate(self, templates: list[Template]) -> None:
        """Set the full template list (called once at startup).

        Args:
            templates: All known templates.
        """
        self._templates = templates
        self._list.clear()
        for t in templates:
            item = QListWidgetItem(t.name)
            item.setData(Qt.ItemDataRole.UserRole, t)
            self._list.addItem(item)

    def filter(self, query: str) -> None:
        """Filter displayed templates to those matching query (case-insensitive).

        Args:
            query: Substring to match against template names.
        """
        query_lower = query.lower()
        for i in range(self._list.count()):
            item = self._list.item(i)
            item.setHidden(query_lower not in item.text().lower())

        # Auto-select first visible item.
        for i in range(self._list.count()):
            item = self._list.item(i)
            if not item.isHidden():
                self._list.setCurrentItem(item)
                break

    def keyPressEvent(self, event) -> None:  # noqa: N802
        """Forward arrow/enter/escape keys for palette navigation.

        Args:
            event: QKeyEvent from the parent input field.
        """
        key = event.key()
        if key == Qt.Key.Key_Escape:
            self.dismissed.emit()
        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._confirm_selection()
        elif key == Qt.Key.Key_Up:
            current = self._list.currentRow()
            if current > 0:
                self._list.setCurrentRow(current - 1)
        elif key == Qt.Key.Key_Down:
            current = self._list.currentRow()
            if current < self._list.count() - 1:
                self._list.setCurrentRow(current + 1)
        else:
            super().keyPressEvent(event)

    def _confirm_selection(self) -> None:
        """Emit template_chosen for the currently highlighted item."""
        item = self._list.currentItem()
        if item and not item.isHidden():
            template = item.data(Qt.ItemDataRole.UserRole)
            self.template_chosen.emit(template)

    def _on_item_activated(self, item: QListWidgetItem) -> None:
        """Handle double-click or Enter on a list item.

        Args:
            item: The activated QListWidgetItem.
        """
        template = item.data(Qt.ItemDataRole.UserRole)
        if template:
            self.template_chosen.emit(template)

    def _setup_ui(self) -> None:
        """Build the palette layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(0)

        self._list = QListWidget()
        self._list.itemActivated.connect(self._on_item_activated)
        layout.addWidget(self._list)


class _InlineVariableForm(QFrame):
    """Compact variable form shown between the chat thread and the input bar.

    Appears when a template with variables is selected via '/' command.
    Hidden by default; shown by set_template(). Purpose-built — does not
    reuse VariableFormWidget (which is a full sidebar-size component).

    Attributes:
        submitted: Signal emitting {var_name: value} dict on submission.
        cancelled: Signal emitted when user cancels the form.
    """

    submitted = pyqtSignal(dict)
    cancelled = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the form as hidden with no fields."""
        super().__init__(parent)
        self.setObjectName("inline_var_form")
        self._fields: dict[str, QLineEdit] = {}
        self._setup_ui()
        self.hide()

    def set_template(self, template: Template) -> None:
        """Build form fields for the template's variables and show the form.

        Args:
            template: Template whose variables define the form fields.
        """
        self._clear_fields()
        for var in template.variables:
            label = QLabel(var.label or var.name)
            field = QLineEdit()
            field.setPlaceholderText(var.default or f"Enter {var.label or var.name}")
            if var.default:
                field.setText(var.default)
            self._fields[var.name] = field
            self._form_layout.addRow(label, field)

        if self._fields:
            # Focus the first field
            list(self._fields.values())[0].setFocus()

        self.show()

    def clear(self) -> None:
        """Remove all form fields and hide the form."""
        self._clear_fields()
        self.hide()

    def get_values(self) -> dict:
        """Return {var_name: current_value} for all fields.

        Returns:
            Dictionary mapping variable names to their current input values.
        """
        return {name: field.text() for name, field in self._fields.items()}

    def _on_submit(self) -> None:
        """Emit submitted(values) with current field values."""
        self.submitted.emit(self.get_values())

    def _on_cancel(self) -> None:
        """Emit cancelled and clear the form."""
        self.cancelled.emit()

    def _clear_fields(self) -> None:
        """Remove all field widgets from the form layout."""
        self._fields.clear()
        while self._form_layout.rowCount() > 0:
            self._form_layout.removeRow(0)

    def _setup_ui(self) -> None:
        """Build the form layout with submit/cancel buttons."""
        from PyQt6.QtWidgets import QFormLayout

        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 6, 8, 6)
        outer.setSpacing(6)

        self._form_layout = QFormLayout()
        self._form_layout.setContentsMargins(0, 0, 0, 0)
        outer.addLayout(self._form_layout)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondary")
        cancel_btn.clicked.connect(self._on_cancel)
        btn_row.addWidget(cancel_btn)

        submit_btn = QPushButton("Send")
        submit_btn.clicked.connect(self._on_submit)
        btn_row.addWidget(submit_btn)

        outer.addLayout(btn_row)


class SlashInputWidget(QWidget):
    """Input bar with slash-command template selection and inline variable form.

    Layout (top to bottom within this widget):
        _inline_form    (hidden by default, visible when template has variables)
        _text_input     (QPlainTextEdit, single-line feel)
        [_status_label  + _send_btn] horizontal row

    Signal chain:
        User types '/' → _palette shown
        User selects template → _on_template_chosen()
            → If no variables: render and emit template_submitted
            → If variables: show _inline_form
        User fills form → _on_form_submitted() → emit template_submitted
        User types plain text + clicks Send → emit plain_submitted

    Attributes:
        template_submitted: Signal emitting a rendered prompt string.
        plain_submitted: Signal emitting a plain text string.
    """

    template_submitted = pyqtSignal(str)
    plain_submitted = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the input bar with empty palette and hidden form."""
        super().__init__(parent)
        self._active_template: Template | None = None
        self._setup_ui()

    # -- Public API ----------------------------------------------------------

    def set_templates(self, templates: list[Template]) -> None:
        """Populate the palette with all known templates.

        Args:
            templates: All templates available for '/' selection.
        """
        self._palette.populate(templates)

    def set_llm_ready(self, ready: bool) -> None:
        """Enable or disable the Send button based on LLM server status.

        Args:
            ready: True when the LLM server is running and ready.
        """
        self._send_btn.setEnabled(ready)
        if not ready:
            self._send_btn.setToolTip("Start the LLM server to send messages")
        else:
            self._send_btn.setToolTip("")

    def set_waiting_message(self, attempt: int, max_attempts: int) -> None:
        """Update the status label while the worker waits for the server.

        Args:
            attempt: Current retry attempt number (1-based).
            max_attempts: Total number of retry attempts planned.
        """
        self._status_label.setText(
            f"Waiting for server… (attempt {attempt}/{max_attempts})"
        )

    def set_generating(self, generating: bool) -> None:
        """Disable or re-enable the input and Send button during generation.

        Args:
            generating: True to disable input (generation in progress).
        """
        self._text_input.setEnabled(not generating)
        self._send_btn.setEnabled(not generating)
        if generating:
            self._status_label.setText("Generating…")
        else:
            self._status_label.setText("")

    # -- Internal slots ------------------------------------------------------

    def _on_text_changed(self) -> None:
        """Intercept text changes to show/update the palette on '/' prefix."""
        text = self._text_input.toPlainText()
        if text.startswith("/"):
            query = text[1:]  # strip leading slash
            if not self._palette.isVisible():
                self._show_palette()
            self._palette.filter(query)
        else:
            if self._palette.isVisible():
                self._dismiss_palette()

    def _on_template_chosen(self, template: Template) -> None:
        """Handle template selection from the palette.

        If the template has no variables, render and submit immediately.
        If it has variables, show the inline form for filling.

        Args:
            template: The chosen Template.
        """
        self._active_template = template
        self._dismiss_palette()

        if not template.variables:
            rendered = template.render({})
            self._text_input.clear()
            self.template_submitted.emit(rendered)
            self._active_template = None
        else:
            self._text_input.setEnabled(False)
            self._inline_form.set_template(template)

    def _on_form_submitted(self, values: dict) -> None:
        """Render the active template with form values and emit template_submitted.

        Args:
            values: {var_name: value} from the inline variable form.
        """
        if self._active_template is not None:
            rendered = self._active_template.render(values)
            self._active_template = None
            self._inline_form.clear()
            self._text_input.setEnabled(True)
            self._text_input.clear()
            self.template_submitted.emit(rendered)

    def _on_form_cancelled(self) -> None:
        """Dismiss the inline form and restore the input."""
        self._active_template = None
        self._inline_form.clear()
        self._text_input.setEnabled(True)
        self._text_input.clear()

    def _on_send_clicked(self) -> None:
        """Emit plain_submitted with the current input text (no template active)."""
        text = self._text_input.toPlainText().strip()
        if text:
            self._text_input.clear()
            self.plain_submitted.emit(text)

    def _show_palette(self) -> None:
        """Position and show the template palette above the input field."""
        self._palette.raise_()
        # Size: up to 5 rows visible, fixed width matches parent
        row_height = 26
        visible_rows = min(5, self._palette._list.count() or 1)
        palette_height = visible_rows * row_height + 10
        self._palette.setGeometry(
            0,
            self.height() - palette_height - self._text_input.height() - 36,
            self.width(),
            palette_height,
        )
        self._palette.show()

    def _dismiss_palette(self) -> None:
        """Hide the palette and clear the slash-command state."""
        self._palette.hide()

    def _key_event_filter(self, obj, event) -> bool:
        """Forward Up/Down/Enter to the palette when it is visible.

        Args:
            obj: The object receiving the event.
            event: The QKeyEvent.

        Returns:
            True if the event was consumed by the palette.
        """
        from PyQt6.QtCore import QEvent

        if event.type() == QEvent.Type.KeyPress and self._palette.isVisible():
            key = event.key()
            if key in (
                Qt.Key.Key_Up,
                Qt.Key.Key_Down,
                Qt.Key.Key_Return,
                Qt.Key.Key_Enter,
                Qt.Key.Key_Escape,
            ):
                self._palette.keyPressEvent(event)
                return True
        return False

    def resizeEvent(self, event) -> None:  # noqa: N802
        """Reposition the palette when the widget resizes.

        Args:
            event: QResizeEvent.
        """
        super().resizeEvent(event)
        if self._palette.isVisible():
            self._show_palette()

    # -- Internal setup ------------------------------------------------------

    def _setup_ui(self) -> None:
        """Build the input bar layout."""
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Inline variable form (hidden initially)
        self._inline_form = _InlineVariableForm()
        self._inline_form.submitted.connect(self._on_form_submitted)
        self._inline_form.cancelled.connect(self._on_form_cancelled)
        outer.addWidget(self._inline_form)

        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setObjectName("slash_input_bar")
        outer.addWidget(separator)

        # Text input area
        self._text_input = QPlainTextEdit()
        self._text_input.setPlaceholderText(
            "Type a message or / to select a template…"
        )
        self._text_input.setMaximumHeight(80)
        self._text_input.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum
        )
        self._text_input.textChanged.connect(self._on_text_changed)
        self._text_input.installEventFilter(self)
        outer.addWidget(self._text_input)

        # Bottom row: status label + Send button
        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(8, 4, 8, 8)

        self._status_label = QLabel()
        self._status_label.setObjectName("status_label")
        self._status_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        bottom_row.addWidget(self._status_label)

        self._send_btn = QPushButton("Send")
        self._send_btn.setEnabled(False)
        self._send_btn.clicked.connect(self._on_send_clicked)
        bottom_row.addWidget(self._send_btn)
        outer.addLayout(bottom_row)

        # Template palette (child widget, positioned absolutely)
        self._palette = _TemplatePalette(self)
        self._palette.template_chosen.connect(self._on_template_chosen)
        self._palette.dismissed.connect(self._on_palette_dismissed)

    def _on_palette_dismissed(self) -> None:
        """Clear input and hide palette when dismissed via Escape."""
        self._text_input.clear()
        self._dismiss_palette()

    def eventFilter(self, obj, event) -> bool:  # noqa: N802
        """Event filter installed on _text_input for palette keyboard nav.

        Args:
            obj: The watched object.
            event: The event.

        Returns:
            True if the event was consumed.
        """
        return self._key_event_filter(obj, event)
