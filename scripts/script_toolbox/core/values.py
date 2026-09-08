# -*- coding: utf-8 -*-
from __future__ import print_function

import copy

from ..model import DocumentIndex
from ..model import walk_items
from ..model.items import clamp
from ..model.items import safe_color
from ..model.items import safe_float
from ..model.items import safe_int
from ..pycompat import text_type


_INDEX_CACHE_LIMIT = 8
_INDEX_CACHE = []


def get_document_index(document):
    """Return the cached lookup index for ``document``.

    Runtime config replacement creates a new document object, so identity is a
    cheap and reliable cache key for the current architecture. The small LRU
    bound prevents old editor/reload documents from being retained forever.
    """
    for position, entry in enumerate(
        list(_INDEX_CACHE)
    ):
        cached_document, index = entry

        if cached_document is not document:
            continue

        index.ensure(
            document
        )

        if position != len(_INDEX_CACHE) - 1:
            _INDEX_CACHE.pop(
                position
            )
            _INDEX_CACHE.append(
                entry
            )

        return index

    index = DocumentIndex(
        document
    )
    _INDEX_CACHE.append(
        (document, index)
    )

    while len(_INDEX_CACHE) > _INDEX_CACHE_LIMIT:
        _INDEX_CACHE.pop(
            0
        )

    return index


def invalidate_document_index(document=None):
    """Invalidate one cached document index, or all indexes when omitted."""
    if document is None:
        del _INDEX_CACHE[:]
        return

    retained = [
        entry
        for entry in _INDEX_CACHE
        if entry[0] is not document
    ]
    del _INDEX_CACHE[:]
    _INDEX_CACHE.extend(
        retained
    )


def _linear_find_item(document, key):
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


def find_item(
    document,
    key,
    index=None
):
    if index is None:
        index = get_document_index(
            document
        )
    else:
        index.ensure(
            document
        )

    item = index.find(
        key
    )

    if item is not None:
        return item

    # Runtime value edits do not change lookup keys, so normal successful
    # lookups stay O(1). This fallback preserves compatibility for external
    # code that mutates a document structure/name/label in place without
    # explicitly invalidating the index.
    item = _linear_find_item(
        document,
        key
    )

    if item is None:
        return None

    index.rebuild(
        document
    )
    return index.find(
        key
    )


def get_value(
    document,
    key,
    default=None,
    index=None
):
    item = find_item(
        document,
        key,
        index=index
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


def store_value(
    document,
    key,
    value,
    index=None
):
    item = find_item(
        document,
        key,
        index=index
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
    "get_document_index",
    "get_value",
    "invalidate_document_index",
    "normalize_value",
    "store_value",
]
