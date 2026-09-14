# -*- coding: utf-8 -*-
from __future__ import print_function

import copy

from ..model import DocumentIndex
from ..model import ITEM_TYPES
from ..model import walk_items
from ..model.item_builtins import register_builtin_items
from ..pycompat import text_type


_INDEX_CACHE_LIMIT = 8
_INDEX_CACHE = []


def get_document_index(document):
    """Return the cached lookup index for ``document``."""
    for position, entry in enumerate(list(_INDEX_CACHE)):
        cached_document, index = entry

        if cached_document is not document:
            continue

        index.ensure(document)

        if position != len(_INDEX_CACHE) - 1:
            _INDEX_CACHE.pop(position)
            _INDEX_CACHE.append(entry)

        return index

    index = DocumentIndex(document)
    _INDEX_CACHE.append((document, index))

    while len(_INDEX_CACHE) > _INDEX_CACHE_LIMIT:
        _INDEX_CACHE.pop(0)

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
    _INDEX_CACHE.extend(retained)


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

    return None


def find_item(document, key, index=None):
    if index is None:
        index = get_document_index(document)
    else:
        index.ensure(document)

    item = index.find(key)
    if item is not None:
        return item

    item = _linear_find_item(document, key)
    if item is None:
        return None

    index.rebuild(document)
    return index.find(key)


def _value_definition(item):
    register_builtin_items()
    if not isinstance(item, dict):
        return None
    definition = ITEM_TYPES.get(item.get("kind"))
    if definition is None or not definition.has_capability("has_value"):
        return None
    if definition.has_capability("state_toggle"):
        props = item.get("props", {}) or {}
        if props.get("state_source", "internal") != "internal":
            return None
    return definition


def get_value(document, key, default=None, index=None):
    item = find_item(document, key, index=index)
    definition = _value_definition(item)
    if definition is None:
        return default

    props = item.get("props", {})
    if "value" not in props:
        return default
    return copy.deepcopy(props["value"])


def normalize_value(item, value):
    definition = _value_definition(item)
    if definition is None:
        return value

    raw_props = dict(item.get("props", {}) or {})
    raw_props["value"] = value
    normalized = definition.normalize_props(raw_props)
    return copy.deepcopy(normalized.get("value", value))


def store_value(document, key, value, index=None):
    item = find_item(document, key, index=index)
    definition = _value_definition(item)
    if definition is None:
        return None

    props = item.setdefault("props", {})
    if "value" not in definition.fields:
        return None
    props["value"] = normalize_value(item, value)
    return item


__all__ = [
    "find_item",
    "get_document_index",
    "get_value",
    "invalidate_document_index",
    "normalize_value",
    "store_value",
]
