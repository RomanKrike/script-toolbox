# -*- coding: utf-8 -*-
from __future__ import print_function

from ...model.item_builtins import register_builtin_items
from ...model.item_registry import ITEM_TYPES
from ...pycompat import text_type


_HORIZONTAL_EQUAL_SIZE_REASON = (
    "Controlled by parent horizontal layout because Equal Child Size is enabled."
)
_HORIZONTAL_WIDTH_REASON = (
    "Width properties are available only inside a horizontal layout."
)
_VERTICAL_HEIGHT_REASON = (
    "Height properties are available only inside a vertical layout."
)


class LayoutPropertyAdapter(object):
    """Bind universal Inspector layout controls through LayoutSpec metadata."""

    def __init__(self, editor):
        self.editor = editor
        self.parent_kind = ""
        self.parent_item = {}
        self.parent_definition = None
        self.parent_layout = None
        self.parent_axis = None

    def set_parent_context(self, parent_kind, parent_item=None):
        register_builtin_items()
        self.parent_kind = text_type(parent_kind or "").lower()
        self.parent_item = parent_item or {}
        self.parent_definition = ITEM_TYPES.get(self.parent_kind)
        self.parent_layout = (
            self.parent_definition.layout_spec
            if self.parent_definition is not None
            else None
        )
        self.parent_axis = (
            self.parent_layout.axis
            if self.parent_layout is not None
            else None
        )
        self.editor.row_context = self.parent_axis == "horizontal"
        self.editor.column_context = self.parent_axis == "vertical"
        parent_props = self.parent_item.get("props", {}) or {}
        equal_size_field = (
            self.parent_layout.equal_size_field
            if self.parent_layout is not None
            else None
        )
        self.editor.row_equal_widths = bool(
            self.editor.row_context and
            equal_size_field and
            parent_props.get(equal_size_field, False)
        )
        self.refresh()

    def load(self, ui):
        ui = ui if isinstance(ui, dict) else {}
        width_mode = ui.get("width_mode", "auto")
        self.editor.row_width_mode.setCurrentIndex({
            "auto": 0,
            "stretch": 1,
            "fixed": 2,
        }.get(width_mode, 0))
        self.editor.row_width.setValue(
            int(ui.get("width", 120))
        )
        self.editor.row_stretch.setValue(
            int(ui.get("stretch", 1))
        )

        height_mode = ui.get("height_mode", "auto")
        self.editor.column_height_mode.setCurrentIndex({
            "auto": 0,
            "stretch": 1,
            "fixed": 2,
        }.get(height_mode, 0))
        self.editor.column_height.setValue(
            int(ui.get("height", 28))
        )
        self.editor.column_stretch.setValue(
            int(ui.get("vertical_stretch", 1))
        )
        self.refresh()

    def write(self, ui):
        if not isinstance(ui, dict):
            return
        if (
            self.editor.row_context and
            not self.editor.row_equal_widths
        ):
            ui["width_mode"] = self.width_mode()
            ui["width"] = int(
                self.editor.row_width.value()
            )
            ui["stretch"] = int(
                self.editor.row_stretch.value()
            )

        if self.editor.column_context:
            ui["height_mode"] = self.height_mode()
            ui["height"] = int(
                self.editor.column_height.value()
            )
            ui["vertical_stretch"] = int(
                self.editor.column_stretch.value()
            )

    def width_mode(self):
        index = self.editor.row_width_mode.currentIndex()
        if index == 2:
            return "fixed"
        if index == 1:
            return "stretch"
        return "auto"

    def height_mode(self):
        index = self.editor.column_height_mode.currentIndex()
        if index == 2:
            return "fixed"
        if index == 1:
            return "stretch"
        return "auto"

    def _parent_props(self):
        if not isinstance(self.parent_item, dict):
            return {}
        value = self.parent_item.get("props", {})
        return value if isinstance(value, dict) else {}

    def _layout_prop(self, field_name, default=None):
        if not field_name:
            return default
        return self._parent_props().get(field_name, default)

    def _horizontal_parent_value(self):
        spec = self.parent_layout
        if spec is None:
            return 0
        if self.parent_axis == "vertical":
            return {
                "stretch": 0,
                "left": 1,
                "center": 2,
                "right": 3,
            }.get(
                self._layout_prop(spec.cross_alignment_field, "stretch"),
                0
            )
        if self.parent_axis == "horizontal":
            return {
                "left": 1,
                "center": 2,
                "right": 3,
                "space_between": 0,
            }.get(
                self._layout_prop(spec.distribution_field, "left"),
                1
            )
        return 0

    def _vertical_parent_value(self):
        spec = self.parent_layout
        if spec is None:
            return 0
        if self.parent_axis == "horizontal":
            return {
                "top": 1,
                "center": 2,
                "bottom": 3,
            }.get(
                self._layout_prop(spec.cross_alignment_field, "center"),
                2
            )
        if self.parent_axis == "vertical":
            return {
                "top": 1,
                "center": 2,
                "bottom": 3,
                "space_between": 0,
            }.get(
                self._layout_prop(spec.distribution_field, "top"),
                1
            )
        return 0

    def _horizontal_alignment_reason(self):
        if self.parent_axis == "vertical":
            return "Controlled by parent vertical layout > Cross Alignment."
        if self.parent_axis == "horizontal":
            return "Controlled by parent horizontal layout > Distribution."
        return "Per-child horizontal alignment override is not supported."

    def _vertical_alignment_reason(self):
        if self.parent_axis == "horizontal":
            return "Controlled by parent horizontal layout > Cross Alignment."
        if self.parent_axis == "vertical":
            return "Controlled by parent vertical layout > Distribution."
        return "Per-child vertical alignment override is not supported."

    def refresh(self):
        editor = self.editor
        width_mode = self.width_mode()
        height_mode = self.height_mode()

        if editor.row_equal_widths:
            width_reason = _HORIZONTAL_EQUAL_SIZE_REASON
            editor.set_property_available(
                editor.row_width_mode,
                False,
                width_reason
            )
            editor.set_property_available(
                editor.row_width,
                False,
                width_reason
            )
            editor.set_property_available(
                editor.row_stretch,
                False,
                width_reason
            )
        elif editor.row_context:
            editor.set_property_available(
                editor.row_width_mode,
                True
            )
            editor.set_property_available(
                editor.row_width,
                width_mode == "fixed",
                "Available when Width Mode is Fixed."
            )
            editor.set_property_available(
                editor.row_stretch,
                width_mode == "stretch",
                "Available when Width Mode is Stretch."
            )
        else:
            editor.set_property_available(
                editor.row_width_mode,
                False,
                _HORIZONTAL_WIDTH_REASON
            )
            editor.set_property_available(
                editor.row_width,
                False,
                _HORIZONTAL_WIDTH_REASON
            )
            editor.set_property_available(
                editor.row_stretch,
                False,
                _HORIZONTAL_WIDTH_REASON
            )

        if editor.column_context:
            editor.set_property_available(
                editor.column_height_mode,
                True
            )
            editor.set_property_available(
                editor.column_height,
                height_mode == "fixed",
                "Available when Height Mode is Fixed."
            )
            editor.set_property_available(
                editor.column_stretch,
                height_mode == "stretch",
                "Available when Height Mode is Stretch."
            )
        else:
            editor.set_property_available(
                editor.column_height_mode,
                False,
                _VERTICAL_HEIGHT_REASON
            )
            editor.set_property_available(
                editor.column_height,
                False,
                _VERTICAL_HEIGHT_REASON
            )
            editor.set_property_available(
                editor.column_stretch,
                False,
                _VERTICAL_HEIGHT_REASON
            )

        editor.layout_horizontal_alignment.setCurrentIndex(
            self._horizontal_parent_value()
        )
        editor.layout_vertical_alignment.setCurrentIndex(
            self._vertical_parent_value()
        )
        editor.set_property_available(
            editor.layout_horizontal_alignment,
            False,
            self._horizontal_alignment_reason()
        )
        editor.set_property_available(
            editor.layout_vertical_alignment,
            False,
            self._vertical_alignment_reason()
        )


__all__ = [
    "LayoutPropertyAdapter",
]
