# -*- coding: utf-8 -*-
from __future__ import print_function

import copy

from ..model import is_container_kind
from ..model import walk_items
from ..model.items import new_id
from ..model.items import sanitize_name
from ..pycompat import text_type
from .references import rewrite_document_references_result
from .references import rewrite_subtree_references_result


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

        if is_container_kind(data.get("kind")):
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

    def clone_subtree(self, data, used_names=None, return_result=False):
        """Clone a subtree and remap links that target items inside it."""
        if used_names is None:
            used_names = self.used_names()

        id_map = {}
        name_map = {}

        def clone_item(source):
            clone = copy.deepcopy(source)
            old_id = text_type(source.get("id", ""))
            old_name = text_type(source.get("name", ""))
            clone["id"] = new_id()
            clone["name"] = self.unique_name(
                clone.get("name", clone.get("kind", "item")),
                used_names
            )

            if old_id:
                id_map[old_id] = text_type(clone["id"])
            if old_name:
                name_map[old_name] = text_type(clone["name"])

            if is_container_kind(clone.get("kind")):
                clone["items"] = [
                    clone_item(child)
                    for child in source.get("items", []) or []
                ]

            return clone

        clone = clone_item(data)
        replacements = dict(id_map)
        for old_name, new_name in name_map.items():
            if old_name not in replacements:
                replacements[old_name] = new_name

        result = rewrite_subtree_references_result(
            clone,
            replacements
        )
        if return_result:
            return clone, result
        return clone

    def rename_item_references_result(
        self,
        item_id,
        old_name,
        new_name
    ):
        """Rewrite managed links and report references needing manual review."""
        if self.find_by_id(item_id) is None:
            return {
                "changed_ids": set(),
                "unresolved_items": [],
            }

        old_name = text_type(old_name or "")
        new_name = text_type(new_name or "")
        if not old_name or old_name == new_name:
            return {
                "changed_ids": set(),
                "unresolved_items": [],
            }

        return rewrite_document_references_result(
            self._document,
            {
                old_name: new_name,
            }
        )

    def rename_item_references(
        self,
        item_id,
        old_name,
        new_name
    ):
        """Backward-compatible changed-ID rename helper."""
        return self.rename_item_references_result(
            item_id,
            old_name,
            new_name
        )["changed_ids"]

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

    # ------------------------------------------------------------------
    # Command support
    # ------------------------------------------------------------------

    def item_state(self, item_or_id):
        """Return non-structural item state suitable for an edit command."""
        if isinstance(item_or_id, dict):
            item = item_or_id
        else:
            item = self.find_by_id(item_or_id)

        if item is None:
            return {}

        state = {}
        for key, value in item.items():
            if key == "items":
                continue
            state[key] = copy.deepcopy(value)
        return state

    def apply_item_state(
        self,
        item_id,
        state,
        rebuild=True
    ):
        item = self.find_by_id(item_id)
        if item is None:
            return False

        children = item.get("items", [])
        item.clear()
        item.update(copy.deepcopy(state or {}))

        if is_container_kind(item.get("kind")):
            item["items"] = children

        if rebuild:
            self.rebuild_index()
        return True

    def root_state(self):
        state = {}
        for key, value in self._document.items():
            if key == "sections":
                continue
            state[key] = copy.deepcopy(value)
        return state

    def apply_root_state(self, state):
        sections = self._document.get("sections", [])
        self._document.clear()
        self._document.update(copy.deepcopy(state or {}))
        self._document["sections"] = sections
        return self._document

    def capture_topology(self):
        topology = {
            "roots": [],
            "children": {},
        }

        def visit(item):
            item_id = text_type(item.get("id", ""))
            if not item_id:
                return

            if is_container_kind(item.get("kind")):
                child_ids = []
                for child in item.get("items", []) or []:
                    child_id = text_type(child.get("id", ""))
                    if child_id:
                        child_ids.append(child_id)
                    visit(child)
                topology["children"][item_id] = child_ids

        for section in self._document.get("sections", []) or []:
            section_id = text_type(section.get("id", ""))
            if section_id:
                topology["roots"].append(section_id)
            visit(section)

        return topology

    def _payload_pool(self, payloads):
        pool = {}

        def register(item):
            if not isinstance(item, dict):
                return
            item_id = text_type(item.get("id", ""))
            if item_id:
                pool[item_id] = item
            if is_container_kind(item.get("kind")):
                for child in item.get("items", []) or []:
                    register(child)

        for payload in (payloads or {}).values():
            register(copy.deepcopy(payload))

        return pool

    def apply_topology(self, topology, payloads=None):
        """Restore ID-only topology, materializing missing subtrees as needed."""
        topology = topology or {
            "roots": [],
            "children": {},
        }
        pool = dict(self._item_cache)
        pool.update(self._payload_pool(payloads))

        for parent_id, child_ids in topology.get("children", {}).items():
            parent_id = text_type(parent_id)
            parent = pool.get(parent_id)
            if parent is None:
                raise KeyError(parent_id)

            children = []
            for child_id in child_ids:
                child_id = text_type(child_id)
                child = pool.get(child_id)
                if child is None:
                    raise KeyError(child_id)
                children.append(child)
            parent["items"] = children

        sections = []
        for item_id in topology.get("roots", []):
            item_id = text_type(item_id)
            item = pool.get(item_id)
            if item is None:
                raise KeyError(item_id)
            sections.append(item)

        self._document["sections"] = sections
        self.rebuild_index()
        return self._document


__all__ = [
    "EditorDocumentController",
]
