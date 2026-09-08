# -*- coding: utf-8 -*-
from __future__ import print_function

from ...compat import QtGui
from .base import PropertyEditorBase


class ColumnPropertyEditor(PropertyEditorBase):

    def __init__(
        self,
        toolbox=None,
        parent=None
    ):
        PropertyEditorBase.__init__(
            self,
            toolbox,
            parent
        )

        self.spacing = QtGui.QSpinBox()
        self.spacing.setRange(0, 30)

        self.horizontal_alignment = QtGui.QComboBox()
        self.horizontal_alignment.addItems([
            "Stretch",
            "Left",
            "Center",
            "Right",
        ])

        self.form.addRow(
            "Spacing",
            self.spacing
        )
        self.form.addRow(
            "Child Alignment",
            self.horizontal_alignment
        )

        note = QtGui.QLabel(
            "Column is a vertical layout container. It can contain controls, "
            "Rows and other Columns. Put Columns inside a Row to build "
            "side-by-side groups with controls stacked underneath each other."
        )
        note.setObjectName("HintText")
        note.setWordWrap(True)
        self.root_layout.addWidget(note)
        self.add_stretch()

        self.spacing.valueChanged.connect(
            self._control_changed
        )
        self.horizontal_alignment.currentIndexChanged.connect(
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
            item.get(
                "horizontal_alignment",
                "stretch"
            ),
            0
        ))

    def write_specific(self, item):
        item["spacing"] = int(
            self.spacing.value()
        )
        item["horizontal_alignment"] = (
            "left"
            if self.horizontal_alignment.currentIndex() == 1
            else "center"
            if self.horizontal_alignment.currentIndex() == 2
            else "right"
            if self.horizontal_alignment.currentIndex() == 3
            else "stretch"
        )


__all__ = [
    "ColumnPropertyEditor",
]
