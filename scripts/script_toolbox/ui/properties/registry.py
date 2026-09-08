# -*- coding: utf-8 -*-

from ...pycompat import text_type
from .base import EmptyPropertyEditor
from .basic import CheckboxPropertyEditor
from .basic import ColorPropertyEditor
from .basic import FloatPropertyEditor
from .basic import IntegerPropertyEditor
from .basic import LabelPropertyEditor
from .basic import MenuPropertyEditor
from .basic import SeparatorPropertyEditor as _SeparatorPropertyEditor
from .basic import StringPropertyEditor
from .button import ButtonPropertyEditor
from .column import ColumnPropertyEditor
from .field import FieldPropertyEditor
from .folder import FolderPropertyEditor
from .icon import IconPropertyEditor
from .row import RowPropertyEditor


class SeparatorPropertyEditor(_SeparatorPropertyEditor):
    """Schema-18 separator editor without the removed callbacks payload."""

    def write_to_item(self):
        if self.item is None:
            return

        self.item["name"] = text_type(
            self.name_edit.text()
        ).strip() or "separator"
        self.item["bindings"] = []
        self.item.pop("callbacks", None)
        self.item.pop("on_change_script", None)


PROPERTY_EDITORS = {
    "folder": FolderPropertyEditor,
    "row": RowPropertyEditor,
    "column": ColumnPropertyEditor,
    "button": ButtonPropertyEditor,
    "icon": IconPropertyEditor,
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
