# -*- coding: utf-8 -*-

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_inspector_section_geometry_uses_shared_metrics_and_helpers():
    metrics = _read("scripts/script_toolbox/style/metrics.py")
    helpers = _read("scripts/script_toolbox/ui/layout_helpers.py")
    base = _read("scripts/script_toolbox/ui/properties/base.py")
    sections = _read("scripts/script_toolbox/ui/properties/sections.py")

    for definition in (
        "PROPERTY_EDITOR_SPACING = 8",
        "PROPERTY_FORM_HORIZONTAL_SPACING = 8",
        "PROPERTY_FORM_VERTICAL_SPACING = 6",
        "PROPERTY_GROUP_MARGINS = (7, 7, 7, 7)",
        "PROPERTY_GROUP_HORIZONTAL_SPACING = 8",
        "PROPERTY_GROUP_VERTICAL_SPACING = 5",
    ):
        assert definition in metrics

    assert "def configure_property_form(form):" in helpers
    assert "def configure_property_group_form(form):" in helpers
    assert "from ...style.metrics import PROPERTY_EDITOR_SPACING" in base
    assert "setSpacing(PROPERTY_EDITOR_SPACING)" in base
    assert "from ...style.metrics import PROPERTY_GROUP_MARGINS" in sections
    assert "configure_property_form(self.form)" in sections
    assert "margins=PROPERTY_GROUP_MARGINS" in sections


def test_numeric_value_rows_use_shared_inline_layout_geometry():
    metrics = _read("scripts/script_toolbox/style/metrics.py")
    helpers = _read("scripts/script_toolbox/ui/layout_helpers.py")
    basic = _read("scripts/script_toolbox/ui/properties/basic.py")

    assert "MARGINS_NONE = (0, 0, 0, 0)" in metrics
    assert "INLINE_CONTROL_SPACING = 4" in metrics
    assert "def configure_inline_layout(" in helpers
    assert basic.count("configure_inline_layout(values_layout)") == 1
    assert "values_layout.setContentsMargins(0, 0, 0, 0)" not in basic
    assert "values_layout.setSpacing(4)" not in basic


def test_integer_and_float_share_numeric_property_editor_base():
    basic = _read("scripts/script_toolbox/ui/properties/basic.py")

    assert "class NumericPropertyEditorBase(ValuePropertyEditorBase):" in basic
    assert "class IntegerPropertyEditor(NumericPropertyEditorBase):" in basic
    assert "class FloatPropertyEditor(NumericPropertyEditorBase):" in basic
    assert "SPINBOX_CLASS = QtGui.QSpinBox" in basic
    assert "SPINBOX_CLASS = QtGui.QDoubleSpinBox" in basic
    assert "VALUE_DEFAULT = 0" in basic
    assert "VALUE_DEFAULT = 0.0" in basic
    assert "DECIMALS_DEFAULT = 3" in basic


def test_action_button_and_toggle_button_appearance_are_split():
    button = _read("scripts/script_toolbox/ui/properties/button.py")
    toggle = _read("scripts/script_toolbox/ui/properties/toggle_button.py")
    sections = _read("scripts/script_toolbox/ui/properties/sections.py")

    assert "section = self.appearance_section" in button
    assert 'section.addRow("Icon", self.icon_path)' in button
    assert 'section.addRow("Color", self.color_button)' in button
    assert '"ON Label"' not in button
    assert '"OFF Color"' not in button
    assert "state_get_script" not in button

    assert '"ON Label"' in toggle
    assert '"OFF Label"' in toggle
    assert '"ON Color"' in toggle
    assert '"OFF Color"' in toggle
    assert '"Get State"' in toggle
    assert '"Turn ON"' in toggle
    assert '"Turn OFF"' in toggle

    assert "configure_property_form(self.form)" in sections
    assert "margins=PROPERTY_GROUP_MARGINS" in sections


def test_trigger_panel_layouts_use_shared_metrics():
    metrics = _read("scripts/script_toolbox/style/metrics.py")
    bindings = _read("scripts/script_toolbox/ui/properties/bindings.py")

    for definition in (
        "FORM_INLINE_SPACING = 8",
        "TRIGGER_PAGE_MARGINS = (2, 3, 2, 2)",
        "TRIGGER_PAGE_SPACING = 4",
        "TRIGGER_PANEL_MARGINS = (5, 5, 5, 5)",
        "TRIGGER_PANEL_SPACING = 3",
    ):
        assert definition in metrics

    assert "configure_inline_layout(" in bindings
    assert "spacing=FORM_INLINE_SPACING" in bindings
    assert "margins=TRIGGER_PAGE_MARGINS" in bindings
    assert "spacing=TRIGGER_PAGE_SPACING" in bindings
    assert "margins=TRIGGER_PANEL_MARGINS" in bindings
    assert "spacing=TRIGGER_PANEL_SPACING" in bindings


def test_base_stylesheet_uses_shared_control_geometry_metrics():
    metrics = _read("scripts/script_toolbox/style/metrics.py")
    stylesheet = _read("scripts/script_toolbox/style/stylesheet.py")

    for definition in (
        "BORDER_RADIUS_CONTROL = 2",
        "BORDER_RADIUS_PANEL = 3",
        "BORDER_RADIUS_CARD = 4",
        "BUTTON_MIN_HEIGHT = 20",
        "INPUT_MIN_HEIGHT = 22",
        "LIST_ITEM_MIN_HEIGHT = 20",
        "TAB_PADDING_HORIZONTAL = 11",
        "SCROLLBAR_EXTENT = 11",
        "SCROLLBAR_HANDLE_MINIMUM = 24",
    ):
        assert definition in metrics

    assert "from . import metrics" in stylesheet
    assert "_STYLE_VALUES.update(vars(metrics))" in stylesheet
    assert "min-height: %(BUTTON_MIN_HEIGHT)spx;" in stylesheet
    assert "min-height: %(INPUT_MIN_HEIGHT)spx;" in stylesheet
    assert "min-height: %(LIST_ITEM_MIN_HEIGHT)spx;" in stylesheet


def test_search_and_icon_buttons_use_shared_component_geometry_metrics():
    metrics = _read("scripts/script_toolbox/style/metrics.py")
    components = _read("scripts/script_toolbox/style/components.py")
    search = _read("scripts/script_toolbox/ui/search_field.py")
    icon_button = _read("scripts/script_toolbox/ui/icon_button.py")

    for definition in (
        "ICON_BUTTON_COMPACT_ICON_SIZE = 16",
        "ICON_BUTTON_COMPACT_SIZE = 25",
        "ICON_BUTTON_TOOLBAR_ICON_SIZE = 18",
        "ICON_BUTTON_TOOLBAR_SIZE = 26",
        "ICON_BUTTON_HEADER_SIZE = 28",
        "SEARCH_FIELD_MIN_HEIGHT = 24",
        "SEARCH_ICON_SIZE = 18",
        "SEARCH_CLEAR_SIZE = 20",
        "SEARCH_TEXT_MARGIN_LEFT = 26",
        "SEARCH_TEXT_MARGIN_RIGHT = 30",
    ):
        assert definition in metrics

    assert "_STYLE_VALUES.update(vars(metrics))" in components
    assert "SEARCH_ICON_GLYPH_SIZE" in search
    assert "SEARCH_CLEAR_GLYPH_SIZE" in search
    assert "SEARCH_TEXT_MARGIN_LEFT" in search
    assert "SEARCH_TEXT_MARGIN_RIGHT" in search
    assert "ICON_BUTTON_COMPACT_ICON_SIZE" in icon_button
    assert "ICON_BUTTON_TOOLBAR_ICON_SIZE" in icon_button
    assert "ICON_BUTTON_HEADER_ICON_SIZE" in icon_button


def test_application_layout_geometry_uses_shared_metrics():
    metrics = _read("scripts/script_toolbox/style/metrics.py")
    interface = _read("scripts/script_toolbox/ui/interface_editor.py")
    main_window = _read("scripts/script_toolbox/ui/main_window.py")
    script_editor = _read("scripts/script_toolbox/ui/script_editor.py")
    share = _read("scripts/script_toolbox/ui/share_hooks.py")

    for definition in (
        "EDITOR_ROOT_MARGINS = (8, 8, 8, 8)",
        "EDITOR_ROOT_SPACING = 7",
        "EDITOR_PANE_MARGINS = (8, 8, 8, 8)",
        "EDITOR_PANE_SPACING = 6",
        "EDITOR_PALETTE_INDENT = 14",
        "EDITOR_TREE_INDENT = 18",
        "EDITOR_ACTION_BUTTON_MIN_WIDTH = 78",
        "TOOLBAR_SPACING = 2",
        "TOOLBAR_GROUP_SPACING = 4",
        "TOOLBOX_TOPBAR_MARGINS = (6, 4, 6, 4)",
        "TOOLBOX_CONTENT_MARGINS = (6, 6, 6, 6)",
        "SCRIPT_EDITOR_ROOT_SPACING = 4",
        "SHARE_ACTION_SPACING = 6",
    ):
        assert definition in metrics

    assert "metrics.EDITOR_ROOT_MARGINS" in interface
    assert interface.count("metrics.EDITOR_PANE_MARGINS") == 3
    assert "metrics.EDITOR_ACTION_BUTTON_MIN_WIDTH" in interface
    assert "metrics.TOOLBOX_TOPBAR_MARGINS" in main_window
    assert "metrics.TOOLBOX_CONTENT_MARGINS" in main_window
    assert "metrics.SCRIPT_EDITOR_ROOT_SPACING" in script_editor
    assert script_editor.count("metrics.TOOLBAR_GROUP_SPACING") == 4
    assert "metrics.SHARE_ACTION_SPACING" in share
