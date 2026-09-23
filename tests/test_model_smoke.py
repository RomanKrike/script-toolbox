# -*- coding: utf-8 -*-

import pytest

from script_toolbox.model.items import create_item
from script_toolbox.model.items import normalize_document
from script_toolbox.model.items import walk_items


def test_removed_toggle_kind_is_rejected():
    with pytest.raises(ValueError):
        create_item("toggle", {"name": "enabled"})


def test_checkbox_defaults_to_right_label():
    item = create_item("checkbox", {"name": "enabled"})
    assert item["kind"] == "checkbox"
    assert item["props"]["label_position"] == "right"


def test_nested_folders_are_preserved_in_new_envelope():
    document = normalize_document({
        "version": 21,
        "sections": [
            {
                "kind": "folder", "name": "render", "ui": {"label": "Render"},
                "props": {},
                "items": [
                    {
                        "kind": "folder", "name": "arnold", "ui": {"label": "Arnold"},
                        "props": {},
                        "items": [
                            {"kind": "integer", "name": "samples", "ui": {}, "props": {"value": 4}}
                        ],
                    }
                ],
            }
        ]
    })
    nested = document["sections"][0]["items"][0]
    assert nested["kind"] == "folder"
    assert nested["items"][0]["kind"] == "integer"


def test_row_accepts_layout_containers_but_rejects_sections():
    row = create_item(
        "row",
        {
            "items": [
                {"kind": "button", "name": "run"},
                {"kind": "folder", "name": "bad_folder"},
                {"kind": "row", "name": "nested_row"},
                {"kind": "column", "name": "nested_column"},
            ]
        }
    )
    assert [item["kind"] for item in row["items"]] == ["button", "row", "column"]


def test_name_and_label_are_independent():
    item = create_item(
        "integer",
        {
            "name": "subdiv_iterations",
            "ui": {"label": "Subdivision Iterations", "show_label": False},
        }
    )
    assert item["name"] == "subdiv_iterations"
    assert item["ui"]["label"] == "Subdivision Iterations"
    assert item["ui"]["show_label"] is False


def test_walk_items_recurses_capability_containers_and_can_include_sections():
    document = normalize_document({
        "version": 21,
        "sections": [
            {
                "kind": "folder", "name": "root", "ui": {}, "props": {},
                "items": [
                    {
                        "kind": "folder", "name": "nested", "ui": {}, "props": {},
                        "items": [
                            {
                                "kind": "row", "name": "controls", "ui": {}, "props": {},
                                "items": [
                                    {
                                        "kind": "column", "name": "left_column", "ui": {}, "props": {},
                                        "items": [
                                            {"kind": "float", "name": "amount", "ui": {}, "props": {}},
                                            {"kind": "checkbox", "name": "enabled", "ui": {}, "props": {}},
                                        ],
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        ]
    })

    names = [item["name"] for item in walk_items(document)]
    assert names == ["controls", "left_column", "amount", "enabled"]

    all_names = [
        item["name"]
        for item in walk_items(document, include_sections=True)
    ]
    assert all_names == [
        "root",
        "nested",
        "controls",
        "left_column",
        "amount",
        "enabled",
    ]
