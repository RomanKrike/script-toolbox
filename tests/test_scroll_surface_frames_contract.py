# -*- coding: utf-8 -*-

import os
import re


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
    assert "from ..style import palette" in source
    assert "border: 1px solid %(BORDER_DARK)s;" in source
    assert "layout.setContentsMargins(1, 1, 1, 1)" in source
    assert "widget.setFrameShape(QtGui.QFrame.NoFrame)" in source
    assert "isinstance(parent, QtGui.QSplitter)" in source
    assert "isinstance(owner_layout, QtGui.QFormLayout)" in source


def test_scroll_surface_theme_colors_use_shared_palette():
    source = _read(
        "scripts/script_toolbox/ui/scroll_surface_frames.py"
    )

    assert "%(CONTROL_BG)s" in source
    assert "%(BORDER_DARK)s" in source
    assert "%(LIST_BG)s" in source
    assert "%(BORDER_PRESSED)s" in source
    assert "%(TEXT_LIST)s" in source
    assert "%(SELECTION_BG)s" in source
    assert "%(SELECTION_TEXT)s" in source
    assert "palette.CONTROL_BG" in source
    assert "palette.BORDER_DARK" in source
    assert "palette.LIST_BG" in source
    assert "palette.BORDER_PRESSED" in source
    assert re.search(r"#[0-9a-fA-F]{6}\b", source) is None


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


def test_runtime_field_consumes_frame_border_and_layout_insets():
    source = _read(
        "scripts/script_toolbox/ui/scroll_surface_frames.py"
    )

    assert "def _fit_runtime_field_inside_frame(control, frame):" in source
    assert "minimum_height != maximum_height" in source
    assert "vertical_inset = 2" in source
    assert "margins = frame.layout().contentsMargins()" in source
    assert "vertical_inset += int(margins.top())" in source
    assert "vertical_inset += int(margins.bottom())" in source
    assert "minimum_height - vertical_inset" in source
    assert "minimum_height - 2" not in source
    assert "control.setMinimumHeight(inner_height)" in source
    assert "control.setMaximumHeight(inner_height)" in source
    assert "_fit_runtime_field_inside_frame(" in source


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
    assert "_apply_runtime_field_surface(control)" in source

    # The requested visual target is the editor's QListWidget/QTreeWidget
    # surface (palette + Existing Interface), not the surrounding EditorPane.
    editor_list_rule = base_style.split(
        "QListWidget,\nQTreeWidget {",
        1
    )[1].split("}", 1)[0]

    frame_rule = source.split(
        "_RUNTIME_FIELD_FRAME_STYLE =",
        1
    )[1].split('"""', 2)[1]

    for token in (
        "background-color: %(LIST_BG)s;",
        "border: 1px solid %(BORDER_PRESSED)s;",
    ):
        assert token in editor_list_rule
        assert token in frame_rule

    # Base theme geometry is tokenized, while the external Maya/Qt4 frame
    # keeps its explicit pixel contract separate from the design-system layer.
    assert "border-radius: %(BORDER_RADIUS_CONTROL)spx;" in editor_list_rule
    assert "border-radius: 2px;" in frame_rule

    assert "background=palette.LIST_BG" in source
    assert "border=palette.BORDER_PRESSED" in source

    runtime_rule = style.split(
        "QListWidget#RuntimeFieldList {{",
        1
    )[1].split("}}", 1)[0]
    assert "background-color: {list_bg};" in runtime_rule
    assert "alternate-background-color: {list_bg};" in runtime_rule
    assert "border: 0px;" in runtime_rule
    assert "border-radius: 0px;" in runtime_rule
    assert "outline: 0px;" in runtime_rule

    item_rule = style.split(
        "QListWidget#RuntimeFieldList::item {{",
        1
    )[1].split("}}", 1)[0]
    assert "border: 0px;" in item_rule
    assert "border-bottom" not in item_rule

    assert "self.setAlternatingRowColors(False)" in runtime
    assert "QListWidget#RuntimeFieldList::item:hover" not in style

    selected_rule = style.split(
        "QListWidget#RuntimeFieldList::item:selected {{",
        1
    )[1].split("}}", 1)[0]
    assert "background-color: {selection_bg};" in selected_rule
    assert "color: {selection_text};" in selected_rule

    # Maya can keep the reparented QListWidget viewport on the host palette.
    # The runtime hook therefore applies the same surface directly and carries
    # a QPalette fallback for the background and orange selection.
    assert "_RUNTIME_FIELD_LIST_STYLE" in source
    assert "control.setStyleSheet(" in source
    assert "QtGui.QPalette.Base" in source
    assert "QtGui.QPalette.AlternateBase" in source
    assert "QtGui.QColor(palette.LIST_BG)" in source
    assert "QtGui.QPalette.Highlight" in source
    assert "QtGui.QColor(palette.SELECTION_BG)" in source
    assert "QtGui.QColor(palette.SELECTION_TEXT)" in source
    assert "viewport.setAutoFillBackground(True)" in source


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
