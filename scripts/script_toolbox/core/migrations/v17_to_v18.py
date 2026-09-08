# -*- coding: utf-8 -*-
from __future__ import print_function

import copy

from ...model.bindings import normalize_bindings
from ...pycompat import text_type


TARGET_VERSION = 18


def _migrate_item(item):
    if not isinstance(item, dict):
        return item

    kind = text_type(
        item.get("kind", "button")
    ).lower()

    # Preserve the historical button language on state transition scripts.
    if kind == "button":
        old_language = text_type(
            item.get("language", "python")
        ).lower()
        if old_language not in ("python", "mel"):
            old_language = "python"

        item["state_get_language"] = "python"
        item["state_on_language"] = text_type(
            item.get("state_on_language", old_language)
        ).lower()
        item["state_off_language"] = text_type(
            item.get("state_off_language", old_language)
        ).lower()

    item["bindings"] = normalize_bindings(
        kind,
        item
    )

    # Schema 18 has one execution model for interactive event scripts.
    item.pop("callbacks", None)
    item.pop("on_change_script", None)

    if kind == "button":
        item.pop("language", None)
        item.pop("click_script", None)
        item.pop("shift_script", None)

    if kind == "icon":
        item.pop("clickable", None)

    if kind in ("folder", "row"):
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
