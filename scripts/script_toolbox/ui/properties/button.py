# -*- coding: utf-8 -*-
from __future__ import print_function

from ...compat import QtGui
from ...model.items import clamp
from ...model.items import safe_color
from ...pycompat import text_type
from ..language_script_editor import LanguageScriptEditor
from .base import PropertyEditorBase


class ButtonPropertyEditor(PropertyEditorBase):

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

        self.mode = QtGui.QComboBox()
        self.mode.addItems([
            "Action",
            "State",
        ])

        self.color = [0.25, 0.25, 0.25]
        self.state_on_color = [0.22, 0.42, 0.26]
        self.state_off_color = [0.30, 0.30, 0.30]

        self.icon_path = QtGui.QLineEdit()
        self.icon_size = QtGui.QSpinBox()
        self.icon_size.setRange(8, 256)
        self.icon_only = QtGui.QCheckBox("Icon Only")

        self.color_button = QtGui.QPushButton("Choose...")
        self.state_on_label = QtGui.QLineEdit()
        self.state_off_label = QtGui.QLineEdit()
        self.state_on_color_button = QtGui.QPushButton("Choose...")
        self.state_off_color_button = QtGui.QPushButton("Choose...")

        self.form.addRow("Mode", self.mode)
        self.form.addRow("Icon Path", self.icon_path)
        self.form.addRow("Icon Size", self.icon_size)
        self.form.addRow("", self.icon_only)

        self.action_group = QtGui.QGroupBox("Action Appearance")
        action_form = QtGui.QFormLayout(self.action_group)
        action_form.addRow("Button Color", self.color_button)
        self.root_layout.addWidget(self.action_group)

        self.state_group = QtGui.QGroupBox("State Appearance")
        state_form = QtGui.QFormLayout(self.state_group)
        state_form.addRow("ON Label", self.state_on_label)
        state_form.addRow("OFF Label", self.state_off_label)
        state_form.addRow("ON Color", self.state_on_color_button)
        state_form.addRow("OFF Color", self.state_off_color_button)
        self.root_layout.addWidget(self.state_group)

        self.state_tabs = QtGui.QTabWidget()

        self.state_get_editor = LanguageScriptEditor(
            language="python",
            toolbox=self.toolbox
        )
        self.state_get_editor.set_language_enabled(
            False,
            "State queries use Python so the state variable can be evaluated."
        )
        self.state_on_editor = LanguageScriptEditor(
            language="python",
            toolbox=self.toolbox
        )
        self.state_off_editor = LanguageScriptEditor(
            language="python",
            toolbox=self.toolbox
        )

        self.state_tabs.addTab(
            self.state_get_editor,
            "Get State"
        )
        self.state_tabs.addTab(
            self.state_on_editor,
            "Turn ON"
        )
        self.state_tabs.addTab(
            self.state_off_editor,
            "Turn OFF"
        )
        self.root_layout.addWidget(
            self.state_tabs,
            1
        )

        self.mode.currentIndexChanged.connect(
            self._mode_changed
        )
        self.icon_path.textEdited.connect(
            self._control_changed
        )
        self.icon_size.valueChanged.connect(
            self._control_changed
        )
        self.icon_only.toggled.connect(
            self._control_changed
        )
        self.color_button.clicked.connect(
            lambda: self.choose_color("action")
        )
        self.state_on_color_button.clicked.connect(
            lambda: self.choose_color("on")
        )
        self.state_off_color_button.clicked.connect(
            lambda: self.choose_color("off")
        )
        self.state_on_label.textEdited.connect(
            self._control_changed
        )
        self.state_off_label.textEdited.connect(
            self._control_changed
        )

        for editor in (
            self.state_get_editor,
            self.state_on_editor,
            self.state_off_editor,
        ):
            editor.textChanged.connect(
                self._control_changed
            )
            editor.languageChanged.connect(
                self._control_changed
            )

        self._refresh_mode()

    def current_mode(self):
        return (
            "state"
            if self.mode.currentIndex() == 1
            else "action"
        )

    def _mode_changed(self, *args):
        if self.item is not None and not self.loading:
            self.binding_panel.write_to_item(
                self.item
            )
            self.item["mode"] = self.current_mode()
            self.refresh_binding_panel()

        self._refresh_mode()
        self._control_changed()

    def _refresh_mode(self):
        state_mode = self.current_mode() == "state"
        self.action_group.setVisible(not state_mode)
        self.state_group.setVisible(state_mode)
        self.state_tabs.setVisible(state_mode)

    def load_specific(self, item):
        self.mode.setCurrentIndex(
            1
            if item.get("mode", "action") == "state"
            else 0
        )

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
        self.state_on_color = safe_color(
            item.get("state_on_color")
        )
        self.state_off_color = safe_color(
            item.get("state_off_color")
        )

        self.state_on_label.setText(
            text_type(
                item.get(
                    "state_on_label",
                    item.get("label", "ON")
                )
            )
        )
        self.state_off_label.setText(
            text_type(
                item.get(
                    "state_off_label",
                    item.get("label", "OFF")
                )
            )
        )

        self.state_get_editor.set_language("python")
        self.state_get_editor.setPlainText(
            text_type(item.get("state_get_script", ""))
        )
        self.state_on_editor.set_language(
            item.get("state_on_language", "python")
        )
        self.state_on_editor.setPlainText(
            text_type(item.get("state_on_script", ""))
        )
        self.state_off_editor.set_language(
            item.get("state_off_language", "python")
        )
        self.state_off_editor.setPlainText(
            text_type(item.get("state_off_script", ""))
        )

        self._refresh_colors()
        self._refresh_mode()

    def _button_color_style(self, color):
        rgb = [
            int(value * 255)
            for value in safe_color(color)
        ]
        return (
            "QPushButton { background-color: rgb(%d,%d,%d); }" %
            (rgb[0], rgb[1], rgb[2])
        )

    def _refresh_colors(self):
        self.color_button.setStyleSheet(
            self._button_color_style(self.color)
        )
        self.state_on_color_button.setStyleSheet(
            self._button_color_style(self.state_on_color)
        )
        self.state_off_color_button.setStyleSheet(
            self._button_color_style(self.state_off_color)
        )

    def choose_color(self, which):
        if which == "on":
            current = self.state_on_color
            title = "Choose ON Color"
        elif which == "off":
            current = self.state_off_color
            title = "Choose OFF Color"
        else:
            current = self.color
            title = "Choose Button Color"

        initial = QtGui.QColor(
            int(current[0] * 255),
            int(current[1] * 255),
            int(current[2] * 255)
        )
        chosen = QtGui.QColorDialog.getColor(
            initial,
            self,
            title
        )

        if not chosen.isValid():
            return

        value = [
            chosen.red() / 255.0,
            chosen.green() / 255.0,
            chosen.blue() / 255.0
        ]

        if which == "on":
            self.state_on_color = value
        elif which == "off":
            self.state_off_color = value
        else:
            self.color = value

        self._refresh_colors()
        self._control_changed()

    def write_specific(self, item):
        item["mode"] = self.current_mode()
        item["color"] = safe_color(self.color)
        item["icon_path"] = text_type(
            self.icon_path.text()
        )
        item["icon_size"] = clamp(
            int(self.icon_size.value()),
            8,
            256
        )
        item["icon_only"] = bool(
            self.icon_only.isChecked()
        )

        item["state_get_script"] = text_type(
            self.state_get_editor.toPlainText()
        )
        item["state_get_language"] = "python"
        item["state_on_script"] = text_type(
            self.state_on_editor.toPlainText()
        )
        item["state_on_language"] = self.state_on_editor.language()
        item["state_off_script"] = text_type(
            self.state_off_editor.toPlainText()
        )
        item["state_off_language"] = self.state_off_editor.language()

        item["state_on_label"] = text_type(
            self.state_on_label.text()
        ).strip() or item.get("label", "ON")
        item["state_off_label"] = text_type(
            self.state_off_label.text()
        ).strip() or item.get("label", "OFF")
        item["state_on_color"] = safe_color(
            self.state_on_color
        )
        item["state_off_color"] = safe_color(
            self.state_off_color
        )

        item.pop("language", None)
        item.pop("click_script", None)
        item.pop("shift_script", None)


__all__ = [
    "ButtonPropertyEditor",
]
