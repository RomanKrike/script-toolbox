# -*- coding: utf-8 -*-
from __future__ import print_function

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
    with open(path, "r") as stream:
        return stream.read()


def test_required_solar_icons_are_bundled():
    icons_dir = os.path.join(
        ROOT,
        "scripts",
        "script_toolbox",
        "resources",
        "icons",
        "solar"
    )

    for name in (
        "cloud-download.svg",
        "cloud-upload.svg",
        "settings.svg",
        "trash-bin-minimalistic-2.svg",
    ):
        path = os.path.join(
            icons_dir,
            name
        )
        assert os.path.isfile(path)
        assert os.path.getsize(path) > 0


def test_solar_resolver_preserves_update_fallback():
    source = _read(
        "scripts/script_toolbox/style/builtin_icons.py"
    )

    assert '("cloud-download", "Cloud Download", "cloud-download.svg")' in source
    assert '("cloud-upload", "Cloud Upload", "cloud-upload.svg")' in source
    assert '("settings", "Settings", "settings.svg")' in source
    assert '"update": "reload"' not in source


def test_icon_properties_use_file_browser():
    icon_editor = _read(
        "scripts/script_toolbox/ui/properties/icon.py"
    )
    browser = _read(
        "scripts/script_toolbox/ui/icon_file_browser.py"
    )
    ui_init = _read(
        "scripts/script_toolbox/ui/__init__.py"
    )

    assert "icon_source" not in icon_editor
    assert "icon_path_field(" in icon_editor
    assert "QFileDialog.getOpenFileName" in browser
    assert "builtin_icons_directory()" in browser
    assert "builtin_icon_resource_from_file_path" in browser
    assert "ButtonPropertyEditor" in ui_init
    assert '"icon_path"' in ui_init
    assert "install_icon_path_browse(" in ui_init


def test_toolbar_overrides_are_targeted():
    overrides = _read(
        "scripts/script_toolbox/ui/toolbar_icon_overrides.py"
    )
    ui_init = _read(
        "scripts/script_toolbox/ui/__init__.py"
    )
    update_ui = _read(
        "scripts/script_toolbox/ui/update_channels_ui.py"
    )

    assert 'toolbar_icon("cloud-download")' in overrides
    assert 'toolbar_icon("cloud-upload")' in overrides
    assert 'tooltip="Clear Output"' in overrides
    assert 'toolbar_icon("delete")' in overrides
    assert 'tooltip="Edit Interface"' in overrides
    assert 'toolbar_icon("settings")' in overrides

    assert "install_interface_share_icons(" in ui_init
    assert "install_script_editor_clear_icon(" in ui_init
    assert "install_toolbox_settings_icon(" in ui_init

    assert 'toolbar_icon("update")' in update_ui
