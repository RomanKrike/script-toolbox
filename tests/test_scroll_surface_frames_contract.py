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


def test_scroll_surface_frame_supports_all_scrollable_control_hosts():
    source = _read(
        "scripts/script_toolbox/ui/scroll_surface_frames.py"
    )

    assert 'frame.setObjectName("ScrollSurfaceFrame")' in source
    assert "border: 1px solid #151515;" in source
    assert "layout.setContentsMargins(1, 1, 1, 1)" in source
    assert "widget.setFrameShape(QtGui.QFrame.NoFrame)" in source
    assert "isinstance(parent, QtGui.QSplitter)" in source
    assert "isinstance(owner_layout, QtGui.QFormLayout)" in source


def test_runtime_list_field_uses_external_scroll_surface_frame():
    source = _read(
        "scripts/script_toolbox/ui/scroll_surface_frames.py"
    )
    style = _read(
        "scripts/script_toolbox/style/runtime_overrides.py"
    )

    assert 'registry.renderer_for("field")' in source
    assert "runtime_module.DisplayFieldList" in source
    assert "wrap_scroll_widget(control)" in source
    assert "QListWidget#RuntimeFieldList" in style
    runtime_rule = style.split(
        "QListWidget#RuntimeFieldList {",
        1
    )[1].split("}", 1)[0]
    assert "border: 0px;" in runtime_rule
    assert "border-radius: 0px;" in runtime_rule


def test_script_editor_frames_code_and_output_scroll_areas():
    source = _read(
        "scripts/script_toolbox/ui/scroll_surface_frames.py"
    )

    assert "self.editor_scroll_frame = wrap_scroll_widget(" in source
    assert 'getattr(self, "editor", None)' in source
    assert "self.output_scroll_frame = wrap_scroll_widget(" in source
    assert 'getattr(self, "output", None)' in source


def test_multiline_property_fields_use_external_frames():
    source = _read(
        "scripts/script_toolbox/ui/scroll_surface_frames.py"
    )

    assert "basic_module.MenuPropertyEditor" in source
    assert 'getattr(self, "items_edit", None)' in source
    assert "field_module.FieldPropertyEditor" in source
    assert 'getattr(self, "value", None)' in source


def test_ui_installs_unified_scroll_surface_contract():
    source = _read(
        "scripts/script_toolbox/ui/__init__.py"
    )

    assert "install_property_editor_scroll_frames()" in source
    assert "install_runtime_scroll_frames(" in source
    assert "install_script_editor_scroll_frames(" in source


def test_panel_scroll_areas_remain_frameless_by_design():
    main_window = _read(
        "scripts/script_toolbox/ui/main_window.py"
    )
    interface_editor = _read(
        "scripts/script_toolbox/ui/interface_editor.py"
    )
    stylesheet = _read(
        "scripts/script_toolbox/style/stylesheet.py"
    )

    assert 'self.scroll.setObjectName(\n            "ToolboxScroll"' in main_window
    assert 'self.property_scroll.setObjectName(\n            "PropertyScroll"' in interface_editor
    assert "QScrollArea {\n    border: 0px;" in stylesheet
