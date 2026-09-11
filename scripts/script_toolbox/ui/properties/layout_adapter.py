# -*- coding: utf-8 -*-
from __future__ import print_function

from ...pycompat import text_type


_ROW_EQUAL_SIZE_REASON = (
    "Controlled by parent Row because Equal Child Size is enabled."
)
_ROW_WIDTH_REASON = "Width properties are available only for items inside a Row."
_COLUMN_HEIGHT_REASON = (
    "Height properties are available only for items inside a Column."
)


class LayoutPropertyAdapter(object):
    """Bridge unified Inspector layout controls to the existing config keys."""

    def __init__(self, editor):
        self.editor = editor
        self.parent_kind = ""
        self.parent_item = {}

    def set_parent_context(self, parent_kind, parent_item=None):
        self.parent_kind = text_type(parent_kind or "").lower()
        self.parent_item = parent_item or {}
        self.editor.row_context = self.parent_kind == "row"
        self.editor.column_context = self.parent_kind == "column"
        self.editor.row_equal_widths = bool(
            self.editor.row_context and
            self.parent_item.get("equal_widths", False)
        )
        self.refresh()

    def load(self, item):
        width_mode = item.get("row_width_mode", "auto")
        self.editor.row_width_mode.setCurrentIndex({
            "auto": 0,
            "stretch": 1,
            "fixed": 2,
        }.get(width_mode, 0))
        self.editor.row_width.setValue(
            int(item.get("row_width", 120))
        )
        self.editor.row_stretch.setValue(
            int(item.get("row_stretch", 1))
        )

        height_mode = item.get("column_height_mode", "auto")
        self.editor.column_height_mode.setCurrentIndex({
            "auto": 0,
            "stretch": 1,
            "fixed": 2,
        }.get(height_mode, 0))
        self.editor.column_height.setValue(
            int(item.get("column_height", 28))
        )
        self.editor.column_stretch.setValue(
            int(item.get("column_stretch", 1))
        )
        self.refresh()

    def write(self, item):
        if (
            self.editor.row_context and
            not self.editor.row_equal_widths
        ):
            item["row_width_mode"] = self.width_mode()
            item["row_width"] = int(
                self.editor.row_width.value()
            )
            item["row_stretch"] = int(
                self.editor.row_stretch.value()
            )

        if self.editor.column_context:
            item["column_height_mode"] = self.height_mode()
            item["column_height"] = int(
                self.editor.column_height.value()
            )
            item["column_stretch"] = int(
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

    def _horizontal_parent_value(self):
        if self.parent_kind == "column":
            return {
                "stretch": 0,
                "left": 1,
                "center": 2,
                "right": 3,
            }.get(
                self.parent_item.get("horizontal_alignment", "stretch"),
                0
            )
        if self.parent_kind == "row":
            return {
                "left": 1,
                "center": 2,
                "right": 3,
                "space_between": 0,
            }.get(
                self.parent_item.get("horizontal_distribution", "left"),
                1
            )
        return 0

    def _vertical_parent_value(self):
        if self.parent_kind == "row":
            return {
                "top": 1,
                "center": 2,
                "bottom": 3,
            }.get(
                self.parent_item.get("vertical_alignment", "center"),
                2
            )
        if self.parent_kind == "column":
            return {
                "top": 1,
                "center": 2,
                "bottom": 3,
                "space_between": 0,
            }.get(
                self.parent_item.get("vertical_distribution", "top"),
                1
            )
        return 0

    def _horizontal_alignment_reason(self):
        if self.parent_kind == "column":
            return "Controlled by parent Column > Cross Alignment."
        if self.parent_kind == "row":
            return "Controlled by parent Row > Distribution."
        return "Per-child horizontal alignment override is not supported."

    def _vertical_alignment_reason(self):
        if self.parent_kind == "row":
            return "Controlled by parent Row > Cross Alignment."
        if self.parent_kind == "column":
            return "Controlled by parent Column > Distribution."
        return "Per-child vertical alignment override is not supported."

    def refresh(self):
        editor = self.editor
        width_mode = self.width_mode()
        height_mode = self.height_mode()

        if editor.row_equal_widths:
            width_reason = _ROW_EQUAL_SIZE_REASON
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
                _ROW_WIDTH_REASON
            )
            editor.set_property_available(
                editor.row_width,
                False,
                _ROW_WIDTH_REASON
            )
            editor.set_property_available(
                editor.row_stretch,
                False,
                _ROW_WIDTH_REASON
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
                _COLUMN_HEIGHT_REASON
            )
            editor.set_property_available(
                editor.column_height,
                False,
                _COLUMN_HEIGHT_REASON
            )
            editor.set_property_available(
                editor.column_stretch,
                False,
                _COLUMN_HEIGHT_REASON
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
