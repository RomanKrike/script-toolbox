# -*- coding: utf-8 -*-
from __future__ import print_function

import copy

from ..model import walk_items
from ..model.items import clamp
from ..model.items import safe_color
from ..model.items import safe_float
from ..model.items import safe_int
from ..pycompat import text_type


def find_item(document, key):
    key_text = text_type(key)

    items = list(
        walk_items(
            document,
            include_folders=False
        )
    )

    for item in items:
        if item.get("id") == key_text:
            return item

    for item in items:
        if item.get("name") == key_text:
            return item

    for item in items:
        if item.get("label") == key_text:
            return item

    return None


def get_value(document, key, default=None):
    item = find_item(
        document,
        key
    )

    if item is None or "value" not in item:
        return default

    return copy.deepcopy(
        item["value"]
    )


def normalize_value(item, value):
    kind = item.get(
        "kind"
    )

    if kind == "field":
        if value is None:
            return ""

        if isinstance(
            value,
            (list, tuple)
        ):
            return [
                text_type(entry)
                for entry in value
            ]

        return text_type(
            value
        )

    if kind == "string":
        return text_type(
            value
        )

    if kind == "integer":
        return clamp(
            safe_int(
                value,
                item["value"]
            ),
            item["min"],
            item["max"]
        )

    if kind == "float":
        return clamp(
            safe_float(
                value,
                item["value"]
            ),
            item["min"],
            item["max"]
        )

    if kind == "checkbox":
        return bool(
            value
        )

    if kind == "menu":
        value = text_type(
            value
        )

        if value in item["items"]:
            return value

        return item["items"][0]

    if kind == "color":
        return safe_color(
            value
        )

    return value


def store_value(document, key, value):
    item = find_item(
        document,
        key
    )

    if item is None or "value" not in item:
        return None

    item["value"] = normalize_value(
        item,
        value
    )

    return item


__all__ = [
    "find_item",
    "get_value",
    "normalize_value",
    "store_value",
]
