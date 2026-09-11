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


def test_parameter_description_uses_shared_dialog_surface():
    palette_source = _read(
        "scripts/script_toolbox/style/palette.py"
    )
    base_style_source = _read(
        "scripts/script_toolbox/style/stylesheet.py"
    )
    style_source = _read(
        "scripts/script_toolbox/style/runtime_overrides.py"
    )
    pane_source = _read(
        "scripts/script_toolbox/ui/property_pane_style.py"
    )
    editor_source = _read(
        "scripts/script_toolbox/ui/interface_editor.py"
    )
    search_source = _read(
        "scripts/script_toolbox/ui/editor_search.py"
    )
    adapter_source = _read(
        "scripts/script_toolbox/ui/editor_document_adapter.py"
    )
    property_source = _read(
        "scripts/script_toolbox/ui/properties/base.py"
    )
    ui_source = _read(
        "scripts/script_toolbox/ui/__init__.py"
    )

    assert 'WINDOW_BG = "#292929"' in palette_source

    base_rule = base_style_source.split(
        "QScrollArea#PropertyScroll,",
        1
    )[1].split("}", 1)[0]
    assert "background-color: %(WINDOW_BG)s;" in base_rule

    assert "QWidget#PropertyPane" in style_source
    assert "QScrollArea#PropertyScroll" in style_source
    assert "QWidget#PropertyViewport" in style_source
    assert "QWidget#PropertyHost" in style_source
    assert "QWidget#PropertyEditor" in style_source
    assert "background-color: {window_bg};" in style_source
    assert "window_bg=WINDOW_BG" in style_source

    assert "from ..style.palette import WINDOW_BG" in pane_source
    assert "PROPERTY_PANE_BACKGROUND = WINDOW_BG" in pane_source
    assert "QtGui.QPalette.Window" in pane_source
    assert "QtGui.QPalette.Base" in pane_source
    assert 'pane.setObjectName("PropertyPane")' in pane_source
    assert "def apply_property_pane_style(editor):" in pane_source
    assert "apply_property_pane_style(editor)" in search_source
    assert "apply_editor_presentation(self)" in adapter_source
    assert "install_property_pane_style(" not in ui_source

    assert "from ..style.palette import WINDOW_BG" in editor_source
    assert "QtGui.QColor(WINDOW_BG)" in editor_source
    assert "from ...style.palette import WINDOW_BG" in property_source
    assert "QtGui.QColor(WINDOW_BG)" in property_source
    assert ".__init__ =" not in pane_source


def test_runtime_field_surface_uses_shared_palette_tokens():
    palette_source = _read(
        "scripts/script_toolbox/style/palette.py"
    )
    style_source = _read(
        "scripts/script_toolbox/style/runtime_overrides.py"
    )

    assert 'LIST_BG = "#242424"' in palette_source
    assert 'SEPARATOR = "#414346"' in palette_source
    assert 'SELECTION_BG = "#68462c"' in palette_source
    assert "background-color: {list_bg};" in style_source
    assert "border-top: 1px solid {separator};" in style_source
    assert "background-color: {selection_bg};" in style_source
