# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtCore


_INSTALL_MARKER = "_script_toolbox_parent_layout_context_installed"
_LEGACY_SELECTION = "_script_toolbox_legacy_layout_selection_changed"


def apply_layout_property_context(editor, current):
    """Expose the selected item's immediate Row/Column parent to its editor."""
    property_editor = getattr(
        editor,
        "current_property_editor",
        None
    )
    if (
        current is None or
        property_editor is None or
        not hasattr(
            property_editor,
            "set_parent_layout_context"
        )
    ):
        return

    parent = current.parent()
    parent_kind = ""
    parent_data = None

    if parent is not None:
        parent_kind = editor.item_data(
            parent,
            QtCore.Qt.UserRole
        )
        parent_id = editor.item_data(
            parent,
            QtCore.Qt.UserRole + 1
        )
        parent_data = editor.item_cache.get(
            parent_id
        )

    property_editor.set_parent_layout_context(
        parent_kind,
        parent_data
    )


def install_layout_property_context(editor_class):
    """Compatibility installer for older direct imports.

    Active InterfaceEditor composition calls apply_layout_property_context()
    directly from the document adapter instead of patching selection_changed.
    """
    if getattr(
        editor_class,
        _INSTALL_MARKER,
        False
    ):
        return editor_class

    setattr(
        editor_class,
        _LEGACY_SELECTION,
        editor_class.selection_changed
    )

    def selection_changed(self, current, previous):
        result = getattr(
            self.__class__,
            _LEGACY_SELECTION
        )(self, current, previous)
        apply_layout_property_context(
            self,
            current
        )
        return result

    editor_class.selection_changed = selection_changed
    setattr(
        editor_class,
        _INSTALL_MARKER,
        True
    )
    return editor_class


__all__ = [
    "apply_layout_property_context",
    "install_layout_property_context",
]
