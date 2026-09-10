# -*- coding: utf-8 -*-

import os

from script_toolbox.model import create_item
from script_toolbox.model.layout_geometry import distribution_spacer_positions


ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


def _source(*parts):
    path = os.path.join(ROOT, *parts)
    with open(path, "r") as handle:
        return handle.read()


def test_distribution_spacer_positions_cover_row_and_column_semantics():
    assert distribution_spacer_positions(
        "left", 3, "left", "right"
    ) == (3,)
    assert distribution_spacer_positions(
        "right", 3, "left", "right"
    ) == (0,)
    assert distribution_spacer_positions(
        "center", 3, "left", "right"
    ) == (0, 3)
    assert distribution_spacer_positions(
        "space_between", 3, "left", "right"
    ) == (1, 2)

    assert distribution_spacer_positions(
        "top", 2, "top", "bottom"
    ) == (2,)
    assert distribution_spacer_positions(
        "bottom", 2, "top", "bottom"
    ) == (0,)


def test_row_uses_explicit_parent_distribution_only():
    row = create_item(
        "row",
        {
            "items": [
                {
                    "kind": "button",
                    "row_alignment": "right",
                },
                {
                    "kind": "button",
                    "row_alignment": "right",
                },
            ],
        }
    )

    assert row["horizontal_distribution"] == "left"

    explicit = create_item(
        "row",
        {"horizontal_distribution": "space_between"}
    )
    assert explicit["horizontal_distribution"] == "space_between"


def test_column_normalizes_distribution_and_child_height_contract():
    column = create_item(
        "column",
        {
            "vertical_distribution": "bottom",
            "items": [
                {
                    "kind": "button",
                    "column_height_mode": "fixed",
                    "column_height": 44,
                },
                {
                    "kind": "field",
                    "column_height_mode": "stretch",
                    "column_stretch": 3,
                },
            ],
        }
    )

    assert column["vertical_distribution"] == "bottom"
    assert column["items"][0]["column_height_mode"] == "fixed"
    assert column["items"][0]["column_height"] == 44
    assert column["items"][1]["column_height_mode"] == "stretch"
    assert column["items"][1]["column_stretch"] == 3


def test_column_child_height_values_are_clamped():
    column = create_item(
        "column",
        {
            "items": [
                {
                    "kind": "button",
                    "column_height_mode": "invalid",
                    "column_height": 99999,
                    "column_stretch": 0,
                },
            ],
        }
    )
    child = column["items"][0]

    assert child["column_height_mode"] == "auto"
    assert child["column_height"] == 2000
    assert child["column_stretch"] == 1


def test_runtime_registry_registers_row_and_column_renderers():
    ui_init = _source(
        "scripts", "script_toolbox", "ui", "__init__.py"
    )
    row_runtime = _source(
        "scripts", "script_toolbox", "ui", "row_layout.py"
    )
    column_runtime = _source(
        "scripts", "script_toolbox", "ui", "column_layout.py"
    )

    assert 'register_runtime_renderer("row", render_row, replace=True)' in ui_init
    assert 'register_runtime_renderer("column", render_column)' in ui_init
    assert '"horizontal_distribution"' in row_runtime
    assert '"vertical_distribution"' in column_runtime
    assert '"column_height_mode"' in column_runtime


def test_property_editor_exposes_unified_parent_layout_adapter():
    base = _source(
        "scripts", "script_toolbox", "ui", "properties", "base.py"
    )
    adapter = _source(
        "scripts", "script_toolbox", "ui", "properties", "layout_adapter.py"
    )
    row = _source(
        "scripts", "script_toolbox", "ui", "properties", "row.py"
    )
    column = _source(
        "scripts", "script_toolbox", "ui", "properties", "column.py"
    )

    assert "LayoutPropertyAdapter" in base
    assert "set_parent_layout_context" in base
    assert '"Width Mode"' in base
    assert '"Height Mode"' in base
    assert '"Horizontal Alignment"' in base
    assert '"Vertical Alignment"' in base
    assert '"row_width_mode"' in adapter
    assert '"row_width"' in adapter
    assert '"row_stretch"' in adapter
    assert '"column_height_mode"' in adapter
    assert '"column_height"' in adapter
    assert '"column_stretch"' in adapter
    assert "row_equal_widths" in adapter
    assert "row_alignment" not in adapter
    assert '"Distribution"' in row
    assert '"Cross Alignment"' in row
    assert '"Equal Child Size"' in row
    assert '"Distribution"' in column
    assert '"Cross Alignment"' in column
    assert '"Equal Child Size"' in column


def test_separator_uses_shared_layout_writer():
    registry = _source(
        "scripts", "script_toolbox", "ui", "properties", "registry.py"
    )

    assert "PropertyEditorBase.write_to_item" in registry
    assert 'self.item["bindings"] = []' in registry


def test_icon_editor_uses_only_canonical_content_alignment():
    icon = _source(
        "scripts", "script_toolbox", "ui", "properties", "icon.py"
    )

    assert '"Content Alignment"' in icon
    assert 'item["content_alignment"]' in icon
    assert 'item.get("content_alignment", "left")' in icon
    assert 'item.get("alignment"' not in icon
    assert 'item["alignment"]' not in icon
