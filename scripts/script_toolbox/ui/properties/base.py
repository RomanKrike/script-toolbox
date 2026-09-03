# -*- coding: utf-8 -*-
from __future__ import print_function

from ...compat import QtCore
from ...compat import QtGui
from ...model.items import sanitize_name
from ...pycompat import text_type


class PropertyEditorBase(QtGui.QWidget):

    changed = QtCore.Signal()

    def __init__(self, toolbox=None, parent=None):
        QtGui.QWidget.__init__(self, parent)

        self.toolbox = toolbox
        self.item = None
        self.loading = False

        self.root_layout = QtGui.QVBoxLayout(self)
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(8)

        self.form = QtGui.QFormLayout()
        self.form.setHorizontalSpacing(8)
        self.form.setVerticalSpacing(6)
        self.form.setLabelAlignment(
            QtCore.Qt.AlignLeft |
            QtCore.Qt.AlignVCenter
        )
        self.root_layout.addLayout(self.form)

        self.name_edit = QtGui.QLineEdit()
        self.label_edit = QtGui.QLineEdit()
        self.show_label_check = QtGui.QCheckBox("Show Label")
        self.tooltip_edit = QtGui.QLineEdit()

        self.form.addRow("Name", self.name_edit)
        self.form.addRow("Label", self.label_edit)
        self.form.addRow("", self.show_label_check)
        self.form.addRow("Tooltip", self.tooltip_edit)

        self.name_edit.textEdited.connect(self._control_changed)
        self.label_edit.textEdited.connect(self._control_changed)
        self.show_label_check.toggled.connect(self._control_changed)
        self.tooltip_edit.textEdited.connect(self._control_changed)

    def add_stretch(self):
        self.root_layout.addStretch(1)

    def bind(self, item):
        self.item = item
        self.loading = True

        try:
            self.name_edit.setText(
                text_type(item.get("name", ""))
            )
            self.label_edit.setText(
                text_type(
                    item.get("label", item.get("name", ""))
                )
            )
            self.show_label_check.setChecked(
                bool(item.get("show_label", True))
            )
            self.tooltip_edit.setText(
                text_type(item.get("tooltip", ""))
            )
            self.load_specific(item)
        finally:
            self.loading = False

    def load_specific(self, item):
        pass

    def write_specific(self, item):
        pass

    def write_to_item(self):
        if self.item is None:
            return

        kind = self.item.get("kind", "item")
        self.item["name"] = sanitize_name(
            text_type(self.name_edit.text()),
            kind
        )

        label = text_type(
            self.label_edit.text()
        ).strip()

        self.item["label"] = label or self.item["name"]
        self.item["show_label"] = bool(
            self.show_label_check.isChecked()
        )
        self.item["tooltip"] = text_type(
            self.tooltip_edit.text()
        )

        self.write_specific(self.item)

    def _control_changed(self, *args):
        if self.loading:
            return

        self.write_to_item()
        self.changed.emit()


class EmptyPropertyEditor(QtGui.QWidget):

    def __init__(self, toolbox=None, parent=None):
        QtGui.QWidget.__init__(self, parent)

        layout = QtGui.QVBoxLayout(self)
        layout.addStretch(1)

        label = QtGui.QLabel(
            "Select a parameter to edit its properties."
        )
        label.setObjectName("HintText")
        label.setAlignment(QtCore.Qt.AlignCenter)

        layout.addWidget(label)
        layout.addStretch(1)

    def bind(self, item):
        pass


__all__ = [
    "EmptyPropertyEditor",
    "PropertyEditorBase",
]
