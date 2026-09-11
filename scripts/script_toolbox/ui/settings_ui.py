# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtGui
from ..style import toolbar_icon
from .settings_dialog import prompt_telemetry_consent
from .settings_dialog import show_settings_dialog


def build_settings_toolbox_class(base_class):
    """Attach Script Toolbox settings and first-run privacy UI to a window."""

    class SettingsToolbox(base_class):

        def __init__(self, parent=None):
            self.settings_button = None
            self.settings_menu = None
            self.open_editor_action = None
            self.settings_action = None
            base_class.__init__(self, parent)

        def build_ui(self):
            base_class.build_ui(self)
            self._install_settings_menu()

        def _install_settings_menu(self):
            button = getattr(
                self,
                "interface_editor_button",
                None
            )
            if button is None:
                return

            try:
                button.clicked.disconnect()
            except Exception:
                pass

            button.setIcon(
                toolbar_icon("gear")
            )
            button.setToolTip(
                "Script Toolbox Menu"
            )

            menu = QtGui.QMenu(
                button
            )

            self.open_editor_action = menu.addAction(
                "Open Editor"
            )
            self.open_editor_action.triggered.connect(
                self._open_editor_from_menu
            )

            menu.addSeparator()

            self.settings_action = menu.addAction(
                "Settings..."
            )
            self.settings_action.triggered.connect(
                self._open_settings_from_menu
            )

            button.clicked.connect(
                self._show_settings_menu
            )

            self.settings_button = button
            self.settings_menu = menu

        def _show_settings_menu(
            self,
            checked=False
        ):
            if (
                self.settings_button is None or
                self.settings_menu is None
            ):
                return

            position = self.settings_button.mapToGlobal(
                self.settings_button.rect().bottomLeft()
            )
            self.settings_menu.exec_(
                position
            )

        def _open_editor_from_menu(
            self,
            checked=False
        ):
            return self.open_interface_editor()

        def _open_settings_from_menu(
            self,
            checked=False
        ):
            return self.open_settings_dialog()

        def open_settings_dialog(self):
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
