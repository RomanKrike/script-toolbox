# -*- coding: utf-8 -*-
from __future__ import print_function

from ...compat import QtGui
from ...model.bindings import normalize_bindings
from ...model.items import clamp
from ...pycompat import text_type
from ..icon_browse import install_icon_browse
from ..language_script_editor import LanguageScriptEditor
from .base import PropertyEditorBase


class ToggleIconPropertyEditor(PropertyEditorBase):
    """Property editor for a stateful icon with independent ON/OFF images."""

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

        self.state_source = QtGui.QComboBox()
        self.state_source.addItems([
            "Internal",
            "Script",
        ])
        self.internal_state = QtGui.QCheckBox()
        self.state_on_path = QtGui.QLineEdit()
        self.state_off_path = QtGui.QLineEdit()
        self.width = QtGui.QSpinBox()
        self.height = QtGui.QSpinBox()
        self.alignment = QtGui.QComboBox()

        self.width.setRange(8, 512)
        self.height.setRange(8, 512)
        self.alignment.addItems([
            "Left",
            "Center",
            "Right",
        ])

        self.behavior_section.addRow(
            "State Source",
            self.state_source
        )
        self.behavior_section.addRow(
            "Internal State",
            self.internal_state
        )

        section = self.appearance_section
        section.addRow(
            "ON Icon",
            self.state_on_path
        )
        section.addRow(
            "OFF Icon",
            self.state_off_path
        )
        section.addRow(
            "Icon Width",
            self.width
        )
        section.addRow(
            "Icon Height",
            self.height
        )
        section.addRow(
            "Content Alignment",
            self.alignment
        )

        self.state_on_browse_button = install_icon_browse(
            self,
            self.state_on_path,
            form=section.form
        )
        self.state_off_browse_button = install_icon_browse(
            self,
            self.state_off_path,
            form=section.form
        )

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
        self.add_trigger_widget(
            self.state_tabs,
            1
        )

        self.state_source.currentIndexChanged.connect(
            self._state_source_changed
        )
        self.internal_state.toggled.connect(
            self._control_changed
        )
        self.state_on_path.textEdited.connect(
            self._control_changed
        )
        self.state_off_path.textEdited.connect(
            self._control_changed
        )
        self.width.valueChanged.connect(
            self._control_changed
        )
        self.height.valueChanged.connect(
            self._control_changed
        )
        self.alignment.currentIndexChanged.connect(
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
            self.state_tabs.setTabEnabled(
                0,
                scripted
            )
            self.state_tabs.setTabToolTip(
                0,
                ""
                if scripted
                else "Get State is used only when State Source is Script."
            )
        except Exception:
            self.state_get_editor.setEnabled(
                scripted
            )

    def load_specific(self, item):
        self.state_source.setCurrentIndex(
            1
            if item.get("state_source", "internal") == "script"
            else 0
        )
        self.internal_state.setChecked(
            bool(item.get("value", False))
        )
        self.state_on_path.setText(
            text_type(item.get("state_on_path", ""))
        )
        self.state_off_path.setText(
            text_type(item.get("state_off_path", ""))
        )
        self.width.setValue(
            int(item.get("width", 24))
        )
        self.height.setValue(
            int(item.get("height", 24))
        )
        alignment = item.get(
            "content_alignment",
            item.get("alignment", "left")
        )
        self.alignment.setCurrentIndex({
            "left": 0,
            "center": 1,
            "right": 2,
        }.get(
            alignment,
            0
        ))

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
        self._refresh_state_source()

    def write_specific(self, item):
        item["state_source"] = self.current_state_source()
        if item["state_source"] == "internal":
            item["value"] = bool(
                self.internal_state.isChecked()
            )
        else:
            item.pop("value", None)

        item["state_on_path"] = text_type(
            self.state_on_path.text()
        )
        item["state_off_path"] = text_type(
            self.state_off_path.text()
        )
        item["width"] = clamp(
            int(self.width.value()),
            8,
            512
        )
        item["height"] = clamp(
            int(self.height.value()),
            8,
            512
        )
        alignment = (
            "right"
            if self.alignment.currentIndex() == 2
            else "center"
            if self.alignment.currentIndex() == 1
            else "left"
        )
        item["content_alignment"] = alignment
        item.pop("alignment", None)

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

        item.pop("path", None)
        item.pop("clickable", None)
        item.pop("mode", None)

    def write_to_item(self):
        PropertyEditorBase.write_to_item(
            self
        )
        if self.item is not None:
            self.item["bindings"] = normalize_bindings(
                "toggle_icon",
                self.item
            )


__all__ = [
    "ToggleIconPropertyEditor",
]
