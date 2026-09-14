# -*- coding: utf-8 -*-
from __future__ import print_function

from ..model.item_builtins import register_builtin_items
from ..model.item_registry import ITEM_TYPES
from . import runtime_renderers as _renderers
from .column_layout import render_column
from .image_item import ImagePropertyEditor
from .image_item import render_image
from .properties.basic import CheckboxPropertyEditor
from .properties.basic import ColorPropertyEditor
from .properties.basic import FloatPropertyEditor
from .properties.basic import IntegerPropertyEditor
from .properties.basic import LabelPropertyEditor
from .properties.basic import MenuPropertyEditor
from .properties.basic import StringPropertyEditor
from .properties.button import ButtonPropertyEditor
from .properties.column import ColumnPropertyEditor
from .properties.field import FieldPropertyEditor
from .properties.folder import FolderPropertyEditor
from .properties.icon import IconPropertyEditor
from .properties.row import RowPropertyEditor
from .properties.separator import SeparatorPropertyEditor
from .properties.text import TextPropertyEditor
from .properties.toggle_button import ToggleButtonPropertyEditor
from .properties.toggle_icon import ToggleIconPropertyEditor
from .row_layout import render_row
from .text_runtime import render_text
from .toggle_button_runtime import render_toggle_button
from .toggle_icon_runtime import render_toggle_icon


_BOOTSTRAPPED = False


def ensure_builtin_item_ui_bindings():
    """Attach Qt-side built-in implementations to registered item types.

    This is the single explicit built-in UI bootstrap. The model registry does
    not import Qt; it only stores the renderer/inspector references after the UI
    package is composed.
    """
    global _BOOTSTRAPPED
    if _BOOTSTRAPPED:
        return ITEM_TYPES

    register_builtin_items()

    inspectors = (
        ("folder", FolderPropertyEditor),
        ("row", RowPropertyEditor),
        ("column", ColumnPropertyEditor),
        ("button", ButtonPropertyEditor),
        ("toggle_button", ToggleButtonPropertyEditor),
        ("icon", IconPropertyEditor),
        ("toggle_icon", ToggleIconPropertyEditor),
        ("string", StringPropertyEditor),
        ("integer", IntegerPropertyEditor),
        ("float", FloatPropertyEditor),
        ("checkbox", CheckboxPropertyEditor),
        ("menu", MenuPropertyEditor),
        ("color", ColorPropertyEditor),
        ("field", FieldPropertyEditor),
        ("label", LabelPropertyEditor),
        ("text", TextPropertyEditor),
        ("separator", SeparatorPropertyEditor),
        ("image", ImagePropertyEditor),
    )

    renderers = (
        ("folder", _renderers._render_folder),
        ("row", render_row),
        ("column", render_column),
        ("button", _renderers._render_button),
        ("toggle_button", render_toggle_button),
        ("icon", _renderers._render_icon),
        ("toggle_icon", render_toggle_icon),
        ("string", _renderers._render_string),
        ("integer", _renderers._render_integer),
        ("float", _renderers._render_float),
        ("checkbox", _renderers._render_checkbox),
        ("menu", _renderers._render_menu),
        ("color", _renderers._render_color),
        ("field", _renderers._render_field),
        ("label", _renderers._render_label),
        ("text", render_text),
        ("separator", _renderers._render_separator),
        ("image", render_image),
    )

    for kind, inspector in inspectors:
        ITEM_TYPES.bind_ui(kind, inspector=inspector)
    for kind, renderer in renderers:
        ITEM_TYPES.bind_ui(kind, renderer=renderer)

    _BOOTSTRAPPED = True
    return ITEM_TYPES


__all__ = [
    "ensure_builtin_item_ui_bindings",
]
