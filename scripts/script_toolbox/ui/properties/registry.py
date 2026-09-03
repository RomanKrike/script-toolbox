# -*- coding: utf-8 -*-

from .base import EmptyPropertyEditor
from .basic import CheckboxPropertyEditor
from .basic import ColorPropertyEditor
from .basic import FloatPropertyEditor
from .basic import IntegerPropertyEditor
from .basic import LabelPropertyEditor
from .basic import MenuPropertyEditor
from .basic import SeparatorPropertyEditor
from .basic import StringPropertyEditor
from .button import ButtonPropertyEditor
from .field import FieldPropertyEditor
from .folder import FolderPropertyEditor
from .row import RowPropertyEditor


PROPERTY_EDITORS = {
    "folder": FolderPropertyEditor,
    "row": RowPropertyEditor,
    "button": ButtonPropertyEditor,
    "string": StringPropertyEditor,
    "integer": IntegerPropertyEditor,
    "float": FloatPropertyEditor,
    "checkbox": CheckboxPropertyEditor,
    "menu": MenuPropertyEditor,
    "color": ColorPropertyEditor,
    "field": FieldPropertyEditor,
    "label": LabelPropertyEditor,
    "separator": SeparatorPropertyEditor,
}


def editor_class(
    kind
):
    return PROPERTY_EDITORS.get(
        kind,
        EmptyPropertyEditor
    )


def create_editor(
    kind,
    toolbox=None,
    parent=None
):
    cls = editor_class(
        kind
    )

    return cls(
        toolbox=toolbox,
        parent=parent
    )


__all__ = [
    "PROPERTY_EDITORS",
    "create_editor",
    "editor_class",
]
