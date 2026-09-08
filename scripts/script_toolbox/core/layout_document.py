# -*- coding: utf-8 -*-
from __future__ import print_function

import copy

from ..model import is_container_kind
from ..model.items import new_id
from ..pycompat import text_type
from .editor_document import EditorDocumentController
from .references import rewrite_item_references


def _walk_subtree(item):
    if not isinstance(item, dict):
        return

    yield item

    if is_container_kind(
        item.get("kind")
    ):
        for child in item.get("items", []) or []:
            for nested in _walk_subtree(child):
                yield nested


def _rewrite_subtree_references(item, replacements):
    changed_ids = set()

    for candidate in _walk_subtree(item):
        if not rewrite_item_references(
            candidate,
            replacements
        ):
            continue

        item_id = text_type(
            candidate.get("id", "")
        )
        if item_id:
            changed_ids.add(item_id)

    return changed_ids


def _rewrite_document_references(document, replacements):
    changed_ids = set()

    for section in (document or {}).get(
        "sections",
        []
    ) or []:
        changed_ids.update(
            _rewrite_subtree_references(
                section,
                replacements
            )
        )

    return changed_ids


class LayoutEditorDocumentController(EditorDocumentController):
    """Editor document controller with Row / Column structural recursion."""

    def cache_subtree(self, data):
        if not isinstance(data, dict):
            return

        item_id = text_type(
            data.get("id", "")
        )
        if item_id:
            self.item_cache[item_id] = data

        if is_container_kind(
            data.get("kind")
        ):
            for child in data.get("items", []) or []:
                self.cache_subtree(child)

    def clone_subtree(self, data, used_names=None):
        """Clone any Folder / Row / Column subtree and remap internal links."""
        if used_names is None:
            used_names = self.used_names()

        id_map = {}
        name_map = {}

        def clone_item(source):
            clone = copy.deepcopy(source)
            old_id = text_type(
                source.get("id", "")
            )
            old_name = text_type(
                source.get("name", "")
            )

            clone["id"] = new_id()
            clone["name"] = self.unique_name(
                clone.get(
                    "name",
                    clone.get("kind", "item")
                ),
                used_names
            )

            if old_id:
                id_map[old_id] = text_type(
                    clone["id"]
                )
            if old_name:
                name_map[old_name] = text_type(
                    clone["name"]
                )

            if is_container_kind(
                clone.get("kind")
            ):
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

        _rewrite_subtree_references(
            clone,
            replacements
        )
        return clone

    def rename_item_references(
        self,
        item_id,
        old_name,
        new_name
    ):
        if self.find_by_id(item_id) is None:
            return set()

        old_name = text_type(
            old_name or ""
        )
        new_name = text_type(
            new_name or ""
        )
        if not old_name or old_name == new_name:
            return set()

        return _rewrite_document_references(
            self.document,
            {
                old_name: new_name,
            }
        )

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
        item.update(
            copy.deepcopy(state or {})
        )

        if is_container_kind(
            item.get("kind")
        ):
            item["items"] = children

        if rebuild:
            self.rebuild_index()
        return True

    def capture_topology(self):
        topology = {
            "roots": [],
            "children": {},
        }

        def visit(item):
            item_id = text_type(
                item.get("id", "")
            )
            if not item_id:
                return

            if is_container_kind(
                item.get("kind")
            ):
                child_ids = []
                for child in item.get("items", []) or []:
                    child_id = text_type(
                        child.get("id", "")
                    )
                    if child_id:
                        child_ids.append(child_id)
                    visit(child)

                topology["children"][item_id] = child_ids

        for section in self.document.get(
            "sections",
            []
        ) or []:
            section_id = text_type(
                section.get("id", "")
            )
            if section_id:
                topology["roots"].append(section_id)
            visit(section)

        return topology

    def _payload_pool(self, payloads):
        pool = {}

        def register(item):
            if not isinstance(item, dict):
                return

            item_id = text_type(
                item.get("id", "")
            )
            if item_id:
                pool[item_id] = item

            if is_container_kind(
                item.get("kind")
            ):
                for child in item.get("items", []) or []:
                    register(child)

        for payload in (payloads or {}).values():
            register(
                copy.deepcopy(payload)
            )

        return pool


__all__ = [
    "LayoutEditorDocumentController",
]
