# -*- coding: utf-8 -*-
from __future__ import print_function

from ...compat import QtGui
from ...model.items import clamp
from ...model.items import safe_color
from ...pycompat import text_type
from ..icon_browse import install_icon_browse
from .base import PropertyEditorBase


class ButtonPropertyEditor(PropertyEditorBase):
    """Property editor for the action-only Button item."""

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

        self.color = [0.25, 0.25, 0.25]
        self.icon_path = QtGui.QLineEdit()
        self.icon_size = QtGui.QSpinBox()
        self.icon_size.setRange(8, 256)
        self.icon_only = QtGui.QCheckBox()
        self.color_button = QtGui.QPushButton("Choose...")

        section = self.appearance_section
        section.addRow("Icon", self.icon_path)
        section.addRow("Icon Size", self.icon_size)
        section.addRow("Icon Only", self.icon_only)
        self.icon_browse_button = install_icon_browse(
            self,
            self.icon_path,
            form=section.form
        )
        section.addRow("Color", self.color_button)

        self.icon_path.textEdited.connect(self._control_changed)
        self.icon_size.valueChanged.connect(self._control_changed)
        self.icon_only.toggled.connect(self._control_changed)
        self.color_button.clicked.connect(self.choose_color)

    def load_specific(self, item):
        self.icon_path.setText(
            text_type(item.get("icon_path", ""))
        )
        self.icon_size.setValue(
            int(item.get("icon_size", 18))
        )
        self.icon_only.setChecked(
            bool(item.get("icon_only", False))
        )
        self.color = safe_color(item.get("color"))
        self._refresh_color()

    def _button_color_style(self, color):
        rgb = [
            int(value * 255)
            for value in safe_color(color)
        ]
        return (
            "QPushButton { background-color: rgb(%d,%d,%d); }" %
            (rgb[0], rgb[1], rgb[2])
        )

    def _refresh_color(self):
        self.color_button.setStyleSheet(
            self._button_color_style(self.color)
        )

    def choose_color(self):
        current = self.color
        initial = QtGui.QColor(
            int(current[0] * 255),
            int(current[1] * 255),
            int(current[2] * 255)
        )
        chosen = QtGui.QColorDialog.getColor(
            initial,
            self,
            "Choose Button Color"
        )

        if not chosen.isValid():
            return

        self.color = [
            chosen.red() / 255.0,
            chosen.green() / 255.0,
            chosen.blue() / 255.0
        ]
        self._refresh_color()
        self._control_changed()

    def write_specific(self, item):
        item["color"] = safe_color(self.color)
        item["icon_path"] = text_type(self.icon_path.text())
        item["icon_size"] = clamp(
            int(self.icon_size.value()),
            8,
            256
        )
        item["icon_only"] = bool(self.icon_only.isChecked())


__all__ = [
    "ButtonPropertyEditor",
]
