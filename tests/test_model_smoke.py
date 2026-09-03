# -*- coding: utf-8 -*-

from script_toolbox.model.items import create_item
from script_toolbox.model.items import normalize_document
from script_toolbox.model.items import walk_items


def test_legacy_toggle_migrates_to_checkbox_left():
    item = create_item(
        "toggle",
        {
            "name": "enabled",
            "label": "Enabled",
            "value": True,
        }
    )

    assert item["kind"] == "checkbox"
    assert item["label_position"] == "left"
    assert item["value"] is True


def test_checkbox_defaults_to_right_label():
    item = create_item(
        "checkbox",
        {
            "name": "enabled",
        }
    )

    assert item["kind"] == "checkbox"
    assert item["label_position"] == "right"


def test_nested_folders_are_preserved():
    document = normalize_document({
        "sections": [
            {
                "name": "render",
                "label": "Render",
                "items": [
                    {
                        "kind": "folder",
                        "name": "arnold",
                        "label": "Arnold",
                        "items": [
                            {
                                "kind": "integer",
                                "name": "samples",
                                "value": 4,
                            }
                        ],
                    }
                ],
            }
        ]
    })

    nested = document["sections"][0]["items"][0]

    assert nested["kind"] == "folder"
    assert nested["name"] == "arnold"
    assert nested["items"][0]["kind"] == "integer"


def test_row_rejects_nested_layout_containers():
    row = create_item(
        "row",
        {
            "items": [
                {
                    "kind": "button",
                    "name": "run",
                },
                {
                    "kind": "folder",
                    "name": "bad_folder",
                },
                {
                    "kind": "row",
                    "name": "bad_row",
                },
            ]
        }
    )

    assert [
        item["kind"]
        for item in row["items"]
    ] == [
        "button"
    ]


def test_name_and_label_are_independent():
    item = create_item(
        "integer",
        {
            "name": "subdiv_iterations",
            "label": "Subdivision Iterations",
            "show_label": False,
        }
    )

    assert item["name"] == "subdiv_iterations"
    assert item["label"] == "Subdivision Iterations"
    assert item["show_label"] is False


def test_walk_items_recurses_folder_and_row():
    document = normalize_document({
        "sections": [
            {
                "name": "root",
                "items": [
                    {
                        "kind": "folder",
                        "name": "nested",
                        "items": [
                            {
                                "kind": "row",
                                "name": "controls",
                                "items": [
                                    {
                                        "kind": "float",
                                        "name": "amount",
                                    },
                                    {
                                        "kind": "checkbox",
                                        "name": "enabled",
                                    },
                                ],
                            }
                        ],
                    }
                ],
            }
        ]
    })

    names = [
        item["name"]
        for item in walk_items(
            document
        )
    ]

    assert names == [
        "controls",
        "amount",
        "enabled",
    ]
