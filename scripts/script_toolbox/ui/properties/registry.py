# -*- coding: utf-8 -*-

from ...model.item_builtins import register_builtin_items
from ...model.item_registry import ITEM_TYPES
from ...model.item_registry import bind_item_ui
from .base import EmptyPropertyEditor


def _ensure_builtin_bindings():
    from ..item_ui_bootstrap import ensure_builtin_item_ui_bindings
    ensure_builtin_item_ui_bindings()


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
    return definition.inspector


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
