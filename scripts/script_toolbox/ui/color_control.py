# -*- coding: utf-8 -*-
"""One RGB/HEX control shared by runtime items and their property editor."""
import re

from ..compat import QtCore, QtGui
from ..model.items import safe_color
from ..pycompat import text_type
from ..style import metrics, palette
from .layout_helpers import configure_inline_layout


class ColorControl(QtGui.QWidget):
    valueChanged = QtCore.Signal(object)

    def __init__(self, value=None, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setObjectName("ColorControl")
        self._value = safe_color(value)
        self._rgb_maximum = 1.0
        layout = self._layout = QtGui.QGridLayout(self)
        configure_inline_layout(layout)
        self.swatch = QtGui.QPushButton(self)
        self.swatch.setObjectName("ColorSwatch")
        self.swatch.setToolTip("Choose Color")
        self.swatch.setAccessibleName("Choose Color")
        self.swatch.setFixedWidth(metrics.COLOR_SWATCH_WIDTH)
        self.swatch.clicked.connect(self.choose_color)
        layout.addWidget(self.swatch, 1, 0, QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.channels = []
        self.channel_labels = []
        for index, name in enumerate(("R", "G", "B")):
            label = QtGui.QLabel(name, self)
            label.setObjectName("ColorChannelLabel")
            spin = QtGui.QDoubleSpinBox(self)
            spin.setObjectName("ColorChannel")
            spin.setRange(0.0, 1.0)
            spin.setDecimals(3)
            spin.setSingleStep(0.01)
            spin.setKeyboardTracking(False)
            spin.setButtonSymbols(QtGui.QAbstractSpinBox.NoButtons)
            spin.setMinimumWidth(metrics.COLOR_CHANNEL_MIN_WIDTH)
            spin.setAccessibleName(name)
            label.setBuddy(spin)
            spin.valueChanged.connect(
                lambda value, channel=index: self._channel_changed(channel, value))
            layout.addWidget(label, 0, index + 1)
            layout.addWidget(spin, 1, index + 1)
            layout.setColumnStretch(index + 1, 1)
            self.channels.append(spin)
            self.channel_labels.append(label)
        label = self.hex_label = QtGui.QLabel("HEX", self)
        label.setObjectName("ColorChannelLabel")
        self.hex_edit = QtGui.QLineEdit(self)
        self.hex_edit.setObjectName("ColorHex")
        self.hex_edit.setMaxLength(7)
        self.hex_edit.setMinimumWidth(metrics.COLOR_HEX_MIN_WIDTH)
        self.hex_edit.setAccessibleName("HEX")
        self.hex_edit.setToolTip("RGB hexadecimal color (#RRGGBB)")
        label.setBuddy(self.hex_edit)
        self.hex_edit.editingFinished.connect(self._hex_finished)
        layout.addWidget(label, 0, 4)
        layout.addWidget(self.hex_edit, 1, 4)
        layout.setColumnStretch(4, 1)
        self.set_value(self._value)

    def configure(self, show_rgb=True, rgb_range="0-1", show_hex=True):
        self._rgb_maximum = 255.0 if rgb_range == "0-255" else 1.0
        for index, spin in enumerate(self.channels):
            blocked = spin.blockSignals(True)
            try:
                spin.setDecimals(0 if self._rgb_maximum == 255.0 else 3)
                spin.setRange(0.0, self._rgb_maximum)
                spin.setSingleStep(1.0 if self._rgb_maximum == 255.0 else 0.01)
            finally:
                spin.blockSignals(blocked)
            spin.setVisible(show_rgb)
            self.channel_labels[index].setVisible(show_rgb)
            self._layout.setColumnStretch(index + 1, 1 if show_rgb else 0)
        self.hex_label.setVisible(show_hex)
        self.hex_edit.setVisible(show_hex)
        self._layout.setColumnStretch(4, 1 if show_hex else 0)
        self.set_value(self._value)

    def value(self):
        return list(self._value)

    def set_value(self, value):
        """Synchronize all displays without emitting a user change.

        Keep full model precision: three decimals are a display/input choice,
        not a reason to quantize untouched channels on model synchronization.
        """
        self._value = safe_color(value)
        for index, spin in enumerate(self.channels):
            blocked = spin.blockSignals(True)
            try:
                spin.setValue(self._value[index] * self._rgb_maximum)
            finally:
                spin.blockSignals(blocked)
        rgb = [int(round(component * 255)) for component in self._value]
        self._display_hex = "#{0:02X}{1:02X}{2:02X}".format(*rgb)
        self.hex_edit.setText(self._display_hex)
        self._refresh_swatch(rgb)

    def _refresh_swatch(self, rgb):
        base = QtGui.QColor(palette.CONTROL_BG)
        disabled = [(component + background) // 2 for component, background
                    in zip(rgb, (base.red(), base.green(), base.blue()))]
        self.swatch.setStyleSheet("""
QPushButton#ColorSwatch {
    background-color: rgb(%s);
    border: 1px solid %s;
    border-radius: %spx;
    min-height: %spx;
    max-height: %spx;
    padding: 0px;
}
QPushButton#ColorSwatch:hover { border-color: %s; }
QPushButton#ColorSwatch:focus { border-color: %s; }
QPushButton#ColorSwatch:disabled {
    background-color: rgb(%s);
    border-color: %s;
}
""" % (",".join(str(v) for v in rgb), palette.TOOLTIP_BORDER,
       metrics.BORDER_RADIUS_CONTROL, metrics.COLOR_CONTROL_HEIGHT - 2,
       metrics.COLOR_CONTROL_HEIGHT - 2, palette.HOVER_BORDER,
       palette.FOCUS_BORDER, ",".join(str(v) for v in disabled),
       palette.BORDER_GROUP))

    def _commit(self, value):
        previous = self.value()
        self.set_value(value)
        if self._value != previous:
            self.valueChanged.emit(self.value())

    def _channel_changed(self, index, value):
        color = self.value()
        color[index] = value / self._rgb_maximum
        self._commit(color)

    def _hex_finished(self):
        value = text_type(self.hex_edit.text()).strip().lstrip("#")
        if "#" + value.upper() == self._display_hex:
            # Merely focusing/leaving HEX must not quantize the model to 8 bits.
            self.hex_edit.setText(self._display_hex)
            return
        if not re.match(r"^[0-9a-fA-F]{6}$", value):
            self.set_value(self._value)
            return
        self._commit([int(value[index:index + 2], 16) / 255.0
                      for index in (0, 2, 4)])

    def choose_color(self):
        initial = QtGui.QColor.fromRgbF(*self._value)
        chosen = QtGui.QColorDialog.getColor(initial, self, "Choose Color")
        if chosen.isValid():
            self._commit([chosen.redF(), chosen.greenF(), chosen.blueF()])
