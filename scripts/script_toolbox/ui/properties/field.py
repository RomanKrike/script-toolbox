# -*- coding: utf-8 -*-
from __future__ import print_function

from ...compat import HOST
from ...compat import QtGui
from ...pycompat import text_type
from .base import PropertyEditorBase


class FieldPropertyEditor(PropertyEditorBase):

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

        self.source = QtGui.QComboBox()
        self.source.addItems([
            "Value",
            "Selection"
        ])

        self.value = QtGui.QLineEdit()
        self.placeholder = QtGui.QLineEdit()
        self.selectable = QtGui.QCheckBox(
            "Selectable text"
        )
        self.select_scene = QtGui.QCheckBox(
            "Select {0} on double-click".format(
                HOST.selection_noun
            )
        )
        self.multiple = QtGui.QCheckBox(
            "Allow multiple selected items"
        )
        self.long_names = QtGui.QCheckBox(
            "Use full paths / names"
        )

        self.form.addRow("Source", self.source)
        self.form.addRow("Value", self.value)
        self.form.addRow("Placeholder", self.placeholder)
        self.form.addRow("", self.selectable)
        self.form.addRow("", self.select_scene)
        self.form.addRow("", self.multiple)
        self.form.addRow("", self.long_names)
        self.add_stretch()

        self.source.currentIndexChanged.connect(
            self._source_changed
        )
        self.value.textEdited.connect(
            self._control_changed
        )
        self.placeholder.textEdited.connect(
            self._control_changed
        )
        self.selectable.toggled.connect(
            self._control_changed
        )
        self.select_scene.toggled.connect(
            self._control_changed
        )
        self.multiple.toggled.connect(
            self._control_changed
        )
        self.long_names.toggled.connect(
            self._control_changed
        )

    def _source_changed(
        self,
        *args
    ):
        self.value.setEnabled(
            self.source.currentIndex() == 0
        )
        self._control_changed()

    def load_specific(
        self,
        item
    ):
        source = item.get(
            "source",
            "value"
        )

        self.source.setCurrentIndex(
            1
            if source == "selection"
            else 0
        )

        value = item.get(
            "value",
            ""
        )

        if isinstance(
            value,
            (list, tuple)
        ):
            value = ", ".join(
                text_type(entry)
                for entry in value
            )

        self.value.setText(
            text_type(
                value
            )
        )
        self.placeholder.setText(
            text_type(
                item.get(
                    "placeholder",
                    ""
                )
            )
        )
        self.selectable.setChecked(
            bool(
                item.get(
                    "selectable",
                    True
                )
            )
        )
        self.select_scene.setChecked(
            bool(
                item.get(
                    "select_scene",
                    False
                )
            )
        )
        self.multiple.setChecked(
            bool(
                item.get(
                    "multiple",
                    True
                )
            )
        )
        self.long_names.setChecked(
            bool(
                item.get(
                    "long_names",
                    False
                )
            )
        )

        self.value.setEnabled(
            source == "value"
        )

    def write_specific(
        self,
        item
    ):
        source = (
            "selection"
            if self.source.currentIndex() == 1
            else "value"
        )

        item["source"] = source

        if source == "value":
            item["value"] = text_type(
                self.value.text()
            )

        item["placeholder"] = text_type(
            self.placeholder.text()
        )
        item["selectable"] = bool(
            self.selectable.isChecked()
        )
        item["select_scene"] = bool(
            self.select_scene.isChecked()
        )
        item["multiple"] = bool(
            self.multiple.isChecked()
        )
        item["long_names"] = bool(
            self.long_names.isChecked()
        )


__all__ = [
    "FieldPropertyEditor",
]
