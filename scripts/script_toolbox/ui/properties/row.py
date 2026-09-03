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

        self.form.addRow(
            "Spacing",
            self.spacing
        )

        note = QtGui.QLabel(
            "Row is a horizontal layout container. "
            "Folders and nested Rows are not allowed inside it."
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

    def write_specific(
        self,
        item
    ):
        item["spacing"] = int(
            self.spacing.value()
        )


__all__ = [
    "RowPropertyEditor",
]
