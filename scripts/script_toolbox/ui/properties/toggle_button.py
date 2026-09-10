# -*- coding: utf-8 -*-
from __future__ import print_function

from ...compat import QtGui
from ...model.bindings import normalize_bindings
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

        self.mode.setCurrentIndex(1)

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

        self.state_source.currentIndexChanged.connect(
            self._state_source_changed
        )
        self.internal_state.toggled.connect(
            self._control_changed
        )

        self._refresh_mode()
        self._refresh_state_source()

    def current_mode(self):
        return "state"

    def _mode_changed(self, *args):
        self._refresh_mode()

    def _refresh_mode(self):
        section = self.appearance_section
        section.set_row_visible(
            self.color_button,
            False
        )
        for widget in (
            self.state_on_label,
            self.state_off_label,
            self.state_on_color_button,
            self.state_off_color_button,
        ):
            section.set_row_visible(
                widget,
                True
            )
        self.state_tabs.setVisible(True)
        self._refresh_trigger_section_visibility()

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
        ButtonPropertyEditor.load_specific(
            self,
            item
        )
        self.mode.setCurrentIndex(1)
        self.state_source.setCurrentIndex(
            1
            if item.get("state_source", "internal") == "script"
            else 0
        )
        self.internal_state.setChecked(
            bool(item.get("value", False))
        )
        self._refresh_mode()
        self._refresh_state_source()

    def write_specific(self, item):
        ButtonPropertyEditor.write_specific(
            self,
            item
        )

        item.pop("mode", None)
        item.pop("color", None)
        item["state_source"] = self.current_state_source()

        if item["state_source"] == "internal":
            item["value"] = bool(
                self.internal_state.isChecked()
            )
        else:
            item.pop("value", None)

    def write_to_item(self):
        PropertyEditorBase.write_to_item(
            self
        )
        if self.item is not None:
            # A Toggle Button must always retain its state-toggle trigger even
            # when users edit the rest of the trigger set.
            self.item["bindings"] = normalize_bindings(
                "toggle_button",
                self.item
            )


__all__ = [
    "ToggleButtonPropertyEditor",
]
