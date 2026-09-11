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


def test_settings_dialog_uses_sidebar_and_stacked_pages():
    source = _read(
        "scripts/script_toolbox/ui/settings_dialog.py"
    )

    assert "QtGui.QListWidget()" in source
    assert 'setObjectName("SettingsCategoryList")' in source
    assert "QtGui.QStackedWidget()" in source
    assert 'setObjectName("SettingsPages")' in source
    assert "currentRowChanged.connect(" in source
    assert "self.pages.setCurrentIndex" in source
    assert 'self._add_category(\n            "General"' in source
    assert 'self._add_category(\n            "Privacy"' in source
    assert 'self._add_category(\n            "About"' in source


def test_settings_dialog_keeps_global_save_and_cancel_controls():
    source = _read(
        "scripts/script_toolbox/ui/settings_dialog.py"
    )

    assert 'QtGui.QPushButton("Cancel")' in source
    assert 'QtGui.QPushButton("Save")' in source
    assert "cancel_button.clicked.connect(self.reject)" in source
    assert "save_button.clicked.connect(self._save)" in source


def test_settings_pages_keep_existing_preferences():
    source = _read(
        "scripts/script_toolbox/ui/settings_dialog.py"
    )

    assert '"Update channel"' in source
    assert '"Usage statistics"' in source
    assert "self.update_channel_combo" in source
    assert "self.telemetry_combo" in source
    assert "get_update_channel()" in source
    assert "get_telemetry_consent()" in source


def test_about_page_exposes_version_links_and_icon_attribution():
    source = _read(
        "scripts/script_toolbox/ui/settings_dialog.py"
    )

    assert "PLUGIN_VERSION" in source
    assert "BUILD_CHANNEL" in source
    assert "GitHub repository" in source
    assert "Documentation" in source
    assert "Third-party assets" in source
    assert "Solar Icons by 480 Design" in source
    assert "Iconify" in source
    assert "CC BY 4.0" in source
    assert "setOpenExternalLinks(True)" in source
