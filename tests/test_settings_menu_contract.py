# -*- coding: utf-8 -*-

import os


ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


def _read(relative_path):
    path = os.path.join(
        ROOT,
        *relative_path.split("/")
    )
    with open(path, "r") as handle:
        return handle.read()


def test_common_menu_bar_replaces_legacy_header_controls():
    source = _read(
        "scripts/script_toolbox/ui/main_window.py"
    )

    assert "QtGui.QMenuBar(" in source
    assert '"ToolboxMenuBar"' in source
    assert 'self._styled_menu("Editor")' in source
    assert 'self._styled_menu("Settings")' in source
    assert 'self._styled_menu("Help")' in source
    assert '"Open Editor"' in source
    assert '"Open Settings"' in source
    assert '"Check for Updates"' in source
    assert (
        'self.check_updates_action = self.settings_menu.addAction('
        in source
    )
    assert '"Reload Config"' in source
    assert "setNativeMenuBar" in source
    assert "menu.setStyleSheet(STYLE)" in source

    assert '"TopBar"' not in source
    assert '"ToolboxTitle"' not in source
    assert "interface_editor_button" not in source
    assert "check_updates_button" not in source
    assert "reload_button" not in source
    assert "update_button" not in source


def test_status_bar_keeps_console_icon_left_and_transient_status_right():
    source = _read(
        "scripts/script_toolbox/ui/main_window.py"
    )

    assert "class ToolboxStatusBar(" in source
    assert 'toolbar_icon("console")' in source
    assert '"StatusLogsIcon"' in source
    assert "self.logs_label" not in source
    assert '"StatusAction"' in source
    assert "addPermanentWidget(" in source
    assert "def show_status(" in source
    assert "def show_action(" in source
    assert "def clearMessage(" in source
    assert '"Ready"' not in source


def test_update_check_is_not_owned_by_help_menu():
    source = _read(
        "scripts/script_toolbox/ui/main_window.py"
    )

    assert (
        'self.check_updates_action = self.settings_menu.addAction('
        in source
    )
    assert (
        'self.check_updates_action = self.help_menu.addAction('
        not in source
    )


def test_settings_wrapper_reuses_existing_settings_dialog_and_help_menu():
    source = _read(
        "scripts/script_toolbox/ui/settings_ui.py"
    )

    assert '"help_menu"' in source
    assert '"GitHub"' in source
    assert '"Help / Docs"' in source
    assert "_install_help_resources" in source
    assert "return show_settings_dialog(" in source
    assert "QtGui.QDesktopServices.openUrl(" in source
    assert "QtCore.QUrl(" in source

    assert (
        '_GITHUB_URL = "https://github.com/RomanKrike/script-toolbox"'
        in source
    )
    assert (
        '_DOCS_URL = "https://romankrike.github.io/script-toolbox/"'
        in source
    )


def test_menu_bar_is_common_ui_not_host_specific():
    source = _read(
        "scripts/script_toolbox/ui/main_window.py"
    )

    assert 'HOST.key == "maya"' not in source
    assert 'HOST.key == "nuke"' not in source
    assert "maya.cmds" not in source
    assert "import nuke" not in source
