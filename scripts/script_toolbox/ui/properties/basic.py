# -*- coding: utf-8 -*-
from __future__ import print_function

from ...compat import QtGui
from ...model.items import clamp
from ...model.items import safe_color
from ...model.items import safe_component_labels
from ...model.items import safe_menu_items
from ...model.items import safe_numeric_size
from ...pycompat import text_type
from .base import PropertyEditorBase
from .base import ValuePropertyEditorBase


def _value_list(value, size, fallback):
    if isinstance(value, (list, tuple)):
        values = list(value)
    else:
        values = [value] * size

    while len(values) < size:
        values.append(fallback)

    return values[:size]


class StringPropertyEditor(ValuePropertyEditorBase):

    def __init__(self, toolbox=None, parent=None):
        ValuePropertyEditorBase.__init__(self, toolbox, parent)
        self.value = QtGui.QLineEdit()
        self.form.addRow("Value", self.value)
        self.add_stretch()
        self.value.textEdited.connect(self._control_changed)

    def load_specific(self, item):
        self.value.setText(text_type(item.get("value", "")))

    def write_specific(self, item):
        item["value"] = text_type(self.value.text())


class IntegerPropertyEditor(ValuePropertyEditorBase):

    def __init__(self, toolbox=None, parent=None):
        ValuePropertyEditorBase.__init__(self, toolbox, parent)

        self.size = QtGui.QComboBox()
        self.size.addItems(["1", "2", "3", "4"])
        self.values_widget = QtGui.QWidget()
        values_layout = QtGui.QHBoxLayout(self.values_widget)
        values_layout.setContentsMargins(0, 0, 0, 0)
        values_layout.setSpacing(4)
        self.values = []
        for index in range(4):
            widget = QtGui.QSpinBox()
            widget.setRange(-1000000, 1000000)
            self.values.append(widget)
            values_layout.addWidget(widget, 1)

        self.component_labels = QtGui.QLineEdit()
        try:
            self.component_labels.setPlaceholderText("X, Y, Z, W")
        except Exception:
            pass
        self.show_slider = QtGui.QCheckBox("Show Slider")
        self.minimum = QtGui.QSpinBox()
        self.maximum = QtGui.QSpinBox()
        self.step = QtGui.QSpinBox()

        for widget in (
            self.minimum,
            self.maximum
        ):
            widget.setRange(-1000000, 1000000)

        self.step.setRange(1, 1000000)

        self.form.addRow("Size", self.size)
        self.form.addRow("Value", self.values_widget)
        self.form.addRow("Component Labels", self.component_labels)
        self.form.addRow("", self.show_slider)
        self.form.addRow("Minimum", self.minimum)
        self.form.addRow("Maximum", self.maximum)
        self.form.addRow("Step", self.step)
        self.add_stretch()

        self.size.currentIndexChanged.connect(self._size_changed)
        for widget in self.values:
            widget.valueChanged.connect(self._control_changed)
        self.component_labels.textEdited.connect(self._control_changed)
        self.show_slider.toggled.connect(self._control_changed)
        self.minimum.valueChanged.connect(self._control_changed)
        self.maximum.valueChanged.connect(self._control_changed)
        self.step.valueChanged.connect(self._control_changed)

    def current_size(self):
        return self.size.currentIndex() + 1

    def _size_changed(self, *args):
        self._refresh_size()
        self._control_changed()

    def _refresh_size(self):
        size = self.current_size()
        for index, widget in enumerate(self.values):
            widget.setVisible(index < size)
        self.component_labels.setEnabled(size > 1)

    def load_specific(self, item):
        size = safe_numeric_size(item.get("size", 1))
        self.minimum.setValue(int(item.get("min", -1000000)))
        self.maximum.setValue(int(item.get("max", 1000000)))
        self.step.setValue(max(1, int(item.get("step", 1))))
        self.size.setCurrentIndex(size - 1)
        values = _value_list(item.get("value", 0), size, 0)
        for index, widget in enumerate(self.values):
            widget.setValue(
                int(values[index]) if index < size else 0
            )
        self.component_labels.setText(
            ", ".join(
                safe_component_labels(
                    item.get("component_labels"),
                    size
                )
            )
        )
        self.show_slider.setChecked(
            bool(item.get("show_slider", False))
        )
        self._refresh_size()

    def write_specific(self, item):
        minimum = int(self.minimum.value())
        maximum = int(self.maximum.value())

        if minimum > maximum:
            minimum, maximum = maximum, minimum

        size = self.current_size()
        values = [
            clamp(
                int(self.values[index].value()),
                minimum,
                maximum
            )
            for index in range(size)
        ]

        item["min"] = minimum
        item["max"] = maximum
        item["step"] = max(1, int(self.step.value()))
        item["size"] = size
        item["component_labels"] = safe_component_labels(
            text_type(self.component_labels.text()),
            size
        )
        item["show_slider"] = bool(
            self.show_slider.isChecked()
        )
        item["value"] = values[0] if size == 1 else values


class FloatPropertyEditor(ValuePropertyEditorBase):

    def __init__(self, toolbox=None, parent=None):
        ValuePropertyEditorBase.__init__(self, toolbox, parent)

        self.size = QtGui.QComboBox()
        self.size.addItems(["1", "2", "3", "4"])
        self.values_widget = QtGui.QWidget()
        values_layout = QtGui.QHBoxLayout(self.values_widget)
        values_layout.setContentsMargins(0, 0, 0, 0)
        values_layout.setSpacing(4)
        self.values = []
        for index in range(4):
            widget = QtGui.QDoubleSpinBox()
            widget.setRange(-1000000.0, 1000000.0)
            widget.setDecimals(6)
            self.values.append(widget)
            values_layout.addWidget(widget, 1)

        self.component_labels = QtGui.QLineEdit()
        try:
            self.component_labels.setPlaceholderText("X, Y, Z, W")
        except Exception:
            pass
        self.show_slider = QtGui.QCheckBox("Show Slider")
        self.minimum = QtGui.QDoubleSpinBox()
        self.maximum = QtGui.QDoubleSpinBox()
        self.step = QtGui.QDoubleSpinBox()
        self.decimals = QtGui.QSpinBox()

        for widget in (
            self.minimum,
            self.maximum
        ):
            widget.setRange(-1000000.0, 1000000.0)
            widget.setDecimals(6)

        self.step.setRange(0.000001, 1000000.0)
        self.step.setDecimals(6)
        self.decimals.setRange(0, 8)

        self.form.addRow("Size", self.size)
        self.form.addRow("Value", self.values_widget)
        self.form.addRow("Component Labels", self.component_labels)
        self.form.addRow("", self.show_slider)
        self.form.addRow("Minimum", self.minimum)
        self.form.addRow("Maximum", self.maximum)
        self.form.addRow("Step", self.step)
        self.form.addRow("Decimals", self.decimals)
        self.add_stretch()

        self.size.currentIndexChanged.connect(self._size_changed)
        for widget in self.values:
            widget.valueChanged.connect(self._control_changed)
        self.component_labels.textEdited.connect(self._control_changed)
        self.show_slider.toggled.connect(self._control_changed)
        self.minimum.valueChanged.connect(self._control_changed)
        self.maximum.valueChanged.connect(self._control_changed)
        self.step.valueChanged.connect(self._control_changed)
        self.decimals.valueChanged.connect(self._decimals_changed)

    def current_size(self):
        return self.size.currentIndex() + 1

    def _size_changed(self, *args):
        self._refresh_size()
        self._control_changed()

    def _decimals_changed(self, *args):
        self._refresh_decimals()
        self._control_changed()

    def _refresh_size(self):
        size = self.current_size()
        for index, widget in enumerate(self.values):
            widget.setVisible(index < size)
        self.component_labels.setEnabled(size > 1)

    def _refresh_decimals(self):
        decimals = int(self.decimals.value())
        for widget in self.values + [
            self.minimum,
            self.maximum,
            self.step,
        ]:
            widget.setDecimals(decimals)

    def load_specific(self, item):
        decimals = int(item.get("decimals", 3))
        size = safe_numeric_size(item.get("size", 1))
        self.decimals.setValue(decimals)
        self._refresh_decimals()
        self.minimum.setValue(float(item.get("min", -1000000.0)))
        self.maximum.setValue(float(item.get("max", 1000000.0)))
        self.step.setValue(max(0.000001, float(item.get("step", 0.1))))
        self.size.setCurrentIndex(size - 1)
        values = _value_list(item.get("value", 0.0), size, 0.0)
        for index, widget in enumerate(self.values):
            widget.setValue(
                float(values[index]) if index < size else 0.0
            )
        self.component_labels.setText(
            ", ".join(
                safe_component_labels(
                    item.get("component_labels"),
                    size
                )
            )
        )
        self.show_slider.setChecked(
            bool(item.get("show_slider", False))
        )
        self._refresh_size()

    def write_specific(self, item):
        decimals = int(self.decimals.value())
        self._refresh_decimals()
        minimum = float(self.minimum.value())
        maximum = float(self.maximum.value())

        if minimum > maximum:
            minimum, maximum = maximum, minimum

        size = self.current_size()
        values = [
            clamp(
                float(self.values[index].value()),
                minimum,
                maximum
            )
            for index in range(size)
        ]

        item["min"] = minimum
        item["max"] = maximum
        item["step"] = max(
            0.000001,
            float(self.step.value())
        )
        item["decimals"] = decimals
        item["size"] = size
        item["component_labels"] = safe_component_labels(
            text_type(self.component_labels.text()),
            size
        )
        item["show_slider"] = bool(
            self.show_slider.isChecked()
        )
        item["value"] = values[0] if size == 1 else values


class CheckboxPropertyEditor(ValuePropertyEditorBase):

    def __init__(self, toolbox=None, parent=None):
        ValuePropertyEditorBase.__init__(self, toolbox, parent)

        self.position = QtGui.QComboBox()
        self.position.addItems([
            "Right",
            "Left"
        ])

        self.value = QtGui.QCheckBox(
            "Checked"
        )

        self.form.addRow(
            "Label Position",
            self.position
        )
        self.form.addRow(
            "Value",
            self.value
        )
        self.add_stretch()

        self.position.currentIndexChanged.connect(
            self._control_changed
        )
        self.value.toggled.connect(
            self._control_changed
        )

    def load_specific(self, item):
        self.position.setCurrentIndex(
            1
            if item.get(
                "label_position",
                "right"
            ) == "left"
            else 0
        )
        self.value.setChecked(
            bool(
                item.get(
                    "value",
                    False
                )
            )
        )

    def write_specific(self, item):
        item["label_position"] = (
            "left"
            if self.position.currentIndex() == 1
            else "right"
        )
        item["value"] = bool(
            self.value.isChecked()
        )


class MenuPropertyEditor(ValuePropertyEditorBase):

    def __init__(self, toolbox=None, parent=None):
        ValuePropertyEditorBase.__init__(self, toolbox, parent)

        self.items_edit = QtGui.QPlainTextEdit()
        self.items_edit.setMinimumHeight(110)
        self.value = QtGui.QComboBox()

        self.form.addRow("Items", self.items_edit)
        self.form.addRow("Value", self.value)
        self.add_stretch()

        self.items_edit.textChanged.connect(self._items_changed)
        self.value.currentIndexChanged.connect(self._control_changed)

    def load_specific(self, item):
        self.items_edit.setPlainText(
            "\n".join(item.get("items", []))
        )
        self._rebuild_values(item.get("value", ""))

    def _parsed_items(self):
        return safe_menu_items(
            text_type(self.items_edit.toPlainText())
        )

    def _rebuild_values(self, selected=None):
        values = self._parsed_items()
        if selected not in values:
            selected = values[0]

        self.value.blockSignals(True)
        try:
            self.value.clear()
            self.value.addItems(values)
            index = self.value.findText(selected)
            if index >= 0:
                self.value.setCurrentIndex(index)
        finally:
            self.value.blockSignals(False)

    def _items_changed(self):
        if self.loading:
            return
        current = text_type(self.value.currentText())
        self._rebuild_values(current)
        self._control_changed()

    def write_specific(self, item):
        values = self._parsed_items()
        selected = text_type(self.value.currentText())
        if selected not in values:
            selected = values[0]
        item["items"] = values
        item["value"] = selected


class ColorPropertyEditor(ValuePropertyEditorBase):

    def __init__(self, toolbox=None, parent=None):
        ValuePropertyEditorBase.__init__(self, toolbox, parent)

        self.color = [0.25, 0.25, 0.25]
        self.button = QtGui.QPushButton("Choose...")
        self.form.addRow("Value", self.button)
        self.add_stretch()
        self.button.clicked.connect(self.choose_color)

    def load_specific(self, item):
        self.color = safe_color(item.get("value"))
        self._refresh_button()

    def _refresh_button(self):
        rgb = [int(value * 255) for value in self.color]
        self.button.setStyleSheet(
            "QPushButton { background-color: rgb(%d,%d,%d); }" %
            (rgb[0], rgb[1], rgb[2])
        )

    def choose_color(self):
        initial = QtGui.QColor(
            int(self.color[0] * 255),
            int(self.color[1] * 255),
            int(self.color[2] * 255)
        )
        chosen = QtGui.QColorDialog.getColor(
            initial,
            self,
            "Choose Color"
        )
        if not chosen.isValid():
            return
        self.color = [
            chosen.red() / 255.0,
            chosen.green() / 255.0,
            chosen.blue() / 255.0
        ]
        self._refresh_button()
        self._control_changed()

    def write_specific(self, item):
        item["value"] = safe_color(self.color)


class LabelPropertyEditor(PropertyEditorBase):

    def __init__(self, toolbox=None, parent=None):
        PropertyEditorBase.__init__(self, toolbox, parent)
        self.add_stretch()


class SeparatorPropertyEditor(PropertyEditorBase):

    def __init__(self, toolbox=None, parent=None):
        PropertyEditorBase.__init__(self, toolbox, parent)

        self.label_edit.setVisible(False)
        self.show_label_check.setVisible(False)
        self.tooltip_edit.setVisible(False)

        label_widget = self.form.labelForField(self.label_edit)
        tooltip_widget = self.form.labelForField(self.tooltip_edit)

        if label_widget is not None:
            label_widget.setVisible(False)
        if tooltip_widget is not None:
            tooltip_widget.setVisible(False)

        self.add_stretch()

    def write_to_item(self):
        if self.item is None:
            return
        self.item["name"] = text_type(
            self.name_edit.text()
        ).strip() or "separator"
        self.item["callbacks"] = {}


__all__ = [
    "CheckboxPropertyEditor",
    "ColorPropertyEditor",
    "FloatPropertyEditor",
    "IntegerPropertyEditor",
    "LabelPropertyEditor",
    "MenuPropertyEditor",
    "SeparatorPropertyEditor",
    "StringPropertyEditor",
]
