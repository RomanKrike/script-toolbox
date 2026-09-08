# -*- coding: utf-8 -*-
from __future__ import print_function

import copy

from ...pycompat import text_type


TARGET_VERSION = 17


def _migrate_item(item):
    if not isinstance(item, dict):
        return item

    callbacks = item.get("callbacks")
    callbacks = dict(callbacks) if isinstance(callbacks, dict) else {}

    legacy = text_type(
        item.get("on_change_script") or ""
    )
    if legacy.strip() and not text_type(
        callbacks.get("on_change") or ""
    ).strip():
        callbacks["on_change"] = legacy

    item["callbacks"] = callbacks
    item.pop("on_change_script", None)

    if item.get("kind") in ("folder", "row"):
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
