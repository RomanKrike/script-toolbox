# -*- coding: utf-8 -*-
from __future__ import print_function

from ...compat import QtGui
from .base import PropertyEditorBase


class ColumnPropertyEditor(PropertyEditorBase):

    def __init__(self, toolbox=None, parent=None):
        PropertyEditorBase.__init__(self, toolbox, parent)

        self.direction = QtGui.QComboBox()
        self.direction.addItem("Vertical")
        self.spacing = QtGui.QSpinBox()
        self.spacing.setRange(0, 30)
        self.vertical_distribution = QtGui.QComboBox()
        self.vertical_distribution.addItems([
            "Start",
            "Center",
            "End",
            "Space Between",
        ])
        self.horizontal_alignment = QtGui.QComboBox()
        self.horizontal_alignment.addItems([
            "Stretch",
            "Start",
            "Center",
            "End",
        ])
        self.equal_child_size = QtGui.QCheckBox()

        section = self.container_layout_section
        section.addRow("Direction", self.direction)
        section.addRow("Spacing", self.spacing)
        section.addRow(
            "Distribution",
            self.vertical_distribution
        )
        section.addRow(
            "Cross Alignment",
            self.horizontal_alignment
        )
        section.addRow(
            "Equal Child Size",
            self.equal_child_size
        )

        self.set_property_available(
            self.direction,
            False,
            "Column direction is fixed to Vertical by the current runtime."
        )
        self.set_property_available(
            self.equal_child_size,
            False,
            "Equal Child Size is not supported by Column layout yet."
        )

        note = QtGui.QLabel(
            "Column stacks controls, Rows and Columns vertically. Select a "
            "child to edit its Height Mode in LAYOUT. Distribution uses "
            "remaining free space, so it has no visible effect while a child "
            "uses Stretch height."
        )
        note.setObjectName("HintText")
        note.setWordWrap(True)
        section.addWidget(note)
        self.add_stretch()

        self.spacing.valueChanged.connect(self._control_changed)
        self.horizontal_alignment.currentIndexChanged.connect(
            self._control_changed
        )
        self.vertical_distribution.currentIndexChanged.connect(
            self._control_changed
        )

    def load_specific(self, item):
        self.spacing.setValue(
            int(item.get("spacing", 4))
        )
        self.horizontal_alignment.setCurrentIndex({
            "stretch": 0,
            "left": 1,
            "center": 2,
            "right": 3,
        }.get(
            item.get("horizontal_alignment", "stretch"),
            0
        ))
        self.vertical_distribution.setCurrentIndex({
            "top": 0,
            "center": 1,
            "bottom": 2,
            "space_between": 3,
        }.get(
            item.get("vertical_distribution", "top"),
            0
        ))

    def write_specific(self, item):
        item["spacing"] = int(self.spacing.value())
        item["horizontal_alignment"] = (
            "left"
            if self.horizontal_alignment.currentIndex() == 1
            else "center"
            if self.horizontal_alignment.currentIndex() == 2
            else "right"
            if self.horizontal_alignment.currentIndex() == 3
            else "stretch"
        )
        item["vertical_distribution"] = (
            "center"
            if self.vertical_distribution.currentIndex() == 1
            else "bottom"
            if self.vertical_distribution.currentIndex() == 2
            else "space_between"
            if self.vertical_distribution.currentIndex() == 3
            else "top"
        )


__all__ = [
    "ColumnPropertyEditor",
]
