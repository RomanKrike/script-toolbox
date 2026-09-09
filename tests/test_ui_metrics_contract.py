# -*- coding: utf-8 -*-

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_property_editor_geometry_uses_shared_metrics_and_helpers():
    metrics = _read(
        "scripts/script_toolbox/style/metrics.py"
    )
    helpers = _read(
        "scripts/script_toolbox/ui/layout_helpers.py"
    )
    base = _read(
        "scripts/script_toolbox/ui/properties/base.py"
    )

    assert "PROPERTY_EDITOR_SPACING = 8" in metrics
    assert "PROPERTY_FORM_HORIZONTAL_SPACING = 8" in metrics
    assert "PROPERTY_FORM_VERTICAL_SPACING = 6" in metrics
    assert "PROPERTY_GROUP_MARGINS = (7, 7, 7, 7)" in metrics
    assert "PROPERTY_GROUP_HORIZONTAL_SPACING = 8" in metrics
    assert "PROPERTY_GROUP_VERTICAL_SPACING = 5" in metrics

    assert "def configure_property_form(form):" in helpers
    assert "def configure_property_group_form(form):" in helpers
    assert "PROPERTY_FORM_HORIZONTAL_SPACING" in helpers
    assert "PROPERTY_GROUP_MARGINS" in helpers

    assert "from ...style.metrics import PROPERTY_EDITOR_SPACING" in base
    assert "configure_property_form(self.form)" in base
    assert base.count("configure_property_group_form(") == 2
    assert "setSpacing(PROPERTY_EDITOR_SPACING)" in base

    assert "setHorizontalSpacing(8)" not in base
    assert "setVerticalSpacing(6)" not in base
    assert "setContentsMargins(7, 7, 7, 7)" not in base
    assert "setVerticalSpacing(5)" not in base


def test_numeric_value_rows_use_shared_inline_layout_geometry():
    metrics = _read(
        "scripts/script_toolbox/style/metrics.py"
    )
    helpers = _read(
        "scripts/script_toolbox/ui/layout_helpers.py"
    )
    basic = _read(
        "scripts/script_toolbox/ui/properties/basic.py"
    )

    assert "MARGINS_NONE = (0, 0, 0, 0)" in metrics
    assert "INLINE_CONTROL_SPACING = 4" in metrics
    assert "def configure_inline_layout(" in helpers
    assert "MARGINS_NONE" in helpers
    assert "INLINE_CONTROL_SPACING" in helpers

    assert basic.count("configure_inline_layout(values_layout)") == 1
    assert "values_layout.setContentsMargins(0, 0, 0, 0)" not in basic
    assert "values_layout.setSpacing(4)" not in basic


def test_integer_and_float_share_numeric_property_editor_base():
    basic = _read(
        "scripts/script_toolbox/ui/properties/basic.py"
    )

    assert (
        "class NumericPropertyEditorBase(ValuePropertyEditorBase):"
        in basic
    )
    assert (
        "class IntegerPropertyEditor(NumericPropertyEditorBase):"
        in basic
    )
    assert (
        "class FloatPropertyEditor(NumericPropertyEditorBase):"
        in basic
    )

    shared = basic.split(
        "class NumericPropertyEditorBase(ValuePropertyEditorBase):",
        1
    )[1].split(
        "class IntegerPropertyEditor(NumericPropertyEditorBase):",
        1
    )[0]
    integer = basic.split(
        "class IntegerPropertyEditor(NumericPropertyEditorBase):",
        1
    )[1].split(
        "class FloatPropertyEditor(NumericPropertyEditorBase):",
        1
    )[0]
    floating = basic.split(
        "class FloatPropertyEditor(NumericPropertyEditorBase):",
        1
    )[1].split(
        "class CheckboxPropertyEditor(ValuePropertyEditorBase):",
        1
    )[0]

    for method in (
        "def current_size(self):",
        "def _size_changed(self, *args):",
        "def _refresh_size(self):",
        "def load_specific(self, item):",
        "def write_specific(self, item):",
    ):
        assert method in shared
        assert method not in integer
        assert method not in floating

    assert "SPINBOX_CLASS = QtGui.QSpinBox" in integer
    assert "VALUE_DEFAULT = 0" in integer
    assert "STEP_DEFAULT = 1" in integer
    assert "STEP_MINIMUM = 1" in integer
    assert "return int(value)" in integer

    assert "SPINBOX_CLASS = QtGui.QDoubleSpinBox" in floating
    assert "VALUE_DEFAULT = 0.0" in floating
    assert "STEP_DEFAULT = 0.1" in floating
    assert "STEP_MINIMUM = 0.000001" in floating
    assert "DISPLAY_DECIMALS = 6" in floating
    assert "DECIMALS_DEFAULT = 3" in floating
    assert "return float(value)" in floating


def test_button_appearance_groups_use_shared_property_group_geometry():
    button = _read(
        "scripts/script_toolbox/ui/properties/button.py"
    )

    assert (
        "from ..layout_helpers import configure_property_group_form"
        in button
    )
    assert button.count("configure_property_group_form(") == 2
    assert 'QGroupBox("Action Appearance")' in button
    assert 'QGroupBox("State Appearance")' in button


def test_trigger_panel_layouts_use_shared_metrics():
    metrics = _read(
        "scripts/script_toolbox/style/metrics.py"
    )
    helpers = _read(
        "scripts/script_toolbox/ui/layout_helpers.py"
    )
    bindings = _read(
        "scripts/script_toolbox/ui/properties/bindings.py"
    )

    assert "FORM_INLINE_SPACING = 8" in metrics
    assert "TRIGGER_PAGE_MARGINS = (2, 3, 2, 2)" in metrics
    assert "TRIGGER_PAGE_SPACING = 4" in metrics
    assert "TRIGGER_PANEL_MARGINS = (5, 5, 5, 5)" in metrics
    assert "TRIGGER_PANEL_SPACING = 3" in metrics

    assert "def configure_layout(" in helpers
    assert "return configure_layout(" in helpers

    assert "configure_inline_layout(" in bindings
    assert "spacing=FORM_INLINE_SPACING" in bindings
    assert "margins=TRIGGER_PAGE_MARGINS" in bindings
    assert "spacing=TRIGGER_PAGE_SPACING" in bindings
    assert "margins=TRIGGER_PANEL_MARGINS" in bindings
    assert "spacing=TRIGGER_PANEL_SPACING" in bindings

    assert "modifier_layout.setContentsMargins(0, 0, 0, 0)" not in bindings
    assert "modifier_layout.setSpacing(8)" not in bindings
    assert "root.setContentsMargins(2, 3, 2, 2)" not in bindings
    assert "root.setContentsMargins(5, 5, 5, 5)" not in bindings
    assert "root.setSpacing(4)" not in bindings
    assert "root.setSpacing(3)" not in bindings


def test_base_stylesheet_uses_shared_control_geometry_metrics():
    metrics = _read(
        "scripts/script_toolbox/style/metrics.py"
    )
    stylesheet = _read(
        "scripts/script_toolbox/style/stylesheet.py"
    )

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
    assert "padding: %(TAB_PADDING_VERTICAL)spx %(TAB_PADDING_HORIZONTAL)spx;" in stylesheet
    assert "width: %(SCROLLBAR_EXTENT)spx;" in stylesheet
    assert "height: %(SCROLLBAR_EXTENT)spx;" in stylesheet


def test_search_and_icon_buttons_use_shared_component_geometry_metrics():
    metrics = _read(
        "scripts/script_toolbox/style/metrics.py"
    )
    components = _read(
        "scripts/script_toolbox/style/components.py"
    )
    search = _read(
        "scripts/script_toolbox/ui/search_field.py"
    )
    icon_button = _read(
        "scripts/script_toolbox/ui/icon_button.py"
    )

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
    assert "min-height: %(SEARCH_FIELD_MIN_HEIGHT)spx;" in components
    assert "SEARCH_ICON_GLYPH_SIZE" in search
    assert "SEARCH_CLEAR_GLYPH_SIZE" in search
    assert "SEARCH_TEXT_MARGIN_LEFT" in search
    assert "SEARCH_TEXT_MARGIN_RIGHT" in search
    assert "_SEARCH_ICON_SIZE = 18" not in search
    assert "_CLEAR_BUTTON_SIZE = 20" not in search

    assert "ICON_BUTTON_COMPACT_ICON_SIZE" in icon_button
    assert "ICON_BUTTON_TOOLBAR_ICON_SIZE" in icon_button
    assert "ICON_BUTTON_HEADER_ICON_SIZE" in icon_button
    assert "ICON_BUTTON_COMPACT: (16, 25)" not in icon_button
    assert "ICON_BUTTON_TOOLBAR: (18, 26)" not in icon_button
    assert "ICON_BUTTON_HEADER: (18, 28)" not in icon_button
