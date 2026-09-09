# -*- coding: utf-8 -*-

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_standard_single_line_inputs_share_one_geometry_contract():
    stylesheet = _read(
        "scripts/script_toolbox/style/stylesheet.py"
    )

    single_line_selector = """QLineEdit,
QComboBox,
QSpinBox,
QDoubleSpinBox {
    min-height: %(INPUT_MIN_HEIGHT)spx;
    padding: %(INPUT_PADDING_VERTICAL)spx %(INPUT_PADDING_HORIZONTAL)spx;
}"""
    assert single_line_selector in stylesheet

    # Multiline editors share border/focus styling, but must not inherit the
    # single-line fixed presentation height.
    assert "QPlainTextEdit {\n    min-height: %(INPUT_MIN_HEIGHT)spx;" not in stylesheet


def test_standard_buttons_share_chrome_without_overriding_role_owned_sizes():
    stylesheet = _read(
        "scripts/script_toolbox/style/stylesheet.py"
    )
    icon_button = _read(
        "scripts/script_toolbox/ui/icon_button.py"
    )
    runtime_renderers = _read(
        "scripts/script_toolbox/ui/runtime_renderers.py"
    )
    trigger_tabs = _read(
        "scripts/script_toolbox/ui/properties/trigger_tabs.py"
    )

    assert "QPushButton,\nQToolButton {" in stylesheet
    assert "border-radius: %(BORDER_RADIUS_PANEL)spx;" in stylesheet
    assert (
        "padding: %(BUTTON_PADDING_VERTICAL)spx "
        "%(BUTTON_PADDING_HORIZONTAL)spx;"
        in stylesheet
    )
    assert "QPushButton {\n    min-height: %(BUTTON_MIN_HEIGHT)spx;" in stylesheet

    # QToolButton size remains role-owned. Technical buttons use semantic
    # presets, runtime icons use user width/height, and Trigger glyph buttons
    # keep their Qt4 clipping contract until the Trigger-tab stage.
    assert "button.setFixedSize(" in icon_button
    assert 'width = int(item.get("width", 24))' in runtime_renderers
    assert 'height = int(item.get("height", 24))' in runtime_renderers
    assert "button.setFixedSize(16, 16)" in trigger_tabs


def test_search_and_icon_controls_keep_semantic_role_geometry():
    components = _read(
        "scripts/script_toolbox/style/components.py"
    )
    search = _read(
        "scripts/script_toolbox/ui/search_field.py"
    )
    icon_button = _read(
        "scripts/script_toolbox/ui/icon_button.py"
    )

    assert "min-height: %(SEARCH_FIELD_MIN_HEIGHT)spx;" in components
    assert "SEARCH_TEXT_MARGIN_LEFT" in search
    assert "SEARCH_TEXT_MARGIN_RIGHT" in search
    assert "ICON_BUTTON_COMPACT_SIZE" in icon_button
    assert "ICON_BUTTON_TOOLBAR_SIZE" in icon_button
    assert "ICON_BUTTON_HEADER_SIZE" in icon_button


def test_runtime_field_reuses_list_item_metrics_but_keeps_visible_rows_local():
    runtime_overrides = _read(
        "scripts/script_toolbox/style/runtime_overrides.py"
    )
    scroll_frames = _read(
        "scripts/script_toolbox/ui/scroll_surface_frames.py"
    )
    runtime = _read(
        "scripts/script_toolbox/ui/runtime.py"
    )

    for name in (
        "LIST_ITEM_MIN_HEIGHT",
        "LIST_ITEM_PADDING_VERTICAL",
        "LIST_ITEM_PADDING_HORIZONTAL",
    ):
        assert name in runtime_overrides
        assert name in scroll_frames

    assert "min-height: 20px;" not in runtime_overrides
    assert "padding: 3px 4px;" not in runtime_overrides
    assert "min-height: 20px;" not in scroll_frames
    assert "padding: 3px 4px;" not in scroll_frames

    # visible_rows controls the outer widget bound and is persisted model
    # behaviour. It deliberately remains separate from item-painting metrics.
    assert 'item.get("visible_rows", 4)' in runtime
    assert "row_height = max(" in runtime
    assert "self.visible_rows * row_height + 6" in runtime
    assert "LIST_ITEM_MIN_HEIGHT" not in runtime


def test_scroll_frame_pixel_contract_is_not_absorbed_into_standard_metrics():
    scroll_frames = _read(
        "scripts/script_toolbox/ui/scroll_surface_frames.py"
    )

    # Stage 5 owns these Maya/Qt4 border/inset pixels. Standard-control
    # cleanup must not silently fold them into generic metrics first.
    assert "border-radius: 2px;" in scroll_frames
    assert "vertical_inset = 2" in scroll_frames
    assert "layout.setContentsMargins(1, 1, 1, 1)" in scroll_frames
