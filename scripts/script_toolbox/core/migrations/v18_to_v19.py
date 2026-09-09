# -*- coding: utf-8 -*-
from __future__ import print_function

import copy

from ...pycompat import text_type


TARGET_VERSION = 19

_STATE_FIELDS = (
    "state_get_script",
    "state_get_language",
    "state_on_script",
    "state_on_language",
    "state_off_script",
    "state_off_language",
    "state_on_label",
    "state_off_label",
    "state_on_color",
    "state_off_color",
)


def _migrate_item(item):
    if not isinstance(item, dict):
        return item

    kind = text_type(
        item.get("kind", "button")
    ).lower()

    if kind == "button":
        mode = text_type(
            item.get("mode", "action")
        ).lower()

        if mode == "state":
            item["kind"] = "toggle_button"
            item["state_source"] = "script"
            item.setdefault("value", False)
        else:
            item.pop("mode", None)
            for key in _STATE_FIELDS:
                item.pop(key, None)

    if item.get("kind") == "toggle_button":
        item.pop("mode", None)
        item.pop("color", None)
        item.pop("language", None)
        item.pop("click_script", None)
        item.pop("shift_script", None)

    if item.get("kind") in (
        "folder",
        "row",
        "column",
    ):
        for child in item.get("items", []) or []:
            _migrate_item(child)

    return item


def migrate(document):
    migrated = copy.deepcopy(document)

    for section in migrated.get("sections", []) or []:
        _migrate_item(section)

    migrated["version"] = TARGET_VERSION
    return migrated


__all__ = [
    "TARGET_VERSION",
    "migrate",
]
