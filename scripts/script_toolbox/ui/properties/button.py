# -*- coding: utf-8 -*-
from __future__ import print_function

from ...compat import HOST
from ...compat import QtGui
from ...model.items import safe_color
from ...pycompat import text_type
from ..script_editor import ScriptEditorWidget
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

        self.language = QtGui.QComboBox()
        self.languages = list(
            HOST.available_languages()
        )

        for language in self.languages:
            self.language.addItem(
                language.upper()
                if language == "mel"
                else language.title()
            )

        self.color = [0.25, 0.25, 0.25]
        self.state_on_color = [0.22, 0.42, 0.26]
        self.state_off_color = [0.30, 0.30, 0.30]

        self.color_button = QtGui.QPushButton("Choose...")
        self.state_on_label = QtGui.QLineEdit()
        self.state_off_label = QtGui.QLineEdit()
        self.state_on_color_button = QtGui.QPushButton("Choose...")
        self.state_off_color_button = QtGui.QPushButton("Choose...")

        self.form.addRow("Mode", self.mode)
        self.form.addRow("Language", self.language)

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

        self.tabs = QtGui.QTabWidget()

        self.click_editor = ScriptEditorWidget(
            language="python",
            toolbox=self.toolbox
        )
        self.shift_editor = ScriptEditorWidget(
            language="python",
            toolbox=self.toolbox
        )
        self.state_get_editor = ScriptEditorWidget(
            language="python",
            toolbox=self.toolbox
        )
        self.state_on_editor = ScriptEditorWidget(
            language="python",
            toolbox=self.toolbox
        )
        self.state_off_editor = ScriptEditorWidget(
            language="python",
            toolbox=self.toolbox
        )

        self.root_layout.addWidget(
            self.tabs,
            1
        )

        self.mode.currentIndexChanged.connect(
            self._mode_changed
        )
        self.language.currentIndexChanged.connect(
            self._language_changed
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
            self.click_editor,
            self.shift_editor,
            self.state_get_editor,
            self.state_on_editor,
            self.state_off_editor,
        ):
            editor.textChanged.connect(
                self._control_changed
            )

        self._refresh_mode()

    def current_language(self):
        index = self.language.currentIndex()

        if (
            index < 0 or
            index >= len(self.languages)
        ):
            return "python"

        return self.languages[index]

    def current_mode(self):
        return (
            "state"
            if self.mode.currentIndex() == 1
            else "action"
        )

    def _mode_changed(self, *args):
        self._refresh_mode()
        self._control_changed()

    def _refresh_mode(self):
        state_mode = self.current_mode() == "state"
        self.action_group.setVisible(not state_mode)
        self.state_group.setVisible(state_mode)

        current_widget = self.tabs.currentWidget()
        self.tabs.clear()

        if state_mode:
            self.tabs.addTab(
                self.state_get_editor,
                "Get State (Python)"
            )
            self.tabs.addTab(
                self.state_on_editor,
                "Turn ON"
            )
            self.tabs.addTab(
                self.state_off_editor,
                "Turn OFF"
            )
        else:
            self.tabs.addTab(
                self.click_editor,
                "Click Script"
            )
            self.tabs.addTab(
                self.shift_editor,
                "Shift + Click"
            )

        if current_widget is not None:
            index = self.tabs.indexOf(current_widget)
            if index >= 0:
                self.tabs.setCurrentIndex(index)

    def _language_changed(self, *args):
        language = self.current_language()

        self.click_editor.set_language(language)
        self.shift_editor.set_language(language)
        self.state_on_editor.set_language(language)
        self.state_off_editor.set_language(language)
        self.state_get_editor.set_language("python")
        self._control_changed()

    def load_specific(self, item):
        language = item.get(
            "language",
            "python"
        )

        if language not in self.languages:
            self.languages.append(language)
            self.language.addItem(
                "{0} (Unavailable in {1})".format(
                    language.upper(),
                    HOST.display_name
                )
            )

        self.language.setCurrentIndex(
            self.languages.index(language)
        )
        self.mode.setCurrentIndex(
            1
            if item.get("mode", "action") == "state"
            else 0
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

        self.click_editor.setPlainText(
            text_type(item.get("click_script", ""))
        )
        self.shift_editor.setPlainText(
            text_type(item.get("shift_script", ""))
        )
        self.state_get_editor.setPlainText(
            text_type(item.get("state_get_script", ""))
        )
        self.state_on_editor.setPlainText(
            text_type(item.get("state_on_script", ""))
        )
        self.state_off_editor.setPlainText(
            text_type(item.get("state_off_script", ""))
        )

        self._language_changed()
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
        item["language"] = self.current_language()
        item["color"] = safe_color(self.color)
        item["click_script"] = text_type(
            self.click_editor.toPlainText()
        )
        item["shift_script"] = text_type(
            self.shift_editor.toPlainText()
        )
        item["state_get_script"] = text_type(
            self.state_get_editor.toPlainText()
        )
        item["state_on_script"] = text_type(
            self.state_on_editor.toPlainText()
        )
        item["state_off_script"] = text_type(
            self.state_off_editor.toPlainText()
        )
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

    def run_click(self):
        self.write_to_item()
        return self.click_editor.run()

    def run_shift(self):
        self.write_to_item()
        return self.shift_editor.run()


__all__ = [
    "ButtonPropertyEditor",
]
