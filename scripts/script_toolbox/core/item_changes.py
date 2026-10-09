# -*- coding: utf-8 -*-
"""Validated Item edits independent of Qt, persistence and script execution."""
from __future__ import print_function

import copy

from ..model.item_builtins import register_builtin_items
from ..model.item_registry import ITEM_TYPES, ItemValidationError
from ..model.items import ITEM_UI_FIELDS, walk_items
from ..pycompat import text_type


def resolve_item(document, key):
    items = list(walk_items(document, include_sections=True))
    for field in ("id", "name"):
        for item in items:
            if item.get(field) == text_type(key):
                return item
    raise KeyError("Item not found: {0}".format(key))


def property_location(item, name):
    register_builtin_items()
    definition = ITEM_TYPES.get(item["kind"], required=True)
    if name in ("id", "kind", "name", "bindings"):
        raise ValueError("Property is not writable through Item.set: " + name)
    if name in definition.fields:
        return "props"
    if name in ITEM_UI_FIELDS:
        return "ui"
    raise ValueError("Unknown {0} property: {1}".format(item["kind"], name))


class ItemChange(object):
    def __init__(self, item, before, after):
        self.item_id = item["id"]
        self.before = before
        self.after = after
        self.fields = frozenset(after)

    @property
    def changed(self):
        return bool(self.fields)


def update_item(item, properties):
    """Validate a complete candidate, then commit all changes together."""
    register_builtin_items()
    definition = ITEM_TYPES.get(item["kind"], required=True)
    candidate = dict((section, copy.deepcopy(item.get(section, {})))
                     for section in ("props", "ui"))
    touched = set()
    for name, value in properties.items():
        if "." in name:
            section, name = name.split(".", 1)
            schema = definition.fields if section == "props" else ITEM_UI_FIELDS if section == "ui" else {}
            if name not in schema:
                raise ValueError("Unknown property: " + section + "." + name)
        else:
            section = property_location(item, name)
        if section == "props" and name == "value":
            if not definition.has_capability("has_value"):
                raise ValueError("This Item does not expose a value")
        if item.get("_preset_reference") and (section, name) != ("props", "value"):
            raise ValueError("Referenced preset definition is read-only")
        if section == "ui":
            try:
                value = ITEM_UI_FIELDS[name].normalize(value)
            except ValueError as exc:
                raise ItemValidationError(item["kind"], name, value, text_type(exc), item["id"], item.get("name"))
        candidate[section][name] = copy.deepcopy(value)
        touched.add(section)
    if ("value" in properties or "props.value" in properties) and definition.has_capability("state_toggle") and candidate["props"].get("state_source", "internal") != "internal":
        raise ValueError("Script-controlled toggle value is read-only")
    if "props" in touched:
        candidate["props"] = definition.normalize_props(
            candidate["props"], item_id=item["id"], item_name=item.get("name"))
    whole_candidate = copy.deepcopy(item)
    whole_candidate.update(candidate)
    candidate["props"] = definition.normalize_item(whole_candidate)["props"]
    before, after = {}, {}
    for section in touched:
        old = item.get(section, {})
        for name, value in candidate[section].items():
            if old.get(name) != value:
                path = section + "." + name
                before[path] = copy.deepcopy(old.get(name))
                after[path] = copy.deepcopy(value)
    change = ItemChange(item, before, after)
    if change.changed:
        for section in touched:
            current = item.get(section)
            if isinstance(current, dict):
                current.clear()
                current.update(candidate[section])
            else:
                item[section] = candidate[section]
    return change


class Item(object):
    """A document-scoped handle; never owns a widget or a copy of Item data."""
    def __init__(self, owner, key):
        self._owner = owner
        self._document = owner.config
        self._id = resolve_item(self._document, key)["id"]

    def _resolve(self):
        if self._owner.config is not self._document:
            raise RuntimeError("Item belongs to a replaced document")
        return resolve_item(self._document, self._id)

    def __getattr__(self, name):
        item = self._resolve()
        if name in ("id", "name", "kind"):
            return item[name]
        try:
            section = property_location(item, name)
        except ValueError as exc:
            raise AttributeError(text_type(exc))
        return copy.deepcopy(item.get(section, {}).get(name))

    def __setattr__(self, name, value):
        if not name.startswith("_"):
            raise AttributeError("Use Item.set({0}=...)".format(name))
        object.__setattr__(self, name, value)

    def set(self, **properties):
        self._resolve()
        return self._owner.change_item(self._id, properties)

    def table(self):
        """Return the typed row/cell API for a spreadsheet Item."""
        from .table_api import Table
        if self._resolve()['kind'] != 'table':
            raise TypeError('Item is not a Table')
        return Table(self)
