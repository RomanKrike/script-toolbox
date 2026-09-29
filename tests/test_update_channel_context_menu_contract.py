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


def test_update_channel_moves_into_shared_settings_menu():
    source = _read(
        "scripts/script_toolbox/ui/update_channels_ui.py"
    )

    assert '"settings_menu"' in source
    assert '"Update Channel"' in source
    assert '"Stable"' in source
    assert '"Development"' in source
    assert "action.setCheckable(" in source
    assert "menu.setStyleSheet(" in source
    assert "STYLE" in source

    assert "QtCore.Qt.CustomContextMenu" not in source
    assert "customContextMenuRequested.connect" not in source
    assert "check_updates_button" not in source
    assert "_update_channel_button" not in source
    assert "mapToGlobal" not in source
