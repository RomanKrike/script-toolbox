# -*- coding: utf-8 -*-

from ...pycompat import text_type
from .action_button import ActionButtonPropertyEditor
from .base import EmptyPropertyEditor
from .base import PropertyEditorBase
from .basic import CheckboxPropertyEditor
from .basic import ColorPropertyEditor
from .basic import FloatPropertyEditor
from .basic import IntegerPropertyEditor
from .basic import LabelPropertyEditor
from .basic import MenuPropertyEditor
from .basic import SeparatorPropertyEditor as _SeparatorPropertyEditor
from .basic import StringPropertyEditor
from .column import ColumnPropertyEditor
from .field import FieldPropertyEditor
from .folder import FolderPropertyEditor
from .icon import IconPropertyEditor
from .row import RowPropertyEditor
from .toggle_button import ToggleButtonPropertyEditor


class SeparatorPropertyEditor(_SeparatorPropertyEditor):
    """Schema-19 separator editor without the removed callbacks payload."""

    def write_to_item(self):
        if self.item is None:
            return

        # Use the shared writer so Row/Column item-layout settings are
        # persisted just like every other control. Separator-specific fields
        # are stripped afterwards.
        PropertyEditorBase.write_to_item(
            self
        )
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
    "button": ActionButtonPropertyEditor,
    "toggle_button": ToggleButtonPropertyEditor,
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
