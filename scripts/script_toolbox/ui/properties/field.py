# -*- coding: utf-8 -*-
from __future__ import print_function

from ...compat import QtGui
from ...pycompat import text_type
from .base import ValuePropertyEditorBase


class FieldPropertyEditor(ValuePropertyEditorBase):

    def __init__(self, toolbox=None, parent=None):
        ValuePropertyEditorBase.__init__(self, toolbox, parent)

        self.source = QtGui.QComboBox()
        self.source.addItems([
            "Value",
            "Selection"
        ])

        self.value = QtGui.QPlainTextEdit()
        self.value.setMinimumHeight(64)
        self.value.setMaximumHeight(92)
        self.placeholder = QtGui.QLineEdit()
        self.display_mode = QtGui.QComboBox()
        self.display_mode.addItems([
            "Single Line",
            "List",
        ])
        self.visible_rows = QtGui.QSpinBox()
        self.visible_rows.setRange(1, 20)
        self.selectable = QtGui.QCheckBox()
        self.select_scene = QtGui.QCheckBox()
        self.multiple = QtGui.QCheckBox()
        self.long_names = QtGui.QCheckBox()

        self.content_section.addRow("Source", self.source)
        self.content_section.addRow("Display", self.display_mode)
        self.content_section.addRow("Value", self.value)
        self.content_section.addRow("Placeholder", self.placeholder)
        self.content_section.addRow("Multiple", self.multiple)
        self.content_section.addRow(
            "Visible Rows",
            self.visible_rows
        )

        self.behavior_section.addRow("Selectable", self.selectable)
        self.behavior_section.addRow(
            "Select Scene on Double Click",
            self.select_scene
        )
        self.behavior_section.addRow("Use Full Paths", self.long_names)
        self.add_stretch()

        self.source.currentIndexChanged.connect(
            self._source_changed
        )
        self.value.textChanged.connect(self._control_changed)
        self.placeholder.textEdited.connect(self._control_changed)
        self.display_mode.currentIndexChanged.connect(
            self._display_changed
        )
        self.visible_rows.valueChanged.connect(
            self._control_changed
        )
        self.selectable.toggled.connect(
            self._control_changed
        )
        self.select_scene.toggled.connect(
            self._control_changed
        )
        self.multiple.toggled.connect(
            self._multiple_changed
        )
        self.long_names.toggled.connect(
            self._control_changed
        )

    def _source_changed(self, *args):
        self._refresh_enabled_state()
        self._control_changed()

    def _display_changed(self, *args):
        self._refresh_enabled_state()
        self._control_changed()

    def _multiple_changed(self, *args):
        if not self.multiple.isChecked():
            self.display_mode.setCurrentIndex(0)
        self._refresh_enabled_state()
        self._control_changed()

    def _refresh_enabled_state(self):
        source_value = self.source.currentIndex() == 0
        multiple = self.multiple.isChecked()
        list_mode = self.display_mode.currentIndex() == 1

        self.set_property_available(
            self.value,
            source_value,
            "Value is provided by the current DCC selection when Source is Selection."
        )
        self.set_property_available(
            self.display_mode,
            multiple,
            "Display mode is fixed to Single Line when Multiple is disabled."
        )
        self.set_property_available(
            self.visible_rows,
            multiple and list_mode,
            "Visible Rows applies only to List display with Multiple enabled."
        )

    def _parse_value(self):
        raw = text_type(self.value.toPlainText())
        if not self.multiple.isChecked():
            return raw.strip()

        return [
            line.strip()
            for line in raw.replace(";", "\n").replace(",", "\n").splitlines()
            if line.strip()
        ]

    def load_specific(self, item):
        source = item.get("source", "value")
        self.source.setCurrentIndex(
            1 if source == "selection" else 0
        )

        value = item.get("value", "")
        if isinstance(value, (list, tuple)):
            value = "\n".join(
                text_type(entry)
                for entry in value
            )

        self.value.setPlainText(text_type(value))
        self.placeholder.setText(
            text_type(item.get("placeholder", ""))
        )
        self.multiple.setChecked(
            bool(item.get("multiple", True))
        )
        self.display_mode.setCurrentIndex(
            1
            if item.get(
                "display_mode",
                "list" if self.multiple.isChecked() else "single"
            ) == "list" and self.multiple.isChecked()
            else 0
        )
        self.visible_rows.setValue(
            int(item.get("visible_rows", 4))
        )
        self.selectable.setChecked(
            bool(item.get("selectable", True))
        )
        self.select_scene.setChecked(
            bool(item.get("select_scene", False))
        )
        self.long_names.setChecked(
            bool(item.get("long_names", False))
        )

        self._refresh_enabled_state()

    def write_specific(self, item):
        source = (
            "selection"
            if self.source.currentIndex() == 1
            else "value"
        )

        item["source"] = source
        item["multiple"] = bool(
            self.multiple.isChecked()
        )

        if source == "value":
            item["value"] = self._parse_value()

        item["placeholder"] = text_type(
            self.placeholder.text()
        )
        item["display_mode"] = (
            "list"
            if self.display_mode.currentIndex() == 1 and item["multiple"]
            else "single"
        )
        item["visible_rows"] = int(
            self.visible_rows.value()
        )
        item["selectable"] = bool(
            self.selectable.isChecked()
        )
        item["select_scene"] = bool(
            self.select_scene.isChecked()
        )
        item["long_names"] = bool(
            self.long_names.isChecked()
        )


__all__ = [
    "FieldPropertyEditor",
]
