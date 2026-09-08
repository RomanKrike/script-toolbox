# -*- coding: utf-8 -*-
from __future__ import print_function

from ..pycompat import text_type
from .items import walk_items


class DocumentIndex(object):
    """O(1) lookup index for normalized toolbox documents.

    Lookup precedence intentionally matches the legacy linear search:
    ``id`` first, then ``name``, then ``label``. When duplicate values exist,
    the first item encountered by ``walk_items`` wins for that lookup field.
    """

    def __init__(
        self,
        document=None,
        include_folders=False
    ):
        self.include_folders = bool(
            include_folders
        )
        self.document = None
        self.items = []
        self.by_id = {}
        self.by_name = {}
        self.by_label = {}

        if document is not None:
            self.rebuild(
                document
            )

    def rebuild(self, document):
        self.document = document
        self.items = []
        self.by_id = {}
        self.by_name = {}
        self.by_label = {}

        for item in walk_items(
            document,
            include_folders=self.include_folders
        ):
            self.items.append(
                item
            )
            self._store_first(
                self.by_id,
                item.get("id"),
                item
            )
            self._store_first(
                self.by_name,
                item.get("name"),
                item
            )
            self._store_first(
                self.by_label,
                item.get("label"),
                item
            )

        return self

    def ensure(self, document):
        if document is not self.document:
            self.rebuild(
                document
            )

        return self

    def invalidate(self):
        self.document = None
        return self

    def find(self, key):
        key_text = text_type(
            key
        )

        item = self.by_id.get(
            key_text
        )

        if item is not None:
            return item

        item = self.by_name.get(
            key_text
        )

        if item is not None:
            return item

        return self.by_label.get(
            key_text
        )

    def _store_first(
        self,
        mapping,
        key,
        item
    ):
        if key is None:
            return

        key_text = text_type(
            key
        )

        if key_text not in mapping:
            mapping[
                key_text
            ] = item

    def __len__(self):
        return len(
            self.items
        )


__all__ = [
    "DocumentIndex",
]
