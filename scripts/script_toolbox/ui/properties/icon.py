# -*- coding: utf-8 -*-
from __future__ import print_function

from ...compat import QtGui
from ...model.items import clamp
from ...pycompat import text_type
from .base import PropertyEditorBase


class IconPropertyEditor(PropertyEditorBase):

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

        self.path = QtGui.QLineEdit()
        self.width = QtGui.QSpinBox()
        self.height = QtGui.QSpinBox()
        self.alignment = QtGui.QComboBox()

        self.width.setRange(8, 512)
        self.height.setRange(8, 512)
        self.alignment.addItems([
            "Left",
            "Center",
            "Right",
        ])

        self.form.addRow(
            "Path",
            self.path
        )
        self.form.addRow(
            "Width",
            self.width
        )
        self.form.addRow(
            "Height",
            self.height
        )
        self.form.addRow(
            "Content Alignment",
            self.alignment
        )
        self.add_stretch()

        self.path.textEdited.connect(
            self._control_changed
        )
        self.width.valueChanged.connect(
            self._control_changed
        )
        self.height.valueChanged.connect(
            self._control_changed
        )
        self.alignment.currentIndexChanged.connect(
            self._control_changed
        )

    def load_specific(self, item):
        self.path.setText(
            text_type(
                item.get(
                    "path",
                    ""
                )
            )
        )
        self.width.setValue(
            int(
                item.get(
                    "width",
                    24
                )
            )
        )
        self.height.setValue(
            int(
                item.get(
                    "height",
                    24
                )
            )
        )
        content_alignment = item.get(
            "content_alignment",
            item.get(
                "alignment",
                "left"
            )
        )
        self.alignment.setCurrentIndex({
            "left": 0,
            "center": 1,
            "right": 2,
        }.get(
            content_alignment,
            0
        ))

    def write_specific(self, item):
        item["path"] = text_type(
            self.path.text()
        )
        item["width"] = clamp(
            int(
                self.width.value()
            ),
            8,
            512
        )
        item["height"] = clamp(
            int(
                self.height.value()
            ),
            8,
            512
        )
        content_alignment = (
            "right"
            if self.alignment.currentIndex() == 2
            else "center"
            if self.alignment.currentIndex() == 1
            else "left"
        )
        item["content_alignment"] = content_alignment

        # Keep the schema-18 runtime alias synchronized. Older configs and
        # renderers still read ``alignment``.
        item["alignment"] = content_alignment
        item.pop("clickable", None)


__all__ = [
    "IconPropertyEditor",
]
