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
        self.mode.setVisible(False)
        try:
            label = self.form.labelForField(self.mode)
            if label is not None:
                label.setVisible(False)
        except Exception:
            pass

        self._refresh_mode()

    def current_mode(self):
        return "action"

    def _mode_changed(self, *args):
        self._refresh_mode()

    def _refresh_mode(self):
        self.action_group.setVisible(True)
        self.state_group.setVisible(False)
        self.state_tabs.setVisible(False)

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
