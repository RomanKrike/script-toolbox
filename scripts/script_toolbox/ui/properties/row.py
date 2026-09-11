# -*- coding: utf-8 -*-
from __future__ import print_function

from ...compat import QtGui
from .base import PropertyEditorBase


class RowPropertyEditor(PropertyEditorBase):

    def __init__(self, toolbox=None, parent=None):
        PropertyEditorBase.__init__(self, toolbox, parent)

        self.direction = QtGui.QComboBox()
        self.direction.addItem("Horizontal")
        self.spacing = QtGui.QSpinBox()
        self.spacing.setRange(0, 30)
        self.equal_widths = QtGui.QCheckBox()
        self.horizontal_distribution = QtGui.QComboBox()
        self.horizontal_distribution.addItems([
            "Start",
            "Center",
            "End",
            "Space Between",
        ])
        self.vertical_alignment = QtGui.QComboBox()
        self.vertical_alignment.addItems([
            "Start",
            "Center",
            "End",
        ])

        section = self.container_layout_section
        section.addRow("Direction", self.direction)
        section.addRow("Spacing", self.spacing)
        section.addRow(
            "Distribution",
            self.horizontal_distribution
        )
        section.addRow(
            "Cross Alignment",
            self.vertical_alignment
        )
        section.addRow(
            "Equal Child Size",
            self.equal_widths
        )

        self.set_property_available(
            self.direction,
            False,
            "Row direction is fixed to Horizontal by the current runtime."
        )

        note = QtGui.QLabel(
            "Row distributes children horizontally. Select a child to edit "
            "its Width Mode in LAYOUT. Distribution uses remaining free "
            "space, so it has no visible effect while Stretch or Equal Child "
            "Size consumes that space."
        )
        note.setObjectName("HintText")
        note.setWordWrap(True)
        section.addWidget(note)
        self.add_stretch()

        self.spacing.valueChanged.connect(self._control_changed)
        self.equal_widths.toggled.connect(self._control_changed)
        self.horizontal_distribution.currentIndexChanged.connect(
            self._control_changed
        )
        self.vertical_alignment.currentIndexChanged.connect(
            self._control_changed
        )

    def load_specific(self, item):
        self.spacing.setValue(
            int(item.get("spacing", 4))
        )
        self.equal_widths.setChecked(
            bool(item.get("equal_widths", False))
        )
        self.horizontal_distribution.setCurrentIndex({
            "left": 0,
            "center": 1,
            "right": 2,
            "space_between": 3,
        }.get(
            item.get("horizontal_distribution", "left"),
            0
        ))
        self.vertical_alignment.setCurrentIndex({
            "top": 0,
            "center": 1,
            "bottom": 2,
        }.get(
            item.get("vertical_alignment", "center"),
            1
        ))

    def write_specific(self, item):
        item["spacing"] = int(self.spacing.value())
        item["equal_widths"] = bool(
            self.equal_widths.isChecked()
        )
        item["horizontal_distribution"] = (
            "center"
            if self.horizontal_distribution.currentIndex() == 1
            else "right"
            if self.horizontal_distribution.currentIndex() == 2
            else "space_between"
            if self.horizontal_distribution.currentIndex() == 3
            else "left"
        )
        item["vertical_alignment"] = (
            "top"
            if self.vertical_alignment.currentIndex() == 0
            else "bottom"
            if self.vertical_alignment.currentIndex() == 2
            else "center"
        )


__all__ = [
    "RowPropertyEditor",
]
