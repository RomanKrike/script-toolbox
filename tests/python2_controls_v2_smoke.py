# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function

import os
import sys


ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)
SCRIPTS = os.path.join(
    ROOT,
    "scripts"
)
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from script_toolbox.constants import CONFIG_VERSION
from script_toolbox.core.migrations import migrate_document
from script_toolbox.core.references import rewrite_item_references
from script_toolbox.core.values import store_value
from script_toolbox.model import walk_items
from script_toolbox.model.bindings import make_binding
from script_toolbox.model.items import create_item


def main():
    assert CONFIG_VERSION == 18

    icon = create_item(
        "icon",
        {
            "name": "icon_test",
            "path": "icon.png",
            "bindings": [
                make_binding(
                    "click",
                    language="python",
                    script="toolbox.get_value('inside')",
                    binding_id="icon_click"
                )
            ],
        }
    )
    assert icon["kind"] == "icon"
    assert icon["bindings"][0]["event"] == "click"

    vector = create_item(
        "integer",
        {
            "id": "vector",
            "name": "vector",
            "size": 3,
            "min": 0,
            "max": 10,
            "value": [1, 2, 3],
            "show_slider": True,
        }
    )

    layout = create_item(
        "row",
        {
            "id": "layout",
            "name": "layout",
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
                            "id": "actions_a",
                            "name": "actions_a",
                            "items": [
                                {
                                    "kind": "button",
                                    "id": "add_a",
                                    "name": "add_a",
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
    assert layout["items"][0]["kind"] == "column"
    assert layout["items"][0]["row_width_mode"] == "stretch"
    assert layout["items"][0]["items"][1]["kind"] == "row"

    document = {
        "version": 18,
        "sections": [
            create_item(
                "folder",
                {
                    "name": "root",
                    "items": [
                        vector,
                        layout,
                    ],
                }
            )
        ],
    }
    names = [
        item.get("name")
        for item in walk_items(document)
    ]
    assert "column_a" in names
    assert "actions_a" in names
    assert "remove_a" in names

    stored = store_value(
        document,
        "vector",
        [-2, 5, 20]
    )
    assert stored["value"] == [0, 5, 10]

    binding_item = create_item(
        "button",
        {
            "bindings": [
                make_binding(
                    "click",
                    language="python",
                    script="toolbox.store_value('inside', 1)",
                    binding_id="button_click",
                    button_mode="action"
                )
            ],
        }
    )
    changed = rewrite_item_references(
        binding_item,
        {"inside": "inside_copy"}
    )
    assert changed is True
    assert "inside_copy" in binding_item["bindings"][0]["script"]

    migrated = migrate_document({
        "version": 16,
        "sections": [
            {
                "kind": "folder",
                "name": "legacy",
                "items": [
                    {
                        "kind": "string",
                        "name": "value",
                        "on_change_script": "print(value)",
                    }
                ],
            }
        ],
    })
    legacy_value = migrated["sections"][0]["items"][0]
    assert migrated["version"] == 18
    assert legacy_value["bindings"][0]["event"] == "value_changed"
    assert legacy_value["bindings"][0]["script"] == "print(value)"
    assert "callbacks" not in legacy_value
    assert "on_change_script" not in legacy_value

    print("Controls v2 / event bindings / columns Python 2.7 smoke passed")


if __name__ == "__main__":
    main()
