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


def test_header_gear_replaces_separate_editor_and_settings_buttons():
    source = _read(
        "scripts/script_toolbox/ui/settings_ui.py"
    )

    assert '"interface_editor_button"' in source
    assert 'toolbar_icon("gear")' in source
    assert '"Open Editor"' in source
    assert '"Settings..."' in source
    assert '"GitHub"' in source
    assert '"Help / Docs"' in source
    assert '"Usage Statistics..."' not in source
    assert "button.clicked.disconnect()" in source
    assert "button.clicked.connect(" in source
    assert "_show_settings_menu" in source

    assert 'toolbar_icon("clipboard")' not in source
    assert "create_icon_button(" not in source
    assert "findChild(" not in source
    assert "topbar.layout().addWidget" not in source


def test_header_gear_menu_keeps_direct_action_references():
    source = _read(
        "scripts/script_toolbox/ui/settings_ui.py"
    )

    assert "self.settings_menu = menu" in source
    assert "self.open_editor_action = menu.addAction(" in source
    assert "self.settings_action = menu.addAction(" in source
    assert "self.github_action = menu.addAction(" in source
    assert "self.help_docs_action = menu.addAction(" in source
    assert "self._open_editor_from_menu" in source
    assert "self._open_settings_from_menu" in source
    assert "self._open_github_from_menu" in source
    assert "self._open_help_docs_from_menu" in source
    assert "self.settings_menu.exec_(" in source


def test_settings_menu_action_opens_general_settings_dialog():
    source = _read(
        "scripts/script_toolbox/ui/settings_ui.py"
    )

    assert "def _open_settings_from_menu(" in source
    assert "return self.open_settings_dialog()" in source
    assert "return show_settings_dialog(" in source


def test_resource_actions_open_project_urls_in_default_browser():
    source = _read(
        "scripts/script_toolbox/ui/settings_ui.py"
    )

    assert (
        '_GITHUB_URL = "https://github.com/RomanKrike/script-toolbox"'
        in source
    )
    assert (
        '_DOCS_URL = "https://romankrike.github.io/script-toolbox/"'
        in source
    )
    assert "QtGui.QDesktopServices.openUrl(" in source
    assert "QtCore.QUrl(url)" in source
