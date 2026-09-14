# -*- coding: utf-8 -*-

from ...model.item_builtins import register_builtin_items
from ...model.item_registry import ITEM_TYPES
from ...model.item_registry import bind_item_ui
from ...model.item_view import item_view
from .base import EmptyPropertyEditor


_ROUTED_EDITORS = {}


def _ensure_builtin_bindings():
    from ..item_ui_bootstrap import ensure_builtin_item_ui_bindings
    ensure_builtin_item_ui_bindings()


def _routed_editor_class(editor_class):
    if editor_class is EmptyPropertyEditor:
        return editor_class
    routed = _ROUTED_EDITORS.get(editor_class)
    if routed is not None:
        return routed

    class EnvelopeRoutedEditor(editor_class):
        def bind(self, item):
            return editor_class.bind(self, item_view(item))

        def set_parent_layout_context(self, parent_kind, parent_item=None):
            if isinstance(parent_item, dict):
                parent_item = item_view(parent_item)
            return editor_class.set_parent_layout_context(
                self,
                parent_kind,
                parent_item
            )

    EnvelopeRoutedEditor.__name__ = (
        editor_class.__name__ + "EnvelopeRouted"
    )
    _ROUTED_EDITORS[editor_class] = EnvelopeRoutedEditor
    return EnvelopeRoutedEditor


def register_property_editor(kind, editor_class, replace=False):
    register_builtin_items()
    definition = ITEM_TYPES.get(kind, required=True)
    if definition.inspector is not None and not replace:
        raise ValueError(
            "Property editor already registered: {0}".format(kind)
        )
    bind_item_ui(kind, inspector=editor_class)
    return editor_class


def editor_class(kind):
    register_builtin_items()
    _ensure_builtin_bindings()
    definition = ITEM_TYPES.get(kind)
    if definition is None or definition.inspector is None:
        return EmptyPropertyEditor
    return _routed_editor_class(definition.inspector)


def create_editor(kind, toolbox=None, parent=None):
    cls = editor_class(kind)
    return cls(
        toolbox=toolbox,
        parent=parent
    )


__all__ = [
    "create_editor",
    "editor_class",
    "register_property_editor",
]
