# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtCore
from ..compat import QtGui
from .settings_dialog import prompt_telemetry_consent
from .settings_dialog import show_settings_dialog


_GITHUB_URL = "https://github.com/RomanKrike/script-toolbox"
_DOCS_URL = "https://romankrike.github.io/script-toolbox/"


class SettingsToolboxMixin(object):

    def __init__(self, parent=None):
        self.github_action = None
        self.help_docs_action = None
        super(SettingsToolboxMixin, self).__init__(parent
        )

    def build_ui(self):
        super(SettingsToolboxMixin, self).build_ui()
        self._install_help_resources()

    def _install_help_resources(self):
        menu = getattr(
            self,
            "help_menu",
            None
        )
        if menu is None:
            return

        if menu.actions():
            menu.addSeparator()

        self.github_action = menu.addAction(
            "GitHub"
        )
        self.github_action.triggered.connect(
            self._open_github_from_menu
        )

        self.help_docs_action = menu.addAction(
            "Help / Docs"
        )
        self.help_docs_action.triggered.connect(
            self._open_help_docs_from_menu
        )

    def _open_github_from_menu(
        self,
        checked=False
    ):
        return self._open_external_url(
            _GITHUB_URL
        )

    def _open_help_docs_from_menu(
        self,
        checked=False
    ):
        return self._open_external_url(
            _DOCS_URL
        )

    def _open_external_url(
        self,
        url
    ):
        return QtGui.QDesktopServices.openUrl(
            QtCore.QUrl(
                url
            )
        )

    def open_settings_dialog(self):
        return show_settings_dialog(
            parent=self
        )

    def prompt_telemetry_consent(self):
        return prompt_telemetry_consent(
            parent=self
        )



def build_settings_toolbox_class(base_class):
    return type("ScriptToolbox", (SettingsToolboxMixin, base_class), {})


__all__ = ["SettingsToolboxMixin", "build_settings_toolbox_class"]
