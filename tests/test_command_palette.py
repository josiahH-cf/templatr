"""Tests for CommandPalette widget.

Covers:
- Palette displays items with name, description, and folder
- filter() narrows visible items in real-time
- Keyboard navigation: Up/Down moves selection, Enter emits item_chosen, Escape emits dismissed
- Recently-used items appear at top of unfiltered list
- show_anchored() positions the palette above the parent widget
"""

from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QWidget

from templatr.ui.command_palette import CommandPalette, PaletteItem


def _make_items():
    """Build a sample list of PaletteItem objects for testing."""
    return [
        PaletteItem(
            name="Code Review",
            description="Reviews code for quality issues",
            folder="coding",
            payload="template:code_review",
        ),
        PaletteItem(
            name="Summarize Text",
            description="Summarizes a block of text",
            folder="writing",
            payload="template:summarize_text",
        ),
        PaletteItem(
            name="Quick Note",
            description="A quick note template",
            folder="",
            payload="template:quick_note",
        ),
        PaletteItem(
            name="Code Explain",
            description="Explains code in detail",
            folder="coding",
            payload="template:code_explain",
        ),
    ]


# -- Display tests -----------------------------------------------------------


def test_palette_hidden_initially(qtbot):
    """CommandPalette is hidden when first created."""
    parent = QWidget()
    palette = CommandPalette(parent)
    qtbot.addWidget(parent)
    assert not palette.isVisible()


def test_populate_shows_all_items(qtbot):
    """populate() makes all items available in the palette."""
    parent = QWidget()
    palette = CommandPalette(parent)
    qtbot.addWidget(parent)
    items = _make_items()
    palette.populate(items)

    assert palette.item_count() == len(items)


def test_items_display_name_description_folder(qtbot):
    """Each item exposes name, description, and folder data."""
    parent = QWidget()
    palette = CommandPalette(parent)
    qtbot.addWidget(parent)
    items = _make_items()
    palette.populate(items)

    # Verify first item has the right data accessible
    data = palette.item_data(0)
    assert data is not None
    assert data.name == "Code Review"
    assert data.description == "Reviews code for quality issues"
    assert data.folder == "coding"


# -- Filter tests ------------------------------------------------------------


def test_filter_narrows_to_matching_items(qtbot):
    """filter('code') shows only items whose name contains 'code'."""
    parent = QWidget()
    palette = CommandPalette(parent)
    qtbot.addWidget(parent)
    palette.populate(_make_items())

    palette.filter("code")

    visible = palette.visible_items()
    assert len(visible) == 2
    names = {item.name for item in visible}
    assert names == {"Code Review", "Code Explain"}


def test_filter_case_insensitive(qtbot):
    """Filtering is case-insensitive."""
    parent = QWidget()
    palette = CommandPalette(parent)
    qtbot.addWidget(parent)
    palette.populate(_make_items())

    palette.filter("CODE")

    visible = palette.visible_items()
    assert len(visible) == 2


def test_filter_empty_string_shows_all(qtbot):
    """Filtering with empty string restores all items."""
    parent = QWidget()
    palette = CommandPalette(parent)
    qtbot.addWidget(parent)
    palette.populate(_make_items())

    palette.filter("code")
    palette.filter("")

    visible = palette.visible_items()
    assert len(visible) == 4


def test_filter_no_match_shows_nothing(qtbot):
    """Filtering with a non-matching query shows zero items."""
    parent = QWidget()
    palette = CommandPalette(parent)
    qtbot.addWidget(parent)
    palette.populate(_make_items())

    palette.filter("zzzzz")

    visible = palette.visible_items()
    assert len(visible) == 0


def test_filter_auto_selects_first_visible(qtbot):
    """After filtering, the first visible item is auto-selected."""
    parent = QWidget()
    palette = CommandPalette(parent)
    qtbot.addWidget(parent)
    palette.populate(_make_items())

    palette.filter("summ")

    selected = palette.selected_item()
    assert selected is not None
    assert selected.name == "Summarize Text"


# -- Keyboard navigation tests -----------------------------------------------


def test_down_arrow_moves_selection(qtbot):
    """Down arrow key moves selection to the next visible item."""
    parent = QWidget()
    palette = CommandPalette(parent)
    qtbot.addWidget(parent)
    parent.show()
    palette.populate(_make_items())
    palette.filter("")  # show all, select first

    palette.keyPressEvent(_key_event(Qt.Key.Key_Down))

    selected = palette.selected_item()
    # Second item after initial auto-select of first
    assert selected is not None
    assert selected.name == "Summarize Text"


def test_up_arrow_moves_selection(qtbot):
    """Up arrow key moves selection to the previous item."""
    parent = QWidget()
    palette = CommandPalette(parent)
    qtbot.addWidget(parent)
    parent.show()
    palette.populate(_make_items())
    palette.filter("")

    palette.keyPressEvent(_key_event(Qt.Key.Key_Down))
    palette.keyPressEvent(_key_event(Qt.Key.Key_Up))

    selected = palette.selected_item()
    assert selected is not None
    assert selected.name == "Code Review"


def test_enter_emits_item_chosen(qtbot):
    """Pressing Enter emits item_chosen with the selected PaletteItem."""
    parent = QWidget()
    palette = CommandPalette(parent)
    qtbot.addWidget(parent)
    parent.show()
    palette.populate(_make_items())
    palette.filter("")

    with qtbot.waitSignal(palette.item_chosen, timeout=1000) as sig:
        palette.keyPressEvent(_key_event(Qt.Key.Key_Return))

    assert sig.args[0].name == "Code Review"


def test_escape_emits_dismissed(qtbot):
    """Pressing Escape emits dismissed signal."""
    parent = QWidget()
    palette = CommandPalette(parent)
    qtbot.addWidget(parent)
    parent.show()
    palette.populate(_make_items())

    with qtbot.waitSignal(palette.dismissed, timeout=1000):
        palette.keyPressEvent(_key_event(Qt.Key.Key_Escape))


# -- Recently-used tests -----------------------------------------------------


def test_set_recent_reorders_unfiltered_list(qtbot):
    """set_recent() places recently-used items at the top of the unfiltered list."""
    parent = QWidget()
    palette = CommandPalette(parent)
    qtbot.addWidget(parent)
    palette.populate(_make_items())

    palette.set_recent(["Quick Note", "Summarize Text"])
    palette.filter("")  # unfiltered

    visible = palette.visible_items()
    assert visible[0].name == "Quick Note"
    assert visible[1].name == "Summarize Text"


def test_set_recent_does_not_affect_filtered_list(qtbot):
    """set_recent() does not affect filter results (filter ranks by match only)."""
    parent = QWidget()
    palette = CommandPalette(parent)
    qtbot.addWidget(parent)
    palette.populate(_make_items())

    palette.set_recent(["Quick Note"])
    palette.filter("code")

    visible = palette.visible_items()
    names = {item.name for item in visible}
    assert "Quick Note" not in names


# -- Anchoring tests ---------------------------------------------------------


def test_show_anchored_makes_palette_visible(qtbot):
    """show_anchored() makes the palette visible."""
    parent = QWidget()
    parent.resize(400, 300)
    palette = CommandPalette(parent)
    qtbot.addWidget(parent)
    parent.show()
    palette.populate(_make_items())

    palette.show_anchored(parent)

    assert palette.isVisible()


def test_show_anchored_positions_above_parent(qtbot):
    """show_anchored() positions the palette so its bottom edge is near the parent's top."""
    parent = QWidget()
    parent.resize(400, 300)
    palette = CommandPalette(parent)
    qtbot.addWidget(parent)
    parent.show()
    palette.populate(_make_items())

    palette.show_anchored(parent)

    # Palette y + height should be <= parent height (i.e. not below the parent)
    assert palette.geometry().bottom() <= parent.height()


# -- Helpers -----------------------------------------------------------------


def _key_event(key):
    """Create a minimal key event for testing keyPressEvent."""
    from PyQt6.QtGui import QKeyEvent
    from PyQt6.QtCore import QEvent

    return QKeyEvent(QEvent.Type.KeyPress, key, Qt.KeyboardModifier.NoModifier)
