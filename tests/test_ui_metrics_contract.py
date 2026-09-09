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

    assert (
        basic.count("configure_inline_layout(values_layout)") == 2
    )
    assert "values_layout.setContentsMargins(0, 0, 0, 0)" not in basic
    assert "values_layout.setSpacing(4)" not in basic


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
