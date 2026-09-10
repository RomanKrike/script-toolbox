# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtGui
from ..style import toolbar_icon
from ..telemetry.events import track_product_event
from .icon_button import ICON_BUTTON_HEADER
from .icon_button import create_icon_button
from .settings_dialog import prompt_telemetry_consent
from .settings_dialog import show_settings_dialog


def build_settings_toolbox_class(base_class):
    """Attach Script Toolbox settings and first-run privacy UI to a window."""

    class SettingsToolbox(base_class):

        def __init__(self, parent=None):
            self.settings_button = None
            base_class.__init__(self, parent)

        def build_ui(self):
            base_class.build_ui(self)
            self._install_settings_button()

        def _install_settings_button(self):
            editor_button = getattr(
                self,
                "interface_editor_button",
                None
            )
            if editor_button is not None:
                editor_button.setIcon(
                    toolbar_icon("clipboard")
                )
                editor_button.setToolTip(
                    "Edit Interface"
                )

            topbar = self.findChild(
                QtGui.QFrame,
                "TopBar"
            )
            if topbar is None or topbar.layout() is None:
                return

            self.settings_button = create_icon_button(
                "gear",
                "Script Toolbox Settings",
                self.open_settings_dialog,
                parent=self,
                preset=ICON_BUTTON_HEADER
            )
            topbar.layout().addWidget(
                self.settings_button
            )

        def open_settings_dialog(self):
            track_product_event(
                "settings_opened"
            )
            return show_settings_dialog(
                parent=self
            )

        def prompt_telemetry_consent(self):
            return prompt_telemetry_consent(
                parent=self
            )

    SettingsToolbox.__name__ = "ScriptToolbox"
    return SettingsToolbox


__all__ = [
    "build_settings_toolbox_class",
]
