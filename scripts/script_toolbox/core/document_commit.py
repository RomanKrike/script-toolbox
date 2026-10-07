# -*- coding: utf-8 -*-
"""Three-way authored-document merge, independent of Qt and persistence."""
from __future__ import print_function

import copy

from ..model import normalize_document, walk_items
from ..pycompat import text_type
from .preset_references import authored_document

_MISSING = object()


class DocumentMergeConflict(RuntimeError):
    def __init__(self, path):
        self.path = path
        RuntimeError.__init__(self,
            "This parameter changed after the editor was opened ({0}). "
            "Reopen the editor to review the current configuration before applying.".format(path))


class DocumentSaveFailure(RuntimeError):
    """The candidate was not activated because persistence failed."""
    pass


def _copy(value):
    return _MISSING if value is _MISSING else copy.deepcopy(value)


def _item_map(values):
    result = {}
    for value in values:
        if not isinstance(value, dict) or not value.get("id") or value["id"] in result:
            return None
        result[value["id"]] = value
    return result


def _merge(base, staged, current, path):
    if staged == base:
        return _copy(current)
    if current == base or staged == current:
        return _copy(staged)
    if all(isinstance(value, dict) for value in (base, staged, current)):
        result = {}
        for key in sorted(set(base) | set(staged) | set(current)):
            value = _merge(base.get(key, _MISSING), staged.get(key, _MISSING),
                           current.get(key, _MISSING), path + "/" + text_type(key))
            if value is not _MISSING:
                result[key] = value
        return result
    if path.rsplit("/", 1)[-1] in ("sections", "items") and all(
            isinstance(value, list) for value in (base, staged, current)):
        maps = [_item_map(value) for value in (base, staged, current)]
        if all(value is not None for value in maps):
            orders = [[item["id"] for item in value] for value in (base, staged, current)]
            if orders[1] == orders[0]:
                order = orders[2]
            elif orders[2] == orders[0] or orders[1] == orders[2]:
                order = orders[1]
            else:
                raise DocumentMergeConflict(path + "/order")
            merged = {}
            for key in set(maps[0]) | set(maps[1]) | set(maps[2]):
                value = _merge(maps[0].get(key, _MISSING), maps[1].get(key, _MISSING),
                               maps[2].get(key, _MISSING), path + "/" + text_type(key))
                if value is not _MISSING:
                    merged[key] = value
            return [merged[key] for key in order if key in merged]
    raise DocumentMergeConflict(path)


def prepare_document_commit(base, staged, current):
    """Keep current changes absent from the editor delta; reject competing edits."""
    document = normalize_document(_merge(authored_document(base), authored_document(staged),
                                        authored_document(current), "document"))
    ids, names = set(), set()
    for item in walk_items(document, include_sections=True):
        if item["id"] in ids or item["name"] in names:
            raise DocumentMergeConflict("document/identity/" + item["name"])
        ids.add(item["id"])
        names.add(item["name"])
    return document
