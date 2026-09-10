# -*- coding: utf-8 -*-
from __future__ import print_function

from ...model.bindings import normalize_bindings
from .button import ButtonPropertyEditor


_STATE_KEYS = (
    "mode",
    "state_source",
    "state_get_script",
    "state_get_language",
    "state_on_script",
    "state_on_language",
    "state_off_script",
    "state_off_language",
    "state_on_label",
    "state_off_label",
    "state_on_color",
    "state_off_color",
)


class ActionButtonPropertyEditor(ButtonPropertyEditor):
    """Button editor with state-only controls removed from the public UI."""

    def __init__(self, toolbox=None, parent=None):
        ButtonPropertyEditor.__init__(
            self,
            toolbox=toolbox,
            parent=parent
        )

        self.mode.setCurrentIndex(0)
        self._refresh_mode()

    def current_mode(self):
        return "action"

    def _mode_changed(self, *args):
        self._refresh_mode()

    def _refresh_mode(self):
        section = self.appearance_section
        section.set_row_visible(
            self.color_button,
            True
        )
        for widget in (
            self.state_on_label,
            self.state_off_label,
            self.state_on_color_button,
            self.state_off_color_button,
        ):
            section.set_row_visible(
                widget,
                False
            )
        self.state_tabs.setVisible(False)
        self._refresh_trigger_section_visibility()

    def load_specific(self, item):
        ButtonPropertyEditor.load_specific(
            self,
            item
        )
        self.mode.setCurrentIndex(0)
        self._refresh_mode()

    def write_specific(self, item):
        ButtonPropertyEditor.write_specific(
            self,
            item
        )

        for key in _STATE_KEYS:
            item.pop(key, None)

        item["bindings"] = normalize_bindings(
            "button",
            item
        )


__all__ = [
    "ActionButtonPropertyEditor",
]
