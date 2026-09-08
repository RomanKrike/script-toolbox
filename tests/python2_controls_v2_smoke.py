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
from script_toolbox.model.items import create_item


def main():
    assert CONFIG_VERSION == 17

    icon = create_item(
        "icon",
        {
            "name": "icon_test",
            "path": "icon.png",
            "clickable": True,
            "callbacks": {
                "on_click": "toolbox.get_value('inside')",
            },
        }
    )
    assert icon["kind"] == "icon"
    assert icon["clickable"] is True

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
    document = {
        "version": 17,
        "sections": [
            create_item(
                "folder",
                {
                    "name": "root",
                    "items": [vector],
                }
            )
        ],
    }
    stored = store_value(
        document,
        "vector",
        [-2, 5, 20]
    )
    assert stored["value"] == [0, 5, 10]

    callback_item = create_item(
        "button",
        {
            "callbacks": {
                "on_click": "toolbox.store_value('inside', 1)",
            },
        }
    )
    changed = rewrite_item_references(
        callback_item,
        {"inside": "inside_copy"}
    )
    assert changed is True
    assert "inside_copy" in callback_item["callbacks"]["on_click"]

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
    assert migrated["version"] == 17
    assert legacy_value["callbacks"]["on_change"] == "print(value)"
    assert "on_change_script" not in legacy_value

    print("Controls v2 Python 2.7 smoke passed")


if __name__ == "__main__":
    main()
