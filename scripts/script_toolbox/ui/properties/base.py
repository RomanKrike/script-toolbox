# -*- coding: utf-8 -*-
from __future__ import print_function

from ...compat import QtCore
from ...compat import QtGui
from ...model.items import sanitize_name
from ...pycompat import text_type
from ..script_editor import ScriptEditorWidget


class PropertyEditorBase(QtGui.QWidget):

    changed = QtCore.Signal()

    def __init__(self, toolbox=None, parent=None):
        QtGui.QWidget.__init__(self, parent)

        self.setObjectName("PropertyEditor")
        try:
            editor_palette = self.palette()
            editor_palette.setColor(
                QtGui.QPalette.Window,
                QtGui.QColor("#303030")
            )
            editor_palette.setColor(
                QtGui.QPalette.Base,
                QtGui.QColor("#303030")
            )
            self.setPalette(editor_palette)
            self.setAutoFillBackground(True)
        except Exception:
            pass

        self.toolbox = toolbox
        self.item = None
        self.loading = False
        self.row_context = False

        self.root_layout = QtGui.QVBoxLayout(self)
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(8)

        self.form = QtGui.QFormLayout()
        self.form.setHorizontalSpacing(8)
        self.form.setVerticalSpacing(6)
        try:
            self.form.setFieldGrowthPolicy(
                QtGui.QFormLayout.AllNonFixedFieldsGrow
            )
        except Exception:
            pass
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

        # Per-item layout settings are only relevant when this item is a
        # direct child of a Row. Keep the controls hidden everywhere else.
        self.row_group = QtGui.QGroupBox("Row Layout")
        row_form = QtGui.QFormLayout(self.row_group)
        row_form.setContentsMargins(7, 7, 7, 7)
        row_form.setHorizontalSpacing(8)
        row_form.setVerticalSpacing(5)
        try:
            row_form.setFieldGrowthPolicy(
                QtGui.QFormLayout.AllNonFixedFieldsGrow
            )
        except Exception:
            pass

        self.row_width_mode = QtGui.QComboBox()
        self.row_width_mode.addItems([
            "Auto",
            "Stretch",
            "Fixed",
        ])
        self.row_width = QtGui.QSpinBox()
        self.row_width.setRange(20, 2000)
        self.row_stretch = QtGui.QSpinBox()
        self.row_stretch.setRange(1, 100)
        self.row_alignment = QtGui.QComboBox()
        self.row_alignment.addItems([
            "Left",
            "Center",
            "Right",
        ])

        row_form.addRow("Width", self.row_width_mode)
        row_form.addRow("Fixed Width", self.row_width)
        row_form.addRow("Stretch", self.row_stretch)
        row_form.addRow("Alignment", self.row_alignment)
        self.root_layout.addWidget(self.row_group)
        self.row_group.setVisible(False)

        self.name_edit.textEdited.connect(self._control_changed)
        self.label_edit.textEdited.connect(self._control_changed)
        self.show_label_check.toggled.connect(self._control_changed)
        self.tooltip_edit.textEdited.connect(self._control_changed)
        self.row_width_mode.currentIndexChanged.connect(
            self._row_layout_changed
        )
        self.row_width.valueChanged.connect(self._control_changed)
        self.row_stretch.valueChanged.connect(self._control_changed)
        self.row_alignment.currentIndexChanged.connect(
            self._control_changed
        )

    def set_row_context(self, enabled):
        self.row_context = bool(enabled)
        self.row_group.setVisible(
            self.row_context
        )
        self._refresh_row_layout_controls()

    def _refresh_row_layout_controls(self):
        mode = (
            "fixed"
            if self.row_width_mode.currentIndex() == 2
            else "stretch"
            if self.row_width_mode.currentIndex() == 1
            else "auto"
        )
        self.row_width.setEnabled(
            self.row_context and mode == "fixed"
        )
        self.row_stretch.setEnabled(
            self.row_context and mode == "stretch"
        )

    def _row_layout_changed(self, *args):
        self._refresh_row_layout_controls()
        self._control_changed()

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

            width_mode = item.get(
                "row_width_mode",
                "auto"
            )
            self.row_width_mode.setCurrentIndex({
                "auto": 0,
                "stretch": 1,
                "fixed": 2,
            }.get(width_mode, 0))
            self.row_width.setValue(
                int(item.get("row_width", 120))
            )
            self.row_stretch.setValue(
                int(item.get("row_stretch", 1))
            )
            self.row_alignment.setCurrentIndex({
                "left": 0,
                "center": 1,
                "right": 2,
            }.get(item.get("row_alignment", "left"), 0))

            self.load_specific(item)
        finally:
            self.loading = False
            self._refresh_row_layout_controls()

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

        if self.row_context:
            self.item["row_width_mode"] = (
                "fixed"
                if self.row_width_mode.currentIndex() == 2
                else "stretch"
                if self.row_width_mode.currentIndex() == 1
                else "auto"
            )
            self.item["row_width"] = int(
                self.row_width.value()
            )
            self.item["row_stretch"] = int(
                self.row_stretch.value()
            )
            self.item["row_alignment"] = (
                "right"
                if self.row_alignment.currentIndex() == 2
                else "center"
                if self.row_alignment.currentIndex() == 1
                else "left"
            )

        self.write_specific(self.item)

    def _control_changed(self, *args):
        if self.loading:
            return

        self.write_to_item()
        self.changed.emit()


class ValuePropertyEditorBase(PropertyEditorBase):
    """Base editor for values that can run a Python On Change script."""

    def __init__(self, toolbox=None, parent=None):
        PropertyEditorBase.__init__(self, toolbox, parent)

        self.on_change_group = QtGui.QGroupBox("On Change")
        group_layout = QtGui.QVBoxLayout(self.on_change_group)
        group_layout.setContentsMargins(6, 6, 6, 6)
        group_layout.setSpacing(4)

        note = QtGui.QLabel(
            "Python namespace: value, old_value, toolbox, host."
        )
        note.setObjectName("HintText")
        note.setWordWrap(True)
        group_layout.addWidget(note)

        self.on_change_editor = ScriptEditorWidget(
            language="python",
            toolbox=self.toolbox
        )
        self.on_change_editor.setMinimumHeight(105)
        try:
            self.on_change_editor.run_button.setEnabled(False)
            self.on_change_editor.run_button.setToolTip(
                "Runs automatically when the value changes"
            )
        except Exception:
            pass
        group_layout.addWidget(
            self.on_change_editor,
            1
        )

        self.root_layout.addWidget(
            self.on_change_group
        )
        self.on_change_editor.textChanged.connect(
            self._control_changed
        )

    def load_value_behavior(self, item):
        self.on_change_editor.setPlainText(
            text_type(
                item.get(
                    "on_change_script",
                    ""
                )
            )
        )
        self.on_change_editor.set_language(
            "python"
        )

    def write_value_behavior(self, item):
        item["on_change_script"] = text_type(
            self.on_change_editor.toPlainText()
        )

    def bind(self, item):
        self.loading = True
        try:
            PropertyEditorBase.bind(self, item)
        finally:
            self.loading = True
            try:
                self.load_value_behavior(item)
            finally:
                self.loading = False

    def write_to_item(self):
        PropertyEditorBase.write_to_item(self)
        if self.item is not None:
            self.write_value_behavior(
                self.item
            )


class EmptyPropertyEditor(QtGui.QWidget):

    def __init__(self, toolbox=None, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setObjectName("PropertyEditor")
        try:
            editor_palette = self.palette()
            editor_palette.setColor(
                QtGui.QPalette.Window,
                QtGui.QColor("#303030")
            )
            editor_palette.setColor(
                QtGui.QPalette.Base,
                QtGui.QColor("#303030")
            )
            self.setPalette(editor_palette)
            self.setAutoFillBackground(True)
        except Exception:
            pass

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
    "ValuePropertyEditorBase",
]
