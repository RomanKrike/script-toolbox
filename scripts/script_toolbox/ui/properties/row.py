# -*- coding: utf-8 -*-
from __future__ import print_function

from ...compat import QtGui
from .base import PropertyEditorBase


class RowPropertyEditor(PropertyEditorBase):

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
        self.spacing.setRange(
            0,
            30
        )
        self.equal_widths = QtGui.QCheckBox(
            "Give children equal width"
        )
        self.vertical_alignment = QtGui.QComboBox()
        self.vertical_alignment.addItems([
            "Top",
            "Center",
            "Bottom",
        ])

        self.form.addRow(
            "Spacing",
            self.spacing
        )
        self.form.addRow(
            "",
            self.equal_widths
        )
        self.form.addRow(
            "Vertical Alignment",
            self.vertical_alignment
        )

        note = QtGui.QLabel(
            "Row is a horizontal layout container. Select an item inside "
            "the Row to configure Auto / Stretch / Fixed width and alignment."
        )
        note.setObjectName(
            "HintText"
        )
        note.setWordWrap(
            True
        )
        self.root_layout.addWidget(
            note
        )
        self.add_stretch()

        self.spacing.valueChanged.connect(
            self._control_changed
        )
        self.equal_widths.toggled.connect(
            self._control_changed
        )
        self.vertical_alignment.currentIndexChanged.connect(
            self._control_changed
        )

    def load_specific(
        self,
        item
    ):
        self.spacing.setValue(
            int(
                item.get(
                    "spacing",
                    4
                )
            )
        )
        self.equal_widths.setChecked(
            bool(
                item.get(
                    "equal_widths",
                    False
                )
            )
        )
        self.vertical_alignment.setCurrentIndex({
            "top": 0,
            "center": 1,
            "bottom": 2,
        }.get(
            item.get(
                "vertical_alignment",
                "center"
            ),
            1
        ))

    def write_specific(
        self,
        item
    ):
        item["spacing"] = int(
            self.spacing.value()
        )
        item["equal_widths"] = bool(
            self.equal_widths.isChecked()
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
