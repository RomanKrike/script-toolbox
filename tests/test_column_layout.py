# -*- coding: utf-8 -*-

import os

from script_toolbox.constants import ITEM_KINDS
from script_toolbox.core.layout_document import LayoutEditorDocumentController
from script_toolbox.model import DocumentIndex
from script_toolbox.model import create_item
from script_toolbox.model import normalize_document
from script_toolbox.model import walk_items
from script_toolbox.model.bindings import make_binding


ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


def _source(*parts):
    path = os.path.join(ROOT, *parts)
    with open(path, "r") as handle:
        return handle.read()


def _column_example():
    return create_item(
        "row",
        {
            "id": "outer_row",
            "name": "outer_row",
            "items": [
                {
                    "kind": "column",
                    "id": "column_a",
                    "name": "column_a",
                    "items": [
                        {
                            "kind": "field",
                            "id": "field_a",
                            "name": "field_a",
                        },
                        {
                            "kind": "row",
                            "id": "buttons_a",
                            "name": "buttons_a",
                            "items": [
                                {
                                    "kind": "button",
                                    "id": "add_a",
                                    "name": "add_a",
                                    "bindings": [
                                        make_binding(
                                            "click",
                                            script=(
                                                "toolbox.get_value('field_a')"
                                            ),
                                            binding_id="add_click",
                                            button_mode="action"
                                        )
                                    ],
                                },
                                {
                                    "kind": "button",
                                    "id": "remove_a",
                                    "name": "remove_a",
                                },
                            ],
                        },
                    ],
                },
                {
                    "kind": "column",
                    "id": "column_b",
                    "name": "column_b",
                    "items": [
                        {
                            "kind": "field",
                            "id": "field_b",
                            "name": "field_b",
                        },
                    ],
                },
            ],
        }
    )


def _document():
    return {
        "version": 18,
        "sections": [
            create_item(
                "folder",
                {
                    "id": "root",
                    "name": "root",
                    "items": [
                        _column_example()
                    ],
                }
            )
        ],
    }


def test_column_is_supported_layout_kind_with_nested_rows():
    layout = _column_example()

    assert "column" in ITEM_KINDS
    assert layout["kind"] == "row"
    assert layout["items"][0]["kind"] == "column"
    assert layout["items"][0]["row_width_mode"] == "stretch"
    assert layout["items"][0]["horizontal_alignment"] == "stretch"
    assert layout["items"][0]["items"][1]["kind"] == "row"
    assert layout["items"][0]["items"][1]["items"][0]["kind"] == "button"


def test_layout_containers_reject_nested_folders_but_keep_rows_and_columns():
    column = create_item(
        "column",
        {
            "items": [
                {
                    "kind": "folder",
                    "name": "invalid_folder",
                },
                {
                    "kind": "row",
                    "name": "valid_row",
                },
                {
                    "kind": "column",
                    "name": "valid_column",
                },
            ]
        }
    )

    assert [
        item["kind"]
        for item in column["items"]
    ] == [
        "row",
        "column",
    ]


def test_normalize_walk_and_index_reach_controls_inside_columns():
    normalized = normalize_document(
        _document()
    )
    names = [
        item["name"]
        for item in walk_items(normalized)
    ]

    assert "outer_row" in names
    assert "column_a" in names
    assert "buttons_a" in names
    assert "add_a" in names
    assert "field_b" in names

    index = DocumentIndex(normalized)
    assert index.find("add_a")["kind"] == "button"
    assert index.find("field_b")["kind"] == "field"


def test_layout_controller_clones_column_subtree_and_remaps_internal_links():
    controller = LayoutEditorDocumentController(
        _document()
    )
    source = controller.find_by_id("outer_row")
    clone = controller.clone_subtree(source)

    column = clone["items"][0]
    field = column["items"][0]
    button = column["items"][1]["items"][0]

    assert clone["id"] != "outer_row"
    assert column["id"] != "column_a"
    assert field["id"] != "field_a"
    assert field["name"] != "field_a"
    assert field["id"] in button["bindings"][0]["script"]
    assert "'field_a'" not in button["bindings"][0]["script"]


def test_layout_controller_topology_tracks_nested_columns_and_rows():
    controller = LayoutEditorDocumentController(
        _document()
    )
    topology = controller.capture_topology()

    assert topology["children"]["root"] == ["outer_row"]
    assert topology["children"]["outer_row"] == [
        "column_a",
        "column_b",
    ]
    assert topology["children"]["column_a"] == [
        "field_a",
        "buttons_a",
    ]
    assert topology["children"]["buttons_a"] == [
        "add_a",
        "remove_a",
    ]


def test_column_editor_and_runtime_are_wired_without_layout_triggers():
    ui_init = _source(
        "scripts",
        "script_toolbox",
        "ui",
        "__init__.py"
    )
    adapter = _source(
        "scripts",
        "script_toolbox",
        "ui",
        "layout_editor_adapter.py"
    )
    column_renderer = _source(
        "scripts",
        "script_toolbox",
        "ui",
        "column_layout.py"
    )
    registry = _source(
        "scripts",
        "script_toolbox",
        "ui",
        "properties",
        "registry.py"
    )
    model_layouts = _source(
        "scripts",
        "script_toolbox",
        "model",
        "layouts.py"
    )

    assert '"Column",' in ui_init
    assert '"column",' in ui_init
    assert 'register_runtime_renderer(\n    "column"' in ui_init
    assert "build_layout_editor_class" in ui_init
    assert '"column": ColumnPropertyEditor' in registry
    assert "QVBoxLayout" in column_renderer
    assert '"horizontal_alignment"' in column_renderer
    assert '"row", "column"' in adapter
    assert 'EVENT_CAPABILITIES.setdefault(\n        "column"' in model_layouts
