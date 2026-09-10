# -*- coding: utf-8 -*-

from pathlib import Path

from script_toolbox.core.config import load_config
from script_toolbox.model import is_container_kind
from script_toolbox.model import walk_items


FIXTURE = (
    Path(__file__).resolve().parent /
    "fixtures" /
    "current_v20_full.json"
)


def _shape(item):
    result = [item["kind"], item["name"]]

    if is_container_kind(item.get("kind")):
        result.append([
            _shape(child)
            for child in item.get("items", [])
        ])

    return result


def test_editor_tree_root_contains_only_folders():
    document = load_config(path=str(FIXTURE))

    assert document["sections"]
    assert all(item["kind"] == "folder" for item in document["sections"])


def test_current_fixture_rows_keep_expected_children():
    document = load_config(path=str(FIXTURE))

    rows = [
        item
        for item in walk_items(document)
        if item["kind"] == "row"
    ]

    assert rows
    assert [child["kind"] for child in rows[0]["items"]] == [
        "button",
        "integer",
    ]


def test_editor_tree_nested_structure_matches_current_baseline():
    document = load_config(path=str(FIXTURE))

    assert [_shape(section) for section in document["sections"]] == [
        [
            "folder",
            "main_tools",
            [
                ["label", "header"],
                ["string", "asset_name"],
                ["integer", "samples"],
                ["float", "exposure"],
                ["checkbox", "enabled"],
                ["menu", "quality"],
                ["color", "tint"],
                ["field", "nodes"],
                ["toggle_button", "render_state"],
                [
                    "row",
                    "actions",
                    [
                        ["button", "run_render"],
                        ["integer", "frames"],
                    ],
                ],
                [
                    "folder",
                    "advanced",
                    [
                        ["field", "selection"],
                        ["separator", "advanced_separator"],
                    ],
                ],
            ],
        ],
        [
            "folder",
            "secondary",
            [
                ["button", "cleanup"],
            ],
        ],
    ]


def test_editor_model_names_and_ids_are_unique_in_current_baseline():
    document = load_config(path=str(FIXTURE))
    items = list(walk_items(document, include_folders=True))

    ids = [item["id"] for item in items]
    names = [item["name"] for item in items]

    assert len(ids) == len(set(ids))
    assert len(names) == len(set(names))


def test_editor_model_layout_metadata_survives_normalization():
    document = load_config(path=str(FIXTURE))
    main = document["sections"][0]
    row = next(item for item in main["items"] if item["name"] == "actions")
    advanced = next(item for item in main["items"] if item["name"] == "advanced")

    assert main["folder_type"] == "collapsible"
    assert advanced["folder_type"] == "tabs"
    assert row["spacing"] == 6
    assert row["equal_widths"] is True
    assert row["vertical_alignment"] == "center"
