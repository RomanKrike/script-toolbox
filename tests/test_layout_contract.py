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
                    "ui": {"alignment": "right"},
                },
                {
                    "kind": "button",
                    "ui": {"alignment": "right"},
                },
            ],
        }
    )

    assert row["props"]["horizontal_distribution"] == "left"

    explicit = create_item(
        "row",
        {
            "props": {
                "horizontal_distribution": "space_between",
            },
        }
    )
    assert explicit["props"]["horizontal_distribution"] == "space_between"


def test_column_normalizes_distribution_and_child_height_contract():
    column = create_item(
        "column",
        {
            "props": {"vertical_distribution": "bottom"},
            "items": [
                {
                    "kind": "button",
                    "ui": {
                        "height_mode": "fixed",
                        "height": 44,
                    },
                },
                {
                    "kind": "field",
                    "ui": {
                        "height_mode": "stretch",
                        "vertical_stretch": 3,
                    },
                },
            ],
        }
    )

    assert column["props"]["vertical_distribution"] == "bottom"
    assert column["items"][0]["ui"]["height_mode"] == "fixed"
    assert column["items"][0]["ui"]["height"] == 44
    assert column["items"][1]["ui"]["height_mode"] == "stretch"
    assert column["items"][1]["ui"]["vertical_stretch"] == 3


def test_column_child_height_values_are_clamped():
    column = create_item(
        "column",
        {
            "items": [
                {
                    "kind": "button",
                    "ui": {
                        "height_mode": "invalid",
                        "height": 99999,
                        "vertical_stretch": 0,
                    },
                },
            ],
        }
    )
    child_ui = column["items"][0]["ui"]

    assert child_ui["height_mode"] == "auto"
    assert child_ui["height"] == 2000
    assert child_ui["vertical_stretch"] == 1


def test_runtime_registry_resolves_row_and_column_from_type_metadata():
    definitions = _source(
        "scripts", "script_toolbox", "model", "item_builtins.py"
    )
    ui_bootstrap = _source(
        "scripts", "script_toolbox", "ui", "item_ui_bootstrap.py"
    )
    row_runtime = _source(
        "scripts", "script_toolbox", "ui", "row_layout.py"
    )
    column_runtime = _source(
        "scripts", "script_toolbox", "ui", "column_layout.py"
    )

    assert 'renderer_path=".row_layout:render_row"' in definitions
    assert 'renderer_path=".column_layout:render_column"' in definitions
    assert "for definition in ITEM_TYPES.all():" in ui_bootstrap
    assert "definition.renderer_path" in ui_bootstrap
    assert 'props.get(\n        "horizontal_distribution"' in row_runtime
    assert 'props.get(\n        "vertical_distribution"' in column_runtime
    assert 'child_ui.get(\n            "height_mode"' in column_runtime
    assert 'child_ui.get("vertical_stretch", 1)' in column_runtime


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
    assert 'ui["width_mode"]' in adapter
    assert 'ui["width"]' in adapter
    assert 'ui["stretch"]' in adapter
    assert 'ui["height_mode"]' in adapter
    assert 'ui["height"]' in adapter
    assert 'ui["vertical_stretch"]' in adapter
    assert "parent_definition.layout_axis" in adapter
    assert "row_equal_widths" in adapter
    assert "row_alignment" not in adapter
    assert '"Distribution"' in row
    assert '"Cross Alignment"' in row
    assert '"Equal Child Size"' in row
    assert '"Distribution"' in column
    assert '"Cross Alignment"' in column
    assert '"Equal Child Size"' in column


def test_property_registry_routes_editors_directly_from_item_definition():
    registry = _source(
        "scripts", "script_toolbox", "ui", "properties", "registry.py"
    )

    assert "ITEM_TYPES.get(kind" in registry
    assert "definition.inspector" in registry
    assert "bind_item_ui(kind, inspector=editor_class)" in registry
    assert "PROPERTY_EDITORS" not in registry
    assert "item_view" not in registry
    assert "EnvelopeRoutedEditor" not in registry


def test_icon_editor_uses_only_canonical_content_alignment():
    icon = _source(
        "scripts", "script_toolbox", "ui", "properties", "icon.py"
    )

    assert '"Content Alignment"' in icon
    assert 'item["content_alignment"]' in icon
    assert 'item.get("content_alignment", "left")' in icon
    assert 'item.get("alignment"' not in icon
    assert 'item["alignment"]' not in icon
