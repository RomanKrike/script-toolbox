# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtCore


_INSTALL_MARKER = "_script_toolbox_parent_layout_context_installed"
_LEGACY_SELECTION = "_script_toolbox_legacy_layout_selection_changed"


def install_layout_property_context(editor_class):
    """Expose immediate Row/Column parent context to property editors."""
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

        editor = getattr(
            self,
            "current_property_editor",
            None
        )
        if (
            current is None or
            editor is None or
            not hasattr(
                editor,
                "set_parent_layout_context"
            )
        ):
            return result

        parent = current.parent()
        parent_kind = ""
        parent_data = None

        if parent is not None:
            parent_kind = self.item_data(
                parent,
                QtCore.Qt.UserRole
            )
            parent_id = self.item_data(
                parent,
                QtCore.Qt.UserRole + 1
            )
            parent_data = self.item_cache.get(
                parent_id
            )

        editor.set_parent_layout_context(
            parent_kind,
            parent_data
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
    "install_layout_property_context",
]
