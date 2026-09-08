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


def test_update_channel_uses_right_click_context_menu():
    source = _read(
        "scripts/script_toolbox/ui/update_channels_ui.py"
    )

    assert "QtCore.Qt.CustomContextMenu" in source
    assert "customContextMenuRequested.connect" in source
    assert "_show_update_channel_menu" in source
    assert "mapToGlobal" in source
    assert "Right-click to change channel." in source

    assert "QToolButton.MenuButtonPopup" not in source
    assert "button.setMenu(" not in source
