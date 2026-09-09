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
