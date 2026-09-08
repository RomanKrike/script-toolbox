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


def test_scroll_surface_frame_preserves_original_outer_constraints():
    source = _read(
        "scripts/script_toolbox/ui/scroll_surface_frames.py"
    )

    assert "frame.setMinimumHeight(minimum_height)" in source
    assert "frame.setMaximumHeight(maximum_height)" in source
    assert "frame.setMinimumWidth(minimum_width)" in source
    assert "frame.setMaximumWidth(maximum_width)" in source
    assert "minimum_height + 2" not in source
    assert "maximum_height + 2" not in source
    assert "minimum_width + 2" not in source
    assert "maximum_width + 2" not in source


def test_runtime_list_field_uses_plain_editor_surface_contract():
    source = _read(
        "scripts/script_toolbox/ui/scroll_surface_frames.py"
    )
    runtime = _read(
        "scripts/script_toolbox/ui/runtime.py"
    )
    style = _read(
        "scripts/script_toolbox/style/runtime_overrides.py"
    )
    base_style = _read(
        "scripts/script_toolbox/style/stylesheet.py"
    )

    assert 'registry.renderer_for("field")' in source
    assert "runtime_module.DisplayFieldList" in source
    assert 'background="#303030"' in source
    assert 'border="#1b1b1b"' in source
    assert "_RUNTIME_FIELD_FRAME_STYLE" in source
    assert "border-radius: 3px;" in source

    editor_rule = base_style.split(
        "QWidget#EditorPane {",
        1
    )[1].split("}", 1)[0]
    for token in (
        "background-color: #303030;",
        "border: 1px solid #1b1b1b;",
        "border-radius: 3px;",
    ):
        assert token in editor_rule
        assert token in source

    runtime_rule = style.split(
        "QListWidget#RuntimeFieldList {",
        1
    )[1].split("}", 1)[0]
    assert "background-color: #242424;" in runtime_rule
    assert "alternate-background-color: #242424;" in runtime_rule
    assert "border: 0px;" in runtime_rule
    assert "border-radius: 0px;" in runtime_rule
    assert "outline: 0px;" in runtime_rule

    item_rule = style.split(
        "QListWidget#RuntimeFieldList::item {",
        1
    )[1].split("}", 1)[0]
    assert "border: 0px;" in item_rule
    assert "border-bottom" not in item_rule

    assert "self.setAlternatingRowColors(False)" in runtime
    assert "QListWidget#RuntimeFieldList::item:hover" not in style

    selected_rule = style.split(
        "QListWidget#RuntimeFieldList::item:selected {",
        1
    )[1].split("}", 1)[0]
    assert "background-color: #68462c;" in selected_rule
    assert "color: #ffffff;" in selected_rule


def test_runtime_folder_pane_override_is_removed():
    style = _read(
        "scripts/script_toolbox/style/runtime_overrides.py"
    )

    assert 'QFrame#RuntimeFolder[folderType="collapsible"],' not in style
    assert "RuntimePane" not in style
    assert "RuntimePaneHost" not in style


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
