# -*- coding: utf-8 -*-
from __future__ import print_function

import copy

from ..model import walk_items
from ..model.items import new_id
from ..model.items import sanitize_name
from ..pycompat import text_type


class EditorDocumentController(object):
    """Own the Interface Editor staged document independently of Qt."""

    def __init__(self, document):
        self._document = {}
        self._item_cache = {}
        self.replace(document)

    @property
    def document(self):
        return self._document

    @property
    def item_cache(self):
        return self._item_cache

    def replace(self, document, copy_document=True):
        candidate = document if isinstance(document, dict) else {}

        if copy_document:
            candidate = copy.deepcopy(candidate)

        self._document = candidate
        self.rebuild_index()
        return self._document

    def adopt(self, document):
        """Adopt an internally assembled staged document without copying it."""
        return self.replace(
            document,
            copy_document=False
        )

    def snapshot(self):
        return copy.deepcopy(self._document)

    def rebuild_index(self):
        self._item_cache = {}

        for item in walk_items(
            self._document,
            include_folders=True
        ):
            item_id = text_type(item.get("id", ""))

            if item_id:
                self._item_cache[item_id] = item

        return self._item_cache

    def replace_index(self, mapping=None):
        self._item_cache = dict(mapping or {})
        return self._item_cache

    def find_by_id(self, item_id):
        return self._item_cache.get(text_type(item_id))

    def cache_subtree(self, data):
        if not isinstance(data, dict):
            return

        item_id = text_type(data.get("id", ""))
        if item_id:
            self._item_cache[item_id] = data

        if data.get("kind") in ("folder", "row"):
            for child in data.get("items", []) or []:
                self.cache_subtree(child)

    def used_names(self):
        return set(
            text_type(item.get("name", ""))
            for item in walk_items(
                self._document,
                include_folders=True
            )
        )

    def unique_name(self, base, used_names=None):
        if used_names is None:
            used_names = self.used_names()

        base = sanitize_name(base, "item")

        if base not in used_names:
            used_names.add(base)
            return base

        index = 2
        while True:
            candidate = "{0}_{1}".format(base, index)
            if candidate not in used_names:
                used_names.add(candidate)
                return candidate
            index += 1

    def clone_subtree(self, data, used_names=None):
        if used_names is None:
            used_names = self.used_names()

        clone = copy.deepcopy(data)
        clone["id"] = new_id()
        clone["name"] = self.unique_name(
            clone.get("name", clone.get("kind", "item")),
            used_names
        )

        if clone.get("kind") in ("folder", "row"):
            clone["items"] = [
                self.clone_subtree(child, used_names)
                for child in clone.get("items", []) or []
            ]

        return clone

    def duplicate_name(self):
        names = set()

        for item in walk_items(
            self._document,
            include_folders=True
        ):
            name = text_type(item.get("name", ""))
            if name in names:
                return name
            names.add(name)

        return None


__all__ = [
    "EditorDocumentController",
]
