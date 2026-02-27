"""Template editor widget for Templatr."""

from typing import List, Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)

from templatr.core.templates import Template, Variable, get_template_manager


class VariableEditor(QDialog):
    """Dialog for editing a single variable."""

    def __init__(self, variable: Optional[Variable] = None, parent=None):
        super().__init__(parent)
        self.variable = variable
        self.setWindowTitle("Edit Variable" if variable else "Add Variable")
        self.setMinimumWidth(400)
        self._setup_ui()

        if variable:
            self._load_variable(variable)

    def _setup_ui(self):
        layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., code, language, description")
        layout.addRow("Name:", self.name_edit)

        self.label_edit = QLineEdit()
        self.label_edit.setPlaceholderText("Display label (optional)")
        layout.addRow("Label:", self.label_edit)

        self.default_edit = QLineEdit()
        self.default_edit.setPlaceholderText("Default value (optional)")
        layout.addRow("Default:", self.default_edit)

        self.multiline_check = QCheckBox("Multi-line input")
        layout.addRow("", self.multiline_check)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _load_variable(self, var: Variable):
        self.name_edit.setText(var.name)
        self.label_edit.setText(var.label)
        self.default_edit.setText(var.default)
        self.multiline_check.setChecked(var.multiline)

    def get_variable(self) -> Optional[Variable]:
        name = self.name_edit.text().strip()
        if not name:
            return None

        return Variable(
            name=name,
            label=self.label_edit.text().strip(),
            default=self.default_edit.text().strip(),
            multiline=self.multiline_check.isChecked(),
        )


class TemplateEditor(QDialog):
    """Dialog for editing a template."""

    template_saved = pyqtSignal(Template)

    def __init__(self, template: Optional[Template] = None, parent=None, last_folder: str = ""):
        super().__init__(parent)
        self.template = template
        self.variables: list[Variable] = list(template.variables) if template else []
        self.refinements: list[str] = list(template.refinements) if template else []
        self._last_folder = last_folder

        # Get initial folder for existing templates
        self._initial_folder = ""
        if template:
            manager = get_template_manager()
            self._initial_folder = manager.get_template_folder(template)

        self.setWindowTitle("Edit Template" if template else "New Template")
        self.setMinimumSize(600, 500)
        self._setup_ui()

        if template:
            self._load_template(template)

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Form layout for basic fields
        form = QFormLayout()

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Template name")
        form.addRow("Name:", self.name_edit)

        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Short description (optional)")
        form.addRow("Description:", self.description_edit)

        # Folder selection
        self.folder_combo = QComboBox()
        self._populate_folders()
        form.addRow("Folder:", self.folder_combo)

        layout.addLayout(form)

        # Variables section
        var_label = QLabel("Variables:")
        layout.addWidget(var_label)

        var_layout = QHBoxLayout()

        self.var_list = QListWidget()
        self.var_list.setMaximumHeight(120)
        var_layout.addWidget(self.var_list)

        var_buttons = QVBoxLayout()

        add_var_btn = QPushButton("Add")
        add_var_btn.clicked.connect(self._add_variable)
        var_buttons.addWidget(add_var_btn)

        edit_var_btn = QPushButton("Edit")
        edit_var_btn.clicked.connect(self._edit_variable)
        var_buttons.addWidget(edit_var_btn)

        del_var_btn = QPushButton("Delete")
        del_var_btn.setObjectName("danger")
        del_var_btn.clicked.connect(self._delete_variable)
        var_buttons.addWidget(del_var_btn)

        var_buttons.addStretch()
        var_layout.addLayout(var_buttons)

        layout.addLayout(var_layout)

        # Refinements section (feedback-based improvements) - only show if there are refinements
        self.refinements_label = QLabel("Refinements (from feedback):")
        layout.addWidget(self.refinements_label)

        refinements_layout = QHBoxLayout()

        self.refinements_list = QListWidget()
        self.refinements_list.setMaximumHeight(80)
        refinements_layout.addWidget(self.refinements_list)

        refinements_buttons = QVBoxLayout()

        edit_ref_btn = QPushButton("Edit")
        edit_ref_btn.clicked.connect(self._edit_refinement)
        refinements_buttons.addWidget(edit_ref_btn)

        del_ref_btn = QPushButton("Delete")
        del_ref_btn.setObjectName("danger")
        del_ref_btn.clicked.connect(self._delete_refinement)
        refinements_buttons.addWidget(del_ref_btn)

        refinements_buttons.addStretch()
        refinements_layout.addLayout(refinements_buttons)

        layout.addLayout(refinements_layout)

        # Hide refinements section if no refinements
        self._update_refinements_visibility()

        # Content section
        content_header = QHBoxLayout()
        content_label = QLabel("Content (use {{variable_name}} for placeholders):")
        content_header.addWidget(content_label)
        content_header.addStretch()

        generate_btn = QPushButton("Generate with AI...")
        generate_btn.setObjectName("secondary")
        generate_btn.setToolTip("Use AI to generate template content from a description")
        generate_btn.clicked.connect(self._generate_with_ai)
        content_header.addWidget(generate_btn)

        layout.addLayout(content_header)

        self.content_edit = QPlainTextEdit()
        self.content_edit.setPlaceholderText(
            "Enter your template content here.\n"
            "Use {{variable_name}} for placeholders."
        )
        layout.addWidget(self.content_edit)

        # Dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_template(self, template: Template):
        self.name_edit.setText(template.name)
        self.description_edit.setText(template.description)
        self.content_edit.setPlainText(template.content)
        self._refresh_var_list()
        self._refresh_refinements_list()
        self._update_refinements_visibility()

    def _refresh_var_list(self):
        self.var_list.clear()
        for var in self.variables:
            text = f"{{{{ {var.name} }}}}"
            if var.label != var.name:
                text += f" - {var.label}"
            if var.multiline:
                text += " [multiline]"
            self.var_list.addItem(text)

    def _refresh_refinements_list(self):
        """Refresh the refinements list widget."""
        self.refinements_list.clear()
        for ref in self.refinements:
            # Truncate long refinements for display
            display_text = ref if len(ref) <= 60 else ref[:57] + "..."
            self.refinements_list.addItem(display_text)

    def _update_refinements_visibility(self):
        """Show/hide refinements section based on whether there are any."""
        has_refinements = len(self.refinements) > 0
        self.refinements_label.setVisible(has_refinements)
        self.refinements_list.setVisible(has_refinements)
        # Find and hide the refinements layout parent widgets
        self.refinements_list.parentWidget()  # This is a bit hacky but works

    def _edit_refinement(self):
        """Edit the selected refinement."""
        row = self.refinements_list.currentRow()
        if row < 0 or row >= len(self.refinements):
            return

        from PyQt6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getMultiLineText(
            self,
            "Edit Refinement",
            "Edit the feedback refinement:",
            self.refinements[row],
        )

        if ok and text.strip():
            self.refinements[row] = text.strip()
            self._refresh_refinements_list()

    def _delete_refinement(self):
        """Delete the selected refinement."""
        row = self.refinements_list.currentRow()
        if row < 0 or row >= len(self.refinements):
            return

        del self.refinements[row]
        self._refresh_refinements_list()
        self._update_refinements_visibility()

    def _add_variable(self):
        dialog = VariableEditor(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            var = dialog.get_variable()
            if var:
                self.variables.append(var)
                self._refresh_var_list()

    def _edit_variable(self):
        row = self.var_list.currentRow()
        if row < 0 or row >= len(self.variables):
            return

        dialog = VariableEditor(self.variables[row], parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            var = dialog.get_variable()
            if var:
                self.variables[row] = var
                self._refresh_var_list()

    def _delete_variable(self):
        row = self.var_list.currentRow()
        if row < 0 or row >= len(self.variables):
            return

        del self.variables[row]
        self._refresh_var_list()

    def _populate_folders(self):
        """Populate the folder combobox."""
        manager = get_template_manager()
        self.folder_combo.clear()
        self.folder_combo.addItem("(No folder)", "")  # Root level

        for folder in manager.list_folders():
            self.folder_combo.addItem(f"📁 {folder}", folder)

        # Select initial folder (existing template) or last used folder (new template)
        folder_to_select = self._initial_folder or self._last_folder
        if folder_to_select:
            index = self.folder_combo.findData(folder_to_select)
            if index >= 0:
                self.folder_combo.setCurrentIndex(index)

    def _save(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Template name is required.")
            return

        content = self.content_edit.toPlainText().strip()
        if not content:
            QMessageBox.warning(self, "Error", "Template content is required.")
            return

        # Get selected folder
        folder = self.folder_combo.currentData() or ""

        # Create or update template
        if self.template:
            self.template.name = name
            self.template.description = self.description_edit.text().strip()
            self.template.content = content
            self.template.variables = self.variables
            self.template.refinements = self.refinements
            template = self.template
        else:
            template = Template(
                name=name,
                description=self.description_edit.text().strip(),
                content=content,
                variables=self.variables,
                refinements=self.refinements,
            )

        # Save to disk (with folder support)
        manager = get_template_manager()
        if manager.save_to_folder(template, folder):
            self.template_saved.emit(template)
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "Failed to save template.")

    def _generate_with_ai(self):
        """Open the AI generation dialog and populate content."""
        from templatr.ui.template_generate import TemplateGenerateDialog

        dialog = TemplateGenerateDialog(self)
        dialog.content_generated.connect(self._on_content_generated)
        dialog.exec()

    def _on_content_generated(self, content: str, found_variables: List[str]):
        """Handle generated content from AI.

        Args:
            content: The generated template content.
            found_variables: List of variable names found in the content.
        """
        # Set the content
        self.content_edit.setPlainText(content)

        # Add any new variables that were found
        existing_names = {v.name for v in self.variables}
        for var_name in found_variables:
            if var_name not in existing_names:
                self.variables.append(Variable(
                    name=var_name,
                    label=var_name.replace("_", " ").title(),
                    default="",
                    multiline=False,
                ))

        self._refresh_var_list()

        # Create initial version if this is a new template with generated content
        if not self.template and content:
            get_template_manager()
            # We'll let the save process handle versioning when the user saves
