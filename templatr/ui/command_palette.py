"""Command palette widget for slash-command template selection.

Provides a filterable popup palette showing templates and system commands.
Each item displays name (bold), description (truncated, gray), and folder
(badge). Supports keyboard navigation, recently-used ordering, and anchored
positioning above the input bar.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import (
    QFrame,
    QListWidget,
    QListWidgetItem,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QVBoxLayout,
    QWidget,
)


@dataclass
class PaletteItem:
    """A single entry in the command palette.

    Attributes:
        name: Display name (bold in palette).
        description: Short description (gray, truncated).
        folder: Category folder name (shown as badge).
        payload: The backing object — a Template or command identifier string.
    """

    name: str
    description: str = ""
    folder: str = ""
    payload: Any = None


class _PaletteItemDelegate(QStyledItemDelegate):
    """Custom delegate that renders name, description, and folder badge.

    Layout per row:
        [folder badge]  Name (bold)
        Description (gray, truncated)
    """

    ROW_HEIGHT = 40
    BADGE_MARGIN = 6

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionViewItem,
        index,
    ) -> None:
        """Render a palette item with name, description, and folder badge."""
        painter.save()

        # Draw selection background
        if option.state & option.State.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
            text_color = option.palette.highlightedText().color()
        else:
            text_color = option.palette.text().color()

        item_data: PaletteItem | None = index.data(Qt.ItemDataRole.UserRole)
        if item_data is None:
            painter.restore()
            return

        rect = option.rect
        x = rect.x() + 8
        y = rect.y()
        max_x = rect.right() - 8

        # Draw folder badge (if present) on the right
        badge_width = 0
        if item_data.folder:
            badge_font = QFont(option.font)
            badge_font.setPointSize(max(badge_font.pointSize() - 2, 7))
            painter.setFont(badge_font)
            badge_text = item_data.folder
            fm = painter.fontMetrics()
            badge_w = fm.horizontalAdvance(badge_text) + 10
            badge_h = fm.height() + 4
            badge_x = max_x - badge_w
            badge_y = y + (rect.height() - badge_h) // 2

            painter.setPen(QPen(QColor(100, 100, 100)))
            painter.drawRoundedRect(badge_x, badge_y, badge_w, badge_h, 4, 4)
            painter.drawText(badge_x + 5, badge_y + fm.ascent() + 2, badge_text)
            badge_width = badge_w + self.BADGE_MARGIN

        available_width = max_x - x - badge_width

        # Draw name (bold) — first line
        name_font = QFont(option.font)
        name_font.setBold(True)
        painter.setFont(name_font)
        painter.setPen(text_color)
        fm_name = painter.fontMetrics()
        elided_name = fm_name.elidedText(
            item_data.name, Qt.TextElideMode.ElideRight, available_width
        )
        painter.drawText(x, y + fm_name.ascent() + 4, elided_name)

        # Draw description (gray) — second line
        if item_data.description:
            desc_font = QFont(option.font)
            desc_font.setPointSize(max(desc_font.pointSize() - 1, 7))
            painter.setFont(desc_font)
            desc_color = QColor(140, 140, 140) if not (
                option.state & option.State.State_Selected
            ) else text_color
            painter.setPen(desc_color)
            fm_desc = painter.fontMetrics()
            elided_desc = fm_desc.elidedText(
                item_data.description, Qt.TextElideMode.ElideRight, available_width
            )
            painter.drawText(
                x, y + fm_name.height() + fm_desc.ascent() + 6, elided_desc
            )

        painter.restore()

    def sizeHint(self, option: QStyleOptionViewItem, index):  # noqa: N802
        """Return fixed row height for consistent layout."""
        from PyQt6.QtCore import QSize

        return QSize(option.rect.width(), self.ROW_HEIGHT)


class CommandPalette(QFrame):
    """Filterable popup palette for templates and system commands.

    Positioned as a child of a parent widget, not a floating dialog.
    Keyboard navigation: Up/Down to move, Enter to confirm, Escape to dismiss.

    Attributes:
        item_chosen: Signal emitted with the selected PaletteItem.
        dismissed: Signal emitted when the palette is closed without selection.
    """

    item_chosen = pyqtSignal(object)  # emits PaletteItem
    dismissed = pyqtSignal()

    def __init__(self, parent: QWidget) -> None:
        """Initialize the palette as a hidden child of parent.

        Args:
            parent: The parent widget this palette will be anchored to.
        """
        super().__init__(parent)
        self.setObjectName("command_palette")
        self._all_items: list[PaletteItem] = []
        self._recent_names: list[str] = []
        self._setup_ui()
        self.hide()

    # -- Public API ----------------------------------------------------------

    def populate(self, items: list[PaletteItem]) -> None:
        """Set the full list of palette items.

        Args:
            items: All items to display in the palette.
        """
        self._all_items = list(items)
        self._rebuild_list(self._all_items)

    def filter(self, query: str) -> None:
        """Filter displayed items to those matching query (case-insensitive).

        When query is empty, shows all items with recently-used at top.
        When query is non-empty, shows matching items ranked by relevance:
        prefix matches first, then substring matches.

        Args:
            query: Substring to match against item names.
        """
        if not query:
            ordered = self._apply_recent_order(self._all_items)
            self._rebuild_list(ordered)
        else:
            query_lower = query.lower()
            prefix_matches = []
            substring_matches = []
            for item in self._all_items:
                name_lower = item.name.lower()
                if name_lower.startswith(query_lower):
                    prefix_matches.append(item)
                elif query_lower in name_lower:
                    substring_matches.append(item)
            self._rebuild_list(prefix_matches + substring_matches)

        # Auto-select first visible item
        if self._list.count() > 0:
            self._list.setCurrentRow(0)

    def set_recent(self, names: list[str]) -> None:
        """Set the list of recently-used item names.

        Recently-used items will appear at the top of the unfiltered list.

        Args:
            names: Ordered list of recent item names (most recent first).
        """
        self._recent_names = list(names)

    def show_anchored(self, anchor: QWidget) -> None:
        """Position and show the palette above the anchor widget.

        Args:
            anchor: The widget to anchor above (typically the input bar).
        """
        self.raise_()
        row_height = _PaletteItemDelegate.ROW_HEIGHT
        visible_rows = min(5, max(self._list.count(), 1))
        palette_height = visible_rows * row_height + 12

        parent = self.parentWidget()
        if parent:
            self.setGeometry(
                0,
                parent.height() - palette_height - anchor.height() - 36,
                parent.width(),
                palette_height,
            )
        self.show()

    def item_count(self) -> int:
        """Return the total number of items in the palette.

        Returns:
            Number of items currently in the list.
        """
        return self._list.count()

    def item_data(self, row: int) -> PaletteItem | None:
        """Return the PaletteItem at the given row.

        Args:
            row: Zero-based row index.

        Returns:
            The PaletteItem, or None if row is out of range.
        """
        item = self._list.item(row)
        if item is None:
            return None
        return item.data(Qt.ItemDataRole.UserRole)

    def visible_items(self) -> list[PaletteItem]:
        """Return all currently visible PaletteItems.

        Returns:
            List of PaletteItem objects for non-hidden rows.
        """
        result = []
        for i in range(self._list.count()):
            item = self._list.item(i)
            if not item.isHidden():
                data = item.data(Qt.ItemDataRole.UserRole)
                if data is not None:
                    result.append(data)
        return result

    def selected_item(self) -> PaletteItem | None:
        """Return the currently selected PaletteItem.

        Returns:
            The selected PaletteItem, or None if nothing is selected.
        """
        current = self._list.currentItem()
        if current is None:
            return None
        return current.data(Qt.ItemDataRole.UserRole)

    # -- Keyboard handling ---------------------------------------------------

    def keyPressEvent(self, event) -> None:  # noqa: N802
        """Handle arrow/enter/escape keys for palette navigation.

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

    # -- Internal ------------------------------------------------------------

    def _confirm_selection(self) -> None:
        """Emit item_chosen for the currently highlighted item."""
        item = self._list.currentItem()
        if item and not item.isHidden():
            palette_item = item.data(Qt.ItemDataRole.UserRole)
            if palette_item is not None:
                self.item_chosen.emit(palette_item)

    def _on_item_activated(self, item: QListWidgetItem) -> None:
        """Handle double-click or Enter on a list item.

        Args:
            item: The activated QListWidgetItem.
        """
        palette_item = item.data(Qt.ItemDataRole.UserRole)
        if palette_item is not None:
            self.item_chosen.emit(palette_item)

    def _rebuild_list(self, items: list[PaletteItem]) -> None:
        """Clear and repopulate the internal QListWidget.

        Args:
            items: Ordered items to display.
        """
        self._list.clear()
        for palette_item in items:
            list_item = QListWidgetItem(palette_item.name)
            list_item.setData(Qt.ItemDataRole.UserRole, palette_item)
            self._list.addItem(list_item)

    def _apply_recent_order(self, items: list[PaletteItem]) -> list[PaletteItem]:
        """Reorder items so that recently-used ones appear first.

        Args:
            items: The full item list.

        Returns:
            New list with recent items at the front, others following in
            their original order.
        """
        if not self._recent_names:
            return items

        recent = []
        rest = []
        name_to_item: dict[str, PaletteItem] = {item.name: item for item in items}

        for name in self._recent_names:
            if name in name_to_item:
                recent.append(name_to_item[name])

        recent_set = {item.name for item in recent}
        for item in items:
            if item.name not in recent_set:
                rest.append(item)

        return recent + rest

    def _setup_ui(self) -> None:
        """Build the palette layout with a custom-delegate QListWidget."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(0)

        self._list = QListWidget()
        self._list.setItemDelegate(_PaletteItemDelegate(self._list))
        self._list.itemActivated.connect(self._on_item_activated)
        layout.addWidget(self._list)
