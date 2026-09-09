from pathlib import Path


def read(path):
    return Path(path).read_text(encoding="utf-8")


def write(path, text):
    Path(path).write_text(text, encoding="utf-8")


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise SystemExit("%s: expected 1 match, got %s" % (label, count))
    return text.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Shared scroll-surface compatibility geometry
# ---------------------------------------------------------------------------
metrics_path = "scripts/script_toolbox/style/metrics.py"
text = read(metrics_path)
text = replace_once(
    text,
    "SCROLLBAR_HANDLE_MARGIN = 2\n\n# Technical icon buttons",
    "SCROLLBAR_HANDLE_MARGIN = 2\n\n"
    "# Scroll surface compatibility geometry -------------------------------------\n"
    "# These values describe the external frame used around scrollable controls.\n"
    "# Keep the role separate from generic control radii because Maya/Qt4 needs\n"
    "# the border and child inset to remain an explicit compatibility contract.\n"
    "SCROLL_SURFACE_BORDER_WIDTH = 1\n"
    "SCROLL_SURFACE_CONTENT_INSET = 1\n"
    "SCROLL_SURFACE_BORDER_RADIUS = 2\n\n"
    "# Technical icon buttons",
    "scroll surface metrics",
)
text = replace_once(
    text,
    '    "SCROLLBAR_HANDLE_MARGIN",\n',
    '    "SCROLLBAR_HANDLE_MARGIN",\n'
    '    "SCROLL_SURFACE_BORDER_WIDTH",\n'
    '    "SCROLL_SURFACE_CONTENT_INSET",\n'
    '    "SCROLL_SURFACE_BORDER_RADIUS",\n',
    "scroll surface metric exports",
)
write(metrics_path, text)


# ---------------------------------------------------------------------------
# ScrollSurfaceFrame owns all border geometry in one place
# ---------------------------------------------------------------------------
source_path = "scripts/script_toolbox/ui/scroll_surface_frames.py"
text = read(source_path)
text = replace_once(
    text,
    "_INSTALLED_RUNTIME = False\n_INSTALLED_SCRIPT_EDITOR = False\n_INSTALLED_PROPERTIES = False\n",
    "_INSTALLED_RUNTIME = False\n"
    "_INSTALLED_INTERFACE_EDITOR = False\n"
    "_INSTALLED_SCRIPT_EDITOR = False\n"
    "_INSTALLED_PROPERTIES = False\n",
    "interface installer flag",
)
old_styles = '''_FRAME_STYLE = """
QFrame#ScrollSurfaceFrame {
    background-color: %(CONTROL_BG)s;
    border: 1px solid %(BORDER_DARK)s;
    border-radius: 2px;
}
""" % palette.__dict__

# Runtime Field should match the actual editor list/tree surface, not the
# surrounding EditorPane container. The list stays frameless because the
# external ScrollSurfaceFrame owns the visible outline in Maya/Qt4.
_RUNTIME_FIELD_FRAME_STYLE = """
QFrame#ScrollSurfaceFrame {
    background-color: %(LIST_BG)s;
    border: 1px solid %(BORDER_PRESSED)s;
    border-radius: 2px;
}
""" % palette.__dict__

_RUNTIME_FIELD_STYLE_VALUES = dict(palette.__dict__)
_RUNTIME_FIELD_STYLE_VALUES.update(vars(metrics))
'''
new_styles = '''# All ScrollSurfaceFrame border geometry is rendered from this one template.
# The colors vary by surface role, while border width/radius remain the same
# explicit Maya/Qt4 compatibility contract.
_SCROLL_SURFACE_STYLE_VALUES = dict(palette.__dict__)
_SCROLL_SURFACE_STYLE_VALUES.update(vars(metrics))

_FRAME_STYLE_TEMPLATE = """
QFrame#ScrollSurfaceFrame {
    background-color: %(background)s;
    border: %(SCROLL_SURFACE_BORDER_WIDTH)spx solid %(border)s;
    border-radius: %(SCROLL_SURFACE_BORDER_RADIUS)spx;
}
"""

# Runtime Field should match the actual editor list/tree surface, not the
# surrounding EditorPane container. The list stays frameless because the
# external ScrollSurfaceFrame owns the visible outline in Maya/Qt4.
'''
text = replace_once(text, old_styles, new_styles, "single frame style owner")
text = replace_once(
    text,
    '""" % _RUNTIME_FIELD_STYLE_VALUES\n\n_CHILD_STYLE',
    '""" % _SCROLL_SURFACE_STYLE_VALUES\n\n_CHILD_STYLE',
    "runtime list style values",
)
old_frame_style = '''def _frame_style(background, border):
    if (
        background == palette.CONTROL_BG and
        border == palette.BORDER_DARK
    ):
        return _FRAME_STYLE

    return """
QFrame#ScrollSurfaceFrame {
    background-color: %s;
    border: 1px solid %s;
    border-radius: 2px;
}
""" % (
        background,
        border
    )
'''
new_frame_style = '''def _frame_style(background, border):
    values = dict(_SCROLL_SURFACE_STYLE_VALUES)
    values.update({
        "background": background,
        "border": border,
    })
    return _FRAME_STYLE_TEMPLATE % values
'''
text = replace_once(text, old_frame_style, new_frame_style, "frame style function")
marker = '''def _fit_runtime_field_inside_frame(control, frame):
'''
helper = '''def _frame_vertical_inset(frame):
    """Return border + layout inset consumed inside a framed surface."""
    vertical_inset = metrics.SCROLL_SURFACE_BORDER_WIDTH * 2

    try:
        margins = frame.layout().contentsMargins()
        vertical_inset += int(margins.top())
        vertical_inset += int(margins.bottom())
    except Exception:
        vertical_inset += metrics.SCROLL_SURFACE_CONTENT_INSET * 2

    return vertical_inset


'''
text = replace_once(text, marker, helper + marker, "vertical inset helper")
old_fit = '''    # The runtime Field frame has a 1 px QSS border on both vertical edges.
    # Count it explicitly rather than relying on QFrame.frameWidth(), which is
    # not reliable for style-sheet borders on older Maya/Qt4 builds.
    vertical_inset = 2

    try:
        margins = frame.layout().contentsMargins()
        vertical_inset += int(margins.top())
        vertical_inset += int(margins.bottom())
    except Exception:
        # _make_frame currently installs 1 px top/bottom layout margins.
        vertical_inset += 2

    inner_height = max(
        1,
        minimum_height - vertical_inset
    )
'''
new_fit = '''    # Do not rely on QFrame.frameWidth(): QSS borders are unreliable there on
    # older Maya/Qt4 builds. The explicit ScrollSurfaceFrame contract owns the
    # border width and layout inset used to derive the child viewport height.
    inner_height = max(
        1,
        minimum_height - _frame_vertical_inset(frame)
    )
'''
text = replace_once(text, old_fit, new_fit, "runtime field inset math")
old_margins = '''    layout = QtGui.QVBoxLayout(frame)
    layout.setContentsMargins(1, 1, 1, 1)
    layout.setSpacing(0)
'''
new_margins = '''    layout = QtGui.QVBoxLayout(frame)
    inset = metrics.SCROLL_SURFACE_CONTENT_INSET
    layout.setContentsMargins(
        inset,
        inset,
        inset,
        inset
    )
    layout.setSpacing(0)
'''
text = replace_once(text, old_margins, new_margins, "frame layout inset")
old_runtime_restyle = '''            if frame is not None:
                _fit_runtime_field_inside_frame(
                    control,
                    frame
                )
                frame.setStyleSheet(
                    _RUNTIME_FIELD_FRAME_STYLE
                )
'''
new_runtime_restyle = '''            if frame is not None:
                _fit_runtime_field_inside_frame(
                    control,
                    frame
                )
'''
text = replace_once(text, old_runtime_restyle, new_runtime_restyle, "runtime duplicate frame style")
script_installer = '''def install_script_editor_scroll_frames(script_editor_class):
'''
interface_installer = '''def install_interface_editor_scroll_frames(interface_editor_class):
    """Frame Palette and Existing Interface trees with the shared contract."""
    global _INSTALLED_INTERFACE_EDITOR
    if _INSTALLED_INTERFACE_EDITOR:
        return

    original_build_ui = interface_editor_class.build_ui

    def build_ui(self):
        original_build_ui(self)
        self.palette_scroll_frame = wrap_scroll_widget(
            getattr(self, "palette", None),
            background=palette.LIST_BG,
            border=palette.BORDER_SOFT
        )
        self.tree_scroll_frame = wrap_scroll_widget(
            getattr(self, "tree", None),
            background=palette.LIST_BG,
            border=palette.BORDER_PRESSED
        )

    interface_editor_class.build_ui = build_ui
    _INSTALLED_INTERFACE_EDITOR = True


'''
text = replace_once(text, script_installer, interface_installer + script_installer, "interface frame installer")
text = replace_once(
    text,
    '    "install_runtime_scroll_frames",\n    "install_script_editor_scroll_frames",\n',
    '    "install_runtime_scroll_frames",\n'
    '    "install_interface_editor_scroll_frames",\n'
    '    "install_script_editor_scroll_frames",\n',
    "interface installer export",
)
write(source_path, text)


# ---------------------------------------------------------------------------
# Install the same frame contract on editor Palette / Existing trees
# ---------------------------------------------------------------------------
ui_path = "scripts/script_toolbox/ui/__init__.py"
text = read(ui_path)
text = replace_once(
    text,
    "from .scroll_surface_frames import install_property_editor_scroll_frames\n",
    "from .scroll_surface_frames import install_interface_editor_scroll_frames\n"
    "from .scroll_surface_frames import install_property_editor_scroll_frames\n",
    "interface frame import",
)
text = replace_once(
    text,
    "InterfaceEditor = build_interface_editor_class(\n"
    "    _interface_editor_module.InterfaceEditor,\n"
    "    controller_class=LayoutEditorDocumentController,\n"
    "    layout_support=True\n"
    ")\n"
    "install_property_editor_scroll_frames()\n",
    "InterfaceEditor = build_interface_editor_class(\n"
    "    _interface_editor_module.InterfaceEditor,\n"
    "    controller_class=LayoutEditorDocumentController,\n"
    "    layout_support=True\n"
    ")\n"
    "install_interface_editor_scroll_frames(\n"
    "    InterfaceEditor\n"
    ")\n"
    "install_property_editor_scroll_frames()\n",
    "interface frame install",
)
write(ui_path, text)


# ---------------------------------------------------------------------------
# Contract tests
# ---------------------------------------------------------------------------
scroll_test_path = "tests/test_scroll_surface_frames_contract.py"
scroll_test = r'''# -*- coding: utf-8 -*-

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


def test_scroll_surface_geometry_has_one_explicit_compatibility_contract():
    metrics = _read(
        "scripts/script_toolbox/style/metrics.py"
    )
    source = _read(
        "scripts/script_toolbox/ui/scroll_surface_frames.py"
    )

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
    assert "_RUNTIME_FIELD_FRAME_STYLE" not in source
    assert "border-radius: 2px;" not in source
    assert "border: 1px solid" not in source


def test_scroll_surface_frame_supports_all_scrollable_control_hosts():
    source = _read(
        "scripts/script_toolbox/ui/scroll_surface_frames.py"
    )

    assert 'frame.setObjectName("ScrollSurfaceFrame")' in source
    assert "from ..style import metrics" in source
    assert "from ..style import palette" in source
    assert "inset = metrics.SCROLL_SURFACE_CONTENT_INSET" in source
    assert "widget.setFrameShape(QtGui.QFrame.NoFrame)" in source
    assert "isinstance(parent, QtGui.QSplitter)" in source
    assert "isinstance(owner_layout, QtGui.QFormLayout)" in source


def test_scroll_surface_theme_colors_use_shared_palette():
    source = _read(
        "scripts/script_toolbox/ui/scroll_surface_frames.py"
    )

    assert "palette.CONTROL_BG" in source
    assert "palette.BORDER_DARK" in source
    assert "palette.LIST_BG" in source
    assert "palette.BORDER_SOFT" in source
    assert "palette.BORDER_PRESSED" in source
    assert "palette.TEXT_LIST" in source
    assert "palette.SELECTION_BG" in source
    assert "palette.SELECTION_TEXT" in source
    assert re.search(r"#[0-9a-fA-F]{6}\b", source) is None


def test_scroll_surface_frame_preserves_original_outer_constraints_without_growth():
    source = _read(
        "scripts/script_toolbox/ui/scroll_surface_frames.py"
    )

    # The wrapper takes over the old border but must keep the same public
    # min/max bounds. Border + inset are consumed from the child viewport.
    assert "frame.setMinimumHeight(minimum_height)" in source
    assert "frame.setMaximumHeight(maximum_height)" in source
    assert "frame.setMinimumWidth(minimum_width)" in source
    assert "frame.setMaximumWidth(maximum_width)" in source

    for forbidden in (
        "minimum_height +",
        "maximum_height +",
        "minimum_width +",
        "maximum_width +",
    ):
        assert forbidden not in source

    assert "minimum_height - _frame_vertical_inset(frame)" in source


def test_runtime_field_consumes_explicit_frame_border_and_layout_insets():
    source = _read(
        "scripts/script_toolbox/ui/scroll_surface_frames.py"
    )

    assert "def _frame_vertical_inset(frame):" in source
    assert "metrics.SCROLL_SURFACE_BORDER_WIDTH * 2" in source
    assert "margins = frame.layout().contentsMargins()" in source
    assert "vertical_inset += int(margins.top())" in source
    assert "vertical_inset += int(margins.bottom())" in source
    assert "metrics.SCROLL_SURFACE_CONTENT_INSET * 2" in source
    assert "def _fit_runtime_field_inside_frame(control, frame):" in source
    assert "minimum_height != maximum_height" in source
    assert "control.setMinimumHeight(inner_height)" in source
    assert "control.setMaximumHeight(inner_height)" in source
    assert "vertical_inset = 2" not in source


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

    editor_list_rule = base_style.split(
        "QListWidget,\nQTreeWidget {",
        1
    )[1].split("}", 1)[0]
    assert "background-color: %(LIST_BG)s;" in editor_list_rule
    assert "border: 1px solid %(BORDER_PRESSED)s;" in editor_list_rule
    assert "border-radius: %(BORDER_RADIUS_CONTROL)spx;" in editor_list_rule

    # Runtime Field asks the same wrapper for the list surface. The frame's
    # geometry comes from the one shared ScrollSurfaceFrame template.
    assert "background=palette.LIST_BG" in source
    assert "border=palette.BORDER_PRESSED" in source
    assert "_RUNTIME_FIELD_FRAME_STYLE" not in source

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

    assert "_RUNTIME_FIELD_LIST_STYLE" in source
    assert "control.setStyleSheet(" in source
    assert "QtGui.QPalette.Base" in source
    assert "QtGui.QPalette.AlternateBase" in source
    assert "QtGui.QColor(palette.LIST_BG)" in source
    assert "QtGui.QPalette.Highlight" in source
    assert "QtGui.QColor(palette.SELECTION_BG)" in source
    assert "QtGui.QColor(palette.SELECTION_TEXT)" in source
    assert "viewport.setAutoFillBackground(True)" in source


def test_interface_editor_palette_and_tree_use_scroll_surface_contract():
    source = _read(
        "scripts/script_toolbox/ui/scroll_surface_frames.py"
    )

    assert "def install_interface_editor_scroll_frames(" in source
    assert "self.palette_scroll_frame = wrap_scroll_widget(" in source
    assert 'getattr(self, "palette", None)' in source
    assert "border=palette.BORDER_SOFT" in source
    assert "self.tree_scroll_frame = wrap_scroll_widget(" in source
    assert 'getattr(self, "tree", None)' in source
    assert "border=palette.BORDER_PRESSED" in source


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

    assert "install_interface_editor_scroll_frames(" in source
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
'''
write(scroll_test_path, scroll_test)

standard_test_path = "tests/test_standard_control_geometry_contract.py"
text = read(standard_test_path)
old_test = '''def test_scroll_frame_pixel_contract_is_not_absorbed_into_standard_metrics():
    scroll_frames = _read(
        "scripts/script_toolbox/ui/scroll_surface_frames.py"
    )

    # Stage 5 owns these Maya/Qt4 border/inset pixels. Standard-control
    # cleanup must not silently fold them into generic metrics first.
    assert "border-radius: 2px;" in scroll_frames
    assert "vertical_inset = 2" in scroll_frames
    assert "layout.setContentsMargins(1, 1, 1, 1)" in scroll_frames
'''
new_test = '''def test_scroll_frame_pixel_contract_is_owned_by_scroll_surface_metrics():
    metrics = _read(
        "scripts/script_toolbox/style/metrics.py"
    )
    scroll_frames = _read(
        "scripts/script_toolbox/ui/scroll_surface_frames.py"
    )

    # Stage 5 now owns these Maya/Qt4 pixels explicitly without folding them
    # into the generic button/input geometry roles.
    assert "SCROLL_SURFACE_BORDER_WIDTH = 1" in metrics
    assert "SCROLL_SURFACE_CONTENT_INSET = 1" in metrics
    assert "SCROLL_SURFACE_BORDER_RADIUS = 2" in metrics
    assert "metrics.SCROLL_SURFACE_BORDER_WIDTH * 2" in scroll_frames
    assert "metrics.SCROLL_SURFACE_CONTENT_INSET" in scroll_frames
    assert "vertical_inset = 2" not in scroll_frames
    assert "layout.setContentsMargins(1, 1, 1, 1)" not in scroll_frames
'''
text = replace_once(text, old_test, new_test, "standard-control stage 5 handoff test")
write(standard_test_path, text)
