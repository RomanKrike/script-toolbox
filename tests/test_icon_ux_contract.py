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


def test_icon_assets_are_packaged():
    icons_dir = os.path.join(
        ROOT,
        "scripts",
        "script_toolbox",
        "icons"
    )

    for name in (
        "cloud-download.svg",
        "cloud-upload.svg",
        "settings.svg",
    ):
        path = os.path.join(
            icons_dir,
            name
        )
        assert os.path.isfile(path)
        assert os.path.getsize(path) > 0


def test_icon_browse_and_toolbar_overrides_are_installed():
    hooks = _read(
        "scripts/script_toolbox/ui/icon_ux_hooks.py"
    )
    ui_init = _read(
        "scripts/script_toolbox/ui/__init__.py"
    )

    assert '"icon_path"' in hooks
    assert '"path"' in hooks
    assert "QFileDialog.getOpenFileName" in hooks
    assert "icons_directory()" in hooks

    assert 'toolbar_icon("delete")' in hooks
    assert '"cloud-download"' in hooks
    assert '"cloud-upload"' in hooks
    assert '"settings"' in hooks

    assert "install_property_icon_browse()" in ui_init
    assert "install_interface_share_icons(" in ui_init
    assert "install_script_editor_clear_icon(" in ui_init
    assert "install_toolbox_settings_icon(" in ui_init
