# -*- coding: utf-8 -*-
from __future__ import print_function

from ...compat import QtGui
from ...model.bindings import normalize_bindings
from ...model.items import safe_color
from ...pycompat import text_type
from ..language_script_editor import LanguageScriptEditor
from .base import PropertyEditorBase
from .button import ButtonPropertyEditor


class ToggleButtonPropertyEditor(ButtonPropertyEditor):
    """Property editor for the dedicated stateful Toggle Button item."""

    def __init__(self, toolbox=None, parent=None):
        ButtonPropertyEditor.__init__(
            self,
            toolbox=toolbox,
            parent=parent
        )

        self.appearance_section.set_row_visible(
            self.color_button,
            False
        )

        self.state_source = QtGui.QComboBox()
        self.state_source.addItems([
            "Internal",
            "Script",
        ])
        self.internal_state = QtGui.QCheckBox()
        self.behavior_section.addRow(
            "State Source",
            self.state_source
        )
        self.behavior_section.addRow(
            "Internal State",
            self.internal_state
        )

        self.state_on_label = QtGui.QLineEdit()
        self.state_off_label = QtGui.QLineEdit()
        self.state_on_color = [0.22, 0.42, 0.26]
        self.state_off_color = [0.30, 0.30, 0.30]
        self.state_on_color_button = QtGui.QPushButton("Choose...")
        self.state_off_color_button = QtGui.QPushButton("Choose...")

        section = self.appearance_section
        section.addRow("ON Label", self.state_on_label)
        section.addRow("OFF Label", self.state_off_label)
        section.addRow("ON Color", self.state_on_color_button)
        section.addRow("OFF Color", self.state_off_color_button)

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
        self.state_tabs.addTab(self.state_get_editor, "Get State")
        self.state_tabs.addTab(self.state_on_editor, "Turn ON")
        self.state_tabs.addTab(self.state_off_editor, "Turn OFF")
        self.add_trigger_widget(self.state_tabs, 1)

        self.state_source.currentIndexChanged.connect(
            self._state_source_changed
        )
        self.internal_state.toggled.connect(self._control_changed)
        self.state_on_label.textEdited.connect(self._control_changed)
        self.state_off_label.textEdited.connect(self._control_changed)
        self.state_on_color_button.clicked.connect(
            lambda: self.choose_state_color("on")
        )
        self.state_off_color_button.clicked.connect(
            lambda: self.choose_state_color("off")
        )

        for editor in (
            self.state_get_editor,
            self.state_on_editor,
            self.state_off_editor,
        ):
            editor.textChanged.connect(self._control_changed)
            editor.languageChanged.connect(self._control_changed)

        self._refresh_state_source()

    def current_state_source(self):
        return (
            "script"
            if self.state_source.currentIndex() == 1
            else "internal"
        )

    def _state_source_changed(self, *args):
        self._refresh_state_source()
        self._control_changed()

    def _refresh_state_source(self):
        scripted = self.current_state_source() == "script"
        self.set_property_available(
            self.internal_state,
            not scripted,
            "Internal State is controlled by Get State when State Source is Script."
        )
        try:
            self.state_tabs.setTabEnabled(0, scripted)
            self.state_tabs.setTabToolTip(
                0,
                "" if scripted else "Get State is used only when State Source is Script."
            )
        except Exception:
            self.state_get_editor.setEnabled(scripted)

    def _refresh_state_colors(self):
        self.state_on_color_button.setStyleSheet(
            self._button_color_style(self.state_on_color)
        )
        self.state_off_color_button.setStyleSheet(
            self._button_color_style(self.state_off_color)
        )

    def choose_state_color(self, which):
        current = (
            self.state_on_color
            if which == "on"
            else self.state_off_color
        )
        title = (
            "Choose ON Color"
            if which == "on"
            else "Choose OFF Color"
        )
        initial = QtGui.QColor(
            int(current[0] * 255),
            int(current[1] * 255),
            int(current[2] * 255)
        )
        chosen = QtGui.QColorDialog.getColor(initial, self, title)
        if not chosen.isValid():
            return

        value = [
            chosen.red() / 255.0,
            chosen.green() / 255.0,
            chosen.blue() / 255.0
        ]
        if which == "on":
            self.state_on_color = value
        else:
            self.state_off_color = value
        self._refresh_state_colors()
        self._control_changed()

    def load_specific(self, item):
        ButtonPropertyEditor.load_specific(self, item)
        self.state_source.setCurrentIndex(
            1
            if item.get("state_source", "internal") == "script"
            else 0
        )
        self.internal_state.setChecked(bool(item.get("value", False)))
        self.state_on_label.setText(
            text_type(item.get("state_on_label", item.get("label", "Toggle")))
        )
        self.state_off_label.setText(
            text_type(item.get("state_off_label", item.get("label", "Toggle")))
        )
        self.state_on_color = safe_color(item.get("state_on_color"))
        self.state_off_color = safe_color(item.get("state_off_color"))

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

        self._refresh_state_colors()
        self._refresh_state_source()

    def write_specific(self, item):
        ButtonPropertyEditor.write_specific(self, item)
        item.pop("color", None)

        item["state_source"] = self.current_state_source()
        if item["state_source"] == "internal":
            item["value"] = bool(self.internal_state.isChecked())
        else:
            item.pop("value", None)

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
        ).strip() or item.get("label", "Toggle")
        item["state_off_label"] = text_type(
            self.state_off_label.text()
        ).strip() or item.get("label", "Toggle")
        item["state_on_color"] = safe_color(self.state_on_color)
        item["state_off_color"] = safe_color(self.state_off_color)

    def write_to_item(self):
        PropertyEditorBase.write_to_item(self)
        if self.item is not None:
            self.item["bindings"] = normalize_bindings(
                "toggle_button",
                self.item
            )


__all__ = [
    "ToggleButtonPropertyEditor",
]
