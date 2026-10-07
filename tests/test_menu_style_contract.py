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


def test_context_menus_keep_visible_group_separators():
    source = _read(
        "scripts/script_toolbox/style/components.py"
    )

    assert "QMenu::separator" in source
    assert "background-color: %(SEPARATOR)s;" in source
    assert "height: 1px;" in source


def test_context_menus_use_dark_plugin_palette():
    source = _read(
        "scripts/script_toolbox/style/components.py"
    )

    assert "QMenu {" in source
    assert "background-color: %(PANEL_BG)s;" in source
    assert "color: %(TEXT_PRIMARY)s;" in source
    assert "QMenu::item {" in source
    assert "QMenu::item:selected" in source
    assert "background-color: %(ICON_BUTTON_HOVER_BG)s;" in source
    assert "QMenu::item:disabled" in source


def test_common_menu_bar_and_status_use_dark_plugin_palette():
    source = _read(
        "scripts/script_toolbox/style/components.py"
    )

    assert "QMenuBar#ToolboxMenuBar {" in source
    assert "background-color: %(CONTROL_BG)s;" in source
    assert "QMenuBar#ToolboxMenuBar::item:selected" in source
    assert "background-color: %(ICON_BUTTON_HOVER_BG)s;" in source
    assert "QStatusBar#ToolboxStatusBar {" in source
    assert "background-color: %(STATUS_BG)s;" in source
    assert "QToolButton#StatusAction" in source
