"""Slash input bar with command palette and inline variable form.

Provides SlashInputWidget, a compound input area that:
- Intercepts '/' to show a filterable command palette with templates and system commands
- Intercepts ':' to match template trigger shortcuts
- Shows a compact inline variable form when a template with variables is selected
- Emits rendered prompts for LLM generation or plain text for pass-through
- Tracks recently-used templates for quick re-access
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from templatr.ui.command_palette import CommandPalette, PaletteItem

if TYPE_CHECKING:
    from templatr.core.templates import Template

# System commands available via /command syntax
SYSTEM_COMMANDS: list[PaletteItem] = [
    PaletteItem(
        name="/help", description="Show available commands", payload="cmd:help"
    ),
    PaletteItem(
        name="/history", description="Show recent prompt history", payload="cmd:history"
    ),
    PaletteItem(
        name="/favorites",
        description="Show favorite outputs",
        payload="cmd:favorites",
    ),
    PaletteItem(
        name="/favorite",
        description="Favorite the last output",
        payload="cmd:favorite",
    ),
    PaletteItem(
        name="/compare",
        description="Compare one prompt across multiple models",
        payload="cmd:compare",
    ),
    PaletteItem(name="/new", description="Create a new template", payload="cmd:new"),
    PaletteItem(name="/import", description="Import a template", payload="cmd:import"),
    PaletteItem(name="/export", description="Export a template", payload="cmd:export"),
    PaletteItem(
        name="/settings", description="Open LLM settings", payload="cmd:settings"
    ),
    PaletteItem(
        name="/browse",
        description="Browse and install community templates",
        payload="cmd:browse",
    ),
]


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

    def eventFilter(self, obj, event) -> bool:  # noqa: N802
        """Handle Escape (cancel) and Enter (submit) in form fields.

        Args:
            obj: The watched field widget.
            event: The event.

        Returns:
            True if the event was consumed.
        """
        from PyQt6.QtCore import QEvent

        if event.type() == QEvent.Type.KeyPress:
            key = event.key()
            if key == Qt.Key.Key_Escape:
                self._on_cancel()
                return True
            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                if not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                    self._on_submit()
                    return True
        return super().eventFilter(obj, event)

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
            field.installEventFilter(self)
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
        template_chosen: Signal emitting the template name when a template is picked.
    """

    template_submitted = pyqtSignal(str)
    plain_submitted = pyqtSignal(str)
    system_command = pyqtSignal(str)  # emits command id (e.g. "help", "settings")
    template_chosen = pyqtSignal(str)  # emits template name when a template is selected

    MAX_RECENT = 5

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the input bar with empty palette and hidden form."""
        super().__init__(parent)
        self._active_template: Template | None = None
        self._llm_ready = False
        self._templates: list[Template] = []
        self._recent_templates: list[str] = []
        self._setup_ui()

    # -- Public API ----------------------------------------------------------

    def set_templates(self, templates: list[Template]) -> None:
        """Store templates for palette population on demand.

        Args:
            templates: All templates available for '/' selection.
        """
        self._templates = list(templates)

    def set_llm_ready(self, ready: bool) -> None:
        """Enable or disable the Send button based on LLM server status.

        Args:
            ready: True when the LLM server is running and ready.
        """
        self._llm_ready = ready
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
        self._send_btn.setEnabled(not generating and self._llm_ready)
        if generating:
            self._status_label.setText("Generating…")
        else:
            self._status_label.setText("")

    def is_palette_visible(self) -> bool:
        """Return True if the command palette is currently visible.

        Used by MainWindow to guard keyboard shortcuts that must not fire
        while the user is navigating the template palette.

        Returns:
            True if the palette is open.
        """
        return self._palette.isVisible()

    # -- Internal slots ------------------------------------------------------

    def _on_text_changed(self) -> None:
        """Intercept text changes to show/update the palette on '/' or ':' prefix."""
        text = self._text_input.toPlainText()
        if text.startswith("/"):
            query = text[1:]  # strip leading slash
            if not self._palette.isVisible():
                self._show_palette()
            items = self._build_palette_items(query, include_system=True)
            self._palette.set_recent(self._recent_templates)
            self._palette.populate(items)
            self._palette.filter(query)
        elif text.startswith(":"):
            query = text[1:]  # strip leading colon
            if not self._palette.isVisible():
                self._show_palette()
            items = self._build_trigger_items(query)
            self._palette.populate(items)
            # Don't call filter() here — _build_trigger_items already
            # pre-filtered by trigger match. Calling filter() would
            # re-filter by name, incorrectly hiding templates whose
            # trigger doesn't match their name.
            if self._palette._list.count() > 0:
                self._palette._list.setCurrentRow(0)
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
        self._track_recent(template.name)
        self._dismiss_palette()
        self.template_chosen.emit(template.name)

        if not template.variables:
            rendered = template.render({})
            self._text_input.clear()
            self.template_submitted.emit(rendered)
            self._active_template = None
        else:
            self._text_input.setEnabled(False)
            self._inline_form.set_template(template)

    def _on_palette_item_chosen(self, palette_item: PaletteItem) -> None:
        """Handle selection of any item from the CommandPalette.

        Routes to either template handling or system command dispatch.

        Args:
            palette_item: The chosen PaletteItem (template or system command).
        """
        payload = palette_item.payload
        if isinstance(payload, str) and payload.startswith("cmd:"):
            cmd_id = payload[4:]  # strip "cmd:" prefix
            self._dismiss_palette()
            self._text_input.clear()
            self.system_command.emit(cmd_id)
        else:
            # payload is a Template object
            self._on_template_chosen(payload)

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
        """Position and show the command palette above the input field."""
        self._palette.show_anchored(self._text_input)

    def _build_palette_items(
        self, query: str, *, include_system: bool = False
    ) -> list[PaletteItem]:
        """Build PaletteItem list from templates and optionally system commands.

        Args:
            query: Search query for filtering.
            include_system: Whether to include system commands.

        Returns:
            Combined list of PaletteItems.
        """
        items: list[PaletteItem] = []

        # Add system commands first
        if include_system:
            items.extend(SYSTEM_COMMANDS)

        # Add templates
        for t in self._templates:
            items.append(
                PaletteItem(
                    name=t.name,
                    description=t.description or "",
                    folder=self._get_template_folder(t),
                    payload=t,
                )
            )

        return items

    def _build_trigger_items(self, query: str) -> list[PaletteItem]:
        """Build PaletteItem list by matching template trigger fields.

        Args:
            query: Trigger query (without leading ':').

        Returns:
            List of PaletteItems matching the trigger.
        """
        items: list[PaletteItem] = []
        query_lower = query.lower()
        for t in self._templates:
            if t.trigger:
                trigger_clean = t.trigger.lstrip(":")
                if query_lower in trigger_clean.lower():
                    items.append(
                        PaletteItem(
                            name=t.name,
                            description=t.description or "",
                            folder=self._get_template_folder(t),
                            payload=t,
                        )
                    )
        return items

    def _get_template_folder(self, template: Template) -> str:
        """Get the folder name for a template, if available.

        Args:
            template: The template to check.

        Returns:
            Folder name string, or empty string if in root/unknown.
        """
        if template._path:
            from templatr.core.templates import get_templates_dir

            try:
                templates_dir = get_templates_dir()
                parent = template._path.parent
                if parent != templates_dir:
                    return parent.name
            except Exception:
                pass
        return ""

    def _track_recent(self, name: str) -> None:
        """Add a template name to the recently-used list.

        Args:
            name: Template name to track.
        """
        if name in self._recent_templates:
            self._recent_templates.remove(name)
        self._recent_templates.insert(0, name)
        self._recent_templates = self._recent_templates[: self.MAX_RECENT]

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

        if event.type() == QEvent.Type.KeyPress:
            key = event.key()
            # Forward nav keys to palette when visible
            if self._palette.isVisible() and key in (
                Qt.Key.Key_Up,
                Qt.Key.Key_Down,
                Qt.Key.Key_Return,
                Qt.Key.Key_Enter,
                Qt.Key.Key_Escape,
            ):
                self._palette.keyPressEvent(event)
                return True
            # Enter without Shift → send; Shift+Enter → newline (default)
            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                if not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                    self._on_send_clicked()
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
            "Type a message or / to select a template… (Enter to send, Shift+Enter for newline)"
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

        # Command palette (child widget, positioned absolutely)
        self._palette = CommandPalette(self)
        self._palette.item_chosen.connect(self._on_palette_item_chosen)
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
