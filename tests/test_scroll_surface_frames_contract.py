# -*- coding: utf-8 -*-

import os
import re


ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


def _read(relative_path):
    path = os.path.join(ROOT, *relative_path.split("/"))
    with open(path, "r") as handle:
        return handle.read()


def test_scroll_surface_geometry_has_one_explicit_contract():
    metrics = _read("scripts/script_toolbox/style/metrics.py")
    source = _read("scripts/script_toolbox/ui/scroll_surface_frames.py")

    for definition in (
        "SCROLL_SURFACE_BORDER_WIDTH = 1",
        "SCROLL_SURFACE_CONTENT_INSET = 1",
        "SCROLL_SURFACE_BORDER_RADIUS = 2",
    ):
        assert definition in metrics

    assert source.count("QFrame#ScrollSurfaceFrame {") == 1
    assert "_FRAME_STYLE_TEMPLATE" in source
    assert "%(SCROLL_SURFACE_BORDER_WIDTH)spx solid %(border)s" in source
    assert "%(SCROLL_SURFACE_BORDER_RADIUS)spx" in source
    assert "border-radius: 2px;" not in source
    assert "border: 1px solid" not in source


def test_scroll_surface_frame_supports_layout_host_types():
    source = _read("scripts/script_toolbox/ui/scroll_surface_frames.py")

    assert 'frame.setObjectName("ScrollSurfaceFrame")' in source
    assert "from ..style import metrics" in source
    assert "from ..style import palette" in source
    assert "widget.setFrameShape(QtGui.QFrame.NoFrame)" in source
    assert "isinstance(parent, QtGui.QSplitter)" in source
    assert "isinstance(owner_layout, QtGui.QFormLayout)" in source


def test_scroll_surface_theme_colors_use_shared_palette():
    source = _read("scripts/script_toolbox/ui/scroll_surface_frames.py")

    for token in (
        "palette.CONTROL_BG",
        "palette.BORDER_DARK",
        "palette.LIST_BG",
        "palette.BORDER_PRESSED",
        "palette.TEXT_LIST",
        "palette.SELECTION_BG",
        "palette.SELECTION_TEXT",
    ):
        assert token in source
    assert re.search(r"#[0-9a-fA-F]{6}\b", source) is None


def test_scroll_surface_frame_preserves_outer_constraints():
    source = _read("scripts/script_toolbox/ui/scroll_surface_frames.py")

    for token in (
        "frame.setMinimumHeight(minimum_height)",
        "frame.setMaximumHeight(maximum_height)",
        "frame.setMinimumWidth(minimum_width)",
        "frame.setMaximumWidth(maximum_width)",
        "minimum_height - _frame_vertical_inset(frame)",
    ):
        assert token in source

    for forbidden in (
        "minimum_height +",
        "maximum_height +",
        "minimum_width +",
        "maximum_width +",
    ):
        assert forbidden not in source


def test_runtime_field_consumes_frame_insets():
    source = _read("scripts/script_toolbox/ui/scroll_surface_frames.py")

    for token in (
        "def _frame_vertical_inset(frame):",
        "metrics.SCROLL_SURFACE_BORDER_WIDTH * 2",
        "margins = frame.layout().contentsMargins()",
        "def _fit_runtime_field_inside_frame(control, frame):",
        "control.setMinimumHeight(inner_height)",
        "control.setMaximumHeight(inner_height)",
    ):
        assert token in source
    assert "vertical_inset = 2" not in source


def test_runtime_list_field_uses_editor_surface_contract():
    source = _read("scripts/script_toolbox/ui/scroll_surface_frames.py")
    runtime = _read("scripts/script_toolbox/ui/runtime.py")
    style = _read("scripts/script_toolbox/style/runtime_overrides.py")
    base_style = _read("scripts/script_toolbox/style/stylesheet.py")

    assert 'registry.renderer_for("field")' in source
    assert "runtime_module.DisplayFieldList" in source
    assert "_apply_runtime_field_surface(control)" in source
    assert "background-color: %(LIST_BG)s;" in base_style
    assert "border: 1px solid %(BORDER_PRESSED)s;" in base_style
    assert "background=palette.LIST_BG" in source
    assert "border=palette.BORDER_PRESSED" in source
    assert "border: 0px;" in style
    assert "outline: 0px;" in style
    assert "self.setAlternatingRowColors(False)" in runtime
    assert "QListWidget#RuntimeFieldList::item:hover" not in style


def test_editor_palette_tree_and_script_editor_use_shared_wrapper():
    editor_frames = _read("scripts/script_toolbox/ui/editor_scroll_frames.py")
    frames = _read("scripts/script_toolbox/ui/scroll_surface_frames.py")

    assert "from .scroll_surface_frames import wrap_scroll_widget" in editor_frames
    assert 'getattr(editor, "palette", None)' in editor_frames
    assert 'getattr(editor, "tree", None)' in editor_frames
    assert editor_frames.count("wrap_scroll_widget(") >= 2
    assert "self.editor_scroll_frame = wrap_scroll_widget(" in frames
    assert "self.output_scroll_frame = wrap_scroll_widget(" in frames


def test_runtime_folder_pane_override_is_removed():
    style = _read("scripts/script_toolbox/style/runtime_overrides.py")

    assert 'QFrame#RuntimeFolder[folderType="collapsible"],' not in style
    assert "RuntimePane" not in style
    assert "RuntimePaneHost" not in style


def test_multiline_property_fields_use_external_frames():
    source = _read("scripts/script_toolbox/ui/scroll_surface_frames.py")

    assert "basic_module.MenuPropertyEditor" in source
    assert 'getattr(self, "items_edit", None)' in source
    assert "field_module.FieldPropertyEditor" in source
    assert 'getattr(self, "value", None)' in source


def test_ui_installs_unified_scroll_surface_contract():
    ui_source = _read("scripts/script_toolbox/ui/__init__.py")
    editor_search = _read("scripts/script_toolbox/ui/editor_search.py")

    assert "install_property_editor_scroll_frames()" in ui_source
    assert "install_runtime_scroll_frames(" in ui_source
    assert "install_script_editor_scroll_frames(" in ui_source
    assert "install_interface_editor_scroll_frames(editor)" in editor_search


def test_panel_scroll_areas_remain_frameless_by_design():
    main_window = _read("scripts/script_toolbox/ui/main_window.py")
    interface_editor = _read("scripts/script_toolbox/ui/interface_editor.py")
    stylesheet = _read("scripts/script_toolbox/style/stylesheet.py")

    assert 'self.scroll.setObjectName("ToolboxScroll")' in main_window
    assert '"PropertyScroll"' in interface_editor
    assert "QScrollArea {\n    border: 0px;" in stylesheet
