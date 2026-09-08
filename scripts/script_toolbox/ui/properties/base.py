# -*- coding: utf-8 -*-
from __future__ import print_function

from ...compat import QtCore
from ...compat import QtGui
from ...model.items import sanitize_name
from ...pycompat import text_type
from .bindings import BindingPanel


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
        self.row_equal_widths = False
        self.column_context = False

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

        # Immediate-parent Row layout --------------------------------------
        self.row_group = QtGui.QGroupBox("Row Item Layout")
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

        row_form.addRow("Item Width", self.row_width_mode)
        row_form.addRow("Fixed Width", self.row_width)
        row_form.addRow("Stretch Weight", self.row_stretch)

        self.row_equal_widths_note = QtGui.QLabel(
            "Width is controlled by the parent Row because Equal Widths "
            "is enabled."
        )
        self.row_equal_widths_note.setObjectName("HintText")
        self.row_equal_widths_note.setWordWrap(True)
        row_form.addRow(
            "",
            self.row_equal_widths_note
        )

        self.root_layout.addWidget(self.row_group)
        self.row_group.setVisible(False)
        self.row_equal_widths_note.setVisible(False)

        # Immediate-parent Column layout -----------------------------------
        self.column_group = QtGui.QGroupBox("Column Item Layout")
        column_form = QtGui.QFormLayout(self.column_group)
        column_form.setContentsMargins(7, 7, 7, 7)
        column_form.setHorizontalSpacing(8)
        column_form.setVerticalSpacing(5)
        try:
            column_form.setFieldGrowthPolicy(
                QtGui.QFormLayout.AllNonFixedFieldsGrow
            )
        except Exception:
            pass

        self.column_height_mode = QtGui.QComboBox()
        self.column_height_mode.addItems([
            "Auto",
            "Stretch",
            "Fixed",
        ])
        self.column_height = QtGui.QSpinBox()
        self.column_height.setRange(8, 2000)
        self.column_stretch = QtGui.QSpinBox()
        self.column_stretch.setRange(1, 100)

        column_form.addRow(
            "Item Height",
            self.column_height_mode
        )
        column_form.addRow(
            "Fixed Height",
            self.column_height
        )
        column_form.addRow(
            "Stretch Weight",
            self.column_stretch
        )

        self.root_layout.addWidget(
            self.column_group
        )
        self.column_group.setVisible(False)

        self.binding_panel = BindingPanel(
            toolbox=self.toolbox,
            parent=self
        )
        self.root_layout.addWidget(
            self.binding_panel
        )

        self.name_edit.textEdited.connect(self._control_changed)
        self.label_edit.textEdited.connect(self._control_changed)
        self.show_label_check.toggled.connect(self._control_changed)
        self.tooltip_edit.textEdited.connect(self._control_changed)
        self.row_width_mode.currentIndexChanged.connect(
            self._row_layout_changed
        )
        self.row_width.valueChanged.connect(self._control_changed)
        self.row_stretch.valueChanged.connect(self._control_changed)
        self.column_height_mode.currentIndexChanged.connect(
            self._column_layout_changed
        )
        self.column_height.valueChanged.connect(
            self._control_changed
        )
        self.column_stretch.valueChanged.connect(
            self._control_changed
        )
        self.binding_panel.changed.connect(
            self._control_changed
        )

    def set_row_context(
        self,
        enabled,
        equal_widths=False
    ):
        self.row_context = bool(enabled)
        self.row_equal_widths = bool(
            enabled and equal_widths
        )
        self.row_group.setVisible(
            self.row_context
        )
        self._refresh_row_layout_controls()

    def set_column_context(self, enabled):
        self.column_context = bool(enabled)
        self.column_group.setVisible(
            self.column_context
        )
        self._refresh_column_layout_controls()

    def set_parent_layout_context(
        self,
        parent_kind,
        parent_item=None
    ):
        parent_kind = text_type(
            parent_kind or ""
        ).lower()
        parent_item = parent_item or {}

        self.set_row_context(
            parent_kind == "row",
            equal_widths=bool(
                parent_item.get(
                    "equal_widths",
                    False
                )
            )
        )
        self.set_column_context(
            parent_kind == "column"
        )

    def _refresh_row_layout_controls(self):
        mode = (
            "fixed"
            if self.row_width_mode.currentIndex() == 2
            else "stretch"
            if self.row_width_mode.currentIndex() == 1
            else "auto"
        )
        editable = (
            self.row_context and
            not self.row_equal_widths
        )
        self.row_width_mode.setEnabled(editable)
        self.row_width.setEnabled(
            editable and mode == "fixed"
        )
        self.row_stretch.setEnabled(
            editable and mode == "stretch"
        )
        self.row_equal_widths_note.setVisible(
            self.row_context and
            self.row_equal_widths
        )

    def _refresh_column_layout_controls(self):
        mode = (
            "fixed"
            if self.column_height_mode.currentIndex() == 2
            else "stretch"
            if self.column_height_mode.currentIndex() == 1
            else "auto"
        )
        self.column_height.setEnabled(
            self.column_context and
            mode == "fixed"
        )
        self.column_stretch.setEnabled(
            self.column_context and
            mode == "stretch"
        )
        self.column_height_mode.setEnabled(
            self.column_context
        )

    def _row_layout_changed(self, *args):
        self._refresh_row_layout_controls()
        self._control_changed()

    def _column_layout_changed(self, *args):
        self._refresh_column_layout_controls()
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
                    item.get(
                        "label",
                        item.get("name", "")
                    )
                )
            )
            self.show_label_check.setChecked(
                bool(
                    item.get(
                        "show_label",
                        True
                    )
                )
            )
            self.tooltip_edit.setText(
                text_type(
                    item.get("tooltip", "")
                )
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
                int(
                    item.get(
                        "row_width",
                        120
                    )
                )
            )
            self.row_stretch.setValue(
                int(
                    item.get(
                        "row_stretch",
                        1
                    )
                )
            )

            height_mode = item.get(
                "column_height_mode",
                "auto"
            )
            self.column_height_mode.setCurrentIndex({
                "auto": 0,
                "stretch": 1,
                "fixed": 2,
            }.get(height_mode, 0))
            self.column_height.setValue(
                int(
                    item.get(
                        "column_height",
                        28
                    )
                )
            )
            self.column_stretch.setValue(
                int(
                    item.get(
                        "column_stretch",
                        1
                    )
                )
            )

            self.binding_panel.load(item)
            self.load_specific(item)
        finally:
            self.loading = False
            self._refresh_row_layout_controls()
            self._refresh_column_layout_controls()

    def refresh_binding_panel(self):
        if self.item is None:
            return
        previous = self.loading
        self.loading = True
        try:
            self.binding_panel.load(self.item)
        finally:
            self.loading = previous

    def load_specific(self, item):
        pass

    def write_specific(self, item):
        pass

    def write_to_item(self):
        if self.item is None:
            return

        kind = self.item.get(
            "kind",
            "item"
        )
        self.item["name"] = sanitize_name(
            text_type(
                self.name_edit.text()
            ),
            kind
        )

        label = text_type(
            self.label_edit.text()
        ).strip()

        self.item["label"] = (
            label or
            self.item["name"]
        )
        self.item["show_label"] = bool(
            self.show_label_check.isChecked()
        )
        self.item["tooltip"] = text_type(
            self.tooltip_edit.text()
        )

        if (
            self.row_context and
            not self.row_equal_widths
        ):
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

        if self.column_context:
            self.item["column_height_mode"] = (
                "fixed"
                if self.column_height_mode.currentIndex() == 2
                else "stretch"
                if self.column_height_mode.currentIndex() == 1
                else "auto"
            )
            self.item["column_height"] = int(
                self.column_height.value()
            )
            self.item["column_stretch"] = int(
                self.column_stretch.value()
            )

        self.write_specific(
            self.item
        )
        self.binding_panel.write_to_item(
            self.item
        )

    def _control_changed(self, *args):
        if self.loading:
            return

        self.write_to_item()
        self.changed.emit()


class ValuePropertyEditorBase(PropertyEditorBase):

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


class EmptyPropertyEditor(QtGui.QWidget):

    def __init__(
        self,
        toolbox=None,
        parent=None
    ):
        QtGui.QWidget.__init__(
            self,
            parent
        )
        self.setObjectName(
            "PropertyEditor"
        )
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
            self.setPalette(
                editor_palette
            )
            self.setAutoFillBackground(
                True
            )
        except Exception:
            pass

        layout = QtGui.QVBoxLayout(
            self
        )
        layout.addStretch(1)

        label = QtGui.QLabel(
            "Select a parameter to edit its properties."
        )
        label.setObjectName(
            "HintText"
        )
        label.setAlignment(
            QtCore.Qt.AlignCenter
        )

        layout.addWidget(label)
        layout.addStretch(1)

    def bind(self, item):
        pass


__all__ = [
    "EmptyPropertyEditor",
    "PropertyEditorBase",
    "ValuePropertyEditorBase",
]
