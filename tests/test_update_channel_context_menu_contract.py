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


def test_update_channel_uses_direct_control_reference_only():
    source = _read(
        "scripts/script_toolbox/ui/update_channels_ui.py"
    )

    assert '"check_updates_button"' in source
    assert "_find_update_check_button" not in source
    assert "findChildren(" not in source
    assert '"TopBar"' not in source
    assert "self.check_updates_button = widget" not in source
    assert "button.toolTip()" not in source
    assert "tooltip.startswith(" not in source
