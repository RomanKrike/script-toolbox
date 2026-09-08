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


def test_parameter_description_uses_dialog_dark_surface():
    style_source = _read(
        "scripts/script_toolbox/style/runtime_overrides.py"
    )
    palette_source = _read(
        "scripts/script_toolbox/ui/property_pane_style.py"
    )
    ui_source = _read(
        "scripts/script_toolbox/ui/__init__.py"
    )

    assert "QWidget#PropertyPane" in style_source
    assert "QScrollArea#PropertyScroll" in style_source
    assert "QWidget#PropertyViewport" in style_source
    assert "QWidget#PropertyHost" in style_source
    assert "QWidget#PropertyEditor" in style_source
    assert "background-color: #292929;" in style_source

    assert 'PROPERTY_PANE_BACKGROUND = "#292929"' in palette_source
    assert "QtGui.QPalette.Window" in palette_source
    assert "QtGui.QPalette.Base" in palette_source
    assert 'pane.setObjectName("PropertyPane")' in palette_source
    assert "install_property_pane_style(" in ui_source
