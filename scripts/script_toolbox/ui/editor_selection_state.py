# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtCore
from ..compat import QtGui
from ..style.palette import SELECTION_BG
from ..style.palette import SELECTION_TEXT


def _tree_selection_stylesheet():
    return (
        "QTreeWidget { "
        "show-decoration-selected: 1; "
        "selection-background-color: %s; "
        "selection-color: %s; "
        "} "
        "QTreeWidget::branch:selected { "
        "background-color: %s; "
        "}"
    ) % (
        SELECTION_BG,
        SELECTION_TEXT,
        SELECTION_BG,
    )


def _apply_selection_palette(widget):
    """Keep native tree branch selection aligned with the QSS row color."""
    if widget is None:
        return

    highlight = QtGui.QColor(
        SELECTION_BG
    )
    highlighted_text = QtGui.QColor(
        SELECTION_TEXT
    )

    for target in (
        widget,
        getattr(widget, "viewport", lambda: None)(),
    ):
        if target is None:
            continue

        try:
            palette = target.palette()
            palette.setColor(
                QtGui.QPalette.Highlight,
                highlight
            )
            palette.setColor(
                QtGui.QPalette.HighlightedText,
                highlighted_text
            )
            target.setPalette(
                palette
            )
        except Exception:
            pass

    # Maya's native Qt style paints the tree decoration / branch area through
    # the QTreeView branch sub-control instead of QPalette.Highlight.  Keep a
    # widget-local rule here so both Create Parameters and Existing Interface
    # use the same selection color without changing tree branches elsewhere.
    try:
        current_style = widget.styleSheet() or ""
        selection_style = _tree_selection_stylesheet()
        if selection_style not in current_style:
            widget.setStyleSheet(
                current_style +
                selection_style
            )
    except Exception:
        pass


def _property_scroll_value(editor):
    try:
        return int(
            editor.property_scroll.verticalScrollBar().value()
        )
    except Exception:
        return 0


def _restore_property_scroll(
    editor,
    value
):
    try:
        scroll_bar = editor.property_scroll.verticalScrollBar()
        maximum = int(
            scroll_bar.maximum()
        )
        value = max(
            0,
            min(
                int(value),
                maximum
            )
        )
        scroll_bar.setValue(
            value
        )
    except Exception:
        pass


def install_editor_selection_state(editor_class):
    """Install editor-only selection styling and Apply state preservation."""
    if getattr(
        editor_class,
        "_script_toolbox_selection_state_installed",
        False
    ):
        return editor_class

    original_build_ui = editor_class.build_ui
    original_apply_changes = editor_class.apply_changes

    def build_ui(self):
        original_build_ui(
            self
        )
        _apply_selection_palette(
            self.palette
        )
        _apply_selection_palette(
            self.tree
        )

    def apply_changes(self):
        current_id = self.current_item_id
        scroll_value = _property_scroll_value(
            self
        )

        result = original_apply_changes(
            self
        )
        if not result:
            return result

        selected = None
        if current_id:
            selected = self.tree_item_by_id(
                current_id
            )

        if selected is not None:
            self.tree.setCurrentItem(
                selected
            )

            def restore_scroll():
                _restore_property_scroll(
                    self,
                    scroll_value
                )

            try:
                QtCore.QTimer.singleShot(
                    0,
                    restore_scroll
                )
            except Exception:
                restore_scroll()

        return result

    editor_class.build_ui = build_ui
    editor_class.apply_changes = apply_changes
    editor_class._script_toolbox_selection_state_installed = True
    return editor_class


__all__ = [
    "install_editor_selection_state",
]
