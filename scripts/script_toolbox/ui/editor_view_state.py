# -*- coding: utf-8 -*-
from __future__ import print_function

from .editor_document_adapter import capture_editor_view_state
from .editor_document_adapter import restore_editor_view_state


def build_editor_view_state_class(base_class):
    """Compatibility wrapper for older direct imports.

    Active InterfaceEditor composition preserves view state inside the
    document/history adapter. This wrapper remains only for callers that still
    import and apply the historical builder directly.
    """
    class InterfaceEditor(base_class):

        def _capture_tree_view_state(self):
            return capture_editor_view_state(
                self
            )

        def _restore_tree_view_state(self, state):
            restore_editor_view_state(
                self,
                state
            )

        def apply_changes(self):
            view_state = self._capture_tree_view_state()
            result = base_class.apply_changes(self)
            if result:
                self._restore_tree_view_state(
                    view_state
                )
            return result

    InterfaceEditor.__name__ = "InterfaceEditor"
    return InterfaceEditor


__all__ = [
    "build_editor_view_state_class",
]
