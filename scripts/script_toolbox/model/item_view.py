# -*- coding: utf-8 -*-
from __future__ import print_function

from ..pycompat import text_type


_ROOT_KEYS = frozenset((
    "kind",
    "id",
    "name",
    "bindings",
    "items",
))

_UI_KEYS = frozenset((
    "label",
    "show_label",
    "tooltip",
    "width_mode",
    "width",
    "stretch",
    "alignment",
    "height_mode",
    "height",
    "vertical_stretch",
))

# Inspector/runtime code uses placement-oriented names. They are a view API,
# not serialized keys; the persisted document remains ui/props-only.
_UI_ALIASES = {
    "row_width_mode": "width_mode",
    "row_width": "width",
    "row_stretch": "stretch",
    "row_alignment": "alignment",
    "column_height_mode": "height_mode",
    "column_height": "height",
    "column_stretch": "vertical_stretch",
}


class ItemDataView(object):
    """Mutable view over the universal Item envelope.

    Root identity/tree fields stay at the root, presentation fields resolve to
    ``ui`` and all type-specific fields resolve to ``props``. This keeps Qt and
    runtime code concise without reintroducing type-specific root JSON keys.
    """

    def __init__(self, item):
        if not isinstance(item, dict):
            raise TypeError("ItemDataView expects a dict item.")
        self.item = item

    def _target(self, key, create=False):
        key = text_type(key or "")
        if key in _ROOT_KEYS:
            return self.item, key
        ui_key = _UI_ALIASES.get(key, key)
        if ui_key in _UI_KEYS:
            if create:
                self.item.setdefault("ui", {})
            return self.item.get("ui", {}), ui_key
        if create:
            self.item.setdefault("props", {})
        return self.item.get("props", {}), key

    def get(self, key, default=None):
        target, resolved = self._target(key)
        return target.get(resolved, default)

    def __getitem__(self, key):
        target, resolved = self._target(key)
        return target[resolved]

    def __setitem__(self, key, value):
        target, resolved = self._target(key, create=True)
        target[resolved] = value

    def __contains__(self, key):
        target, resolved = self._target(key)
        return resolved in target

    def pop(self, key, default=None):
        target, resolved = self._target(key, create=True)
        return target.pop(resolved, default)

    def setdefault(self, key, default=None):
        target, resolved = self._target(key, create=True)
        return target.setdefault(resolved, default)

    def keys(self):
        result = []
        for key in self.item.keys():
            if key not in ("ui", "props") and key not in result:
                result.append(key)
        for key in self.item.get("ui", {}).keys():
            if key not in result:
                result.append(key)
        for key in self.item.get("props", {}).keys():
            if key not in result:
                result.append(key)
        return result

    def items(self):
        return [(key, self.get(key)) for key in self.keys()]

    def __iter__(self):
        return iter(self.keys())

    def raw(self):
        return self.item


def item_view(item):
    if isinstance(item, ItemDataView):
        return item
    return ItemDataView(item)


__all__ = [
    "ItemDataView",
    "item_view",
]
