# -*- coding: utf-8 -*-
from __future__ import print_function

import re
import uuid

from ..pycompat import text_type
from ..constants import CONFIG_VERSION
from ..constants import FOLDER_TYPES


def new_id():
    return uuid.uuid4().hex


def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def safe_int(value, fallback=0):
    try:
        return int(value)
    except Exception:
        return int(fallback)


def safe_float(value, fallback=0.0):
    try:
        return float(value)
    except Exception:
        return float(fallback)


def safe_color(value):
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        value = [0.25, 0.25, 0.25]

    return [
        clamp(safe_float(value[0], 0.25), 0.0, 1.0),
        clamp(safe_float(value[1], 0.25), 0.0, 1.0),
        clamp(safe_float(value[2], 0.25), 0.0, 1.0),
    ]


def sanitize_name(value, fallback="item"):
    value = text_type(value or "").strip()

    if not value:
        value = text_type(fallback or "item")

    value = re.sub(r"[^A-Za-z0-9_]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")

    if not value:
        value = "item"

    if value[0].isdigit():
        value = "_" + value

    return value


def default_name(kind, item_id):
    return sanitize_name(
        "{0}_{1}".format(kind, text_type(item_id)[:4]),
        kind,
    )


def safe_menu_items(value):
    if isinstance(value, (list, tuple)):
        result = [
            text_type(item)
            for item in value
            if text_type(item).strip()
        ]
    else:
        value = text_type(value or "")
        result = [
            line.strip()
            for line in value.replace(",", "\n").splitlines()
            if line.strip()
        ]

    if not result:
        result = ["Option 1", "Option 2"]

    return result


def base_item(kind, data=None, default_label=None):
    data = data or {}
    item_id = data.get("id") or new_id()

    legacy_name = data.get("name")
    label = data.get("label")

    if label is None:
        label = legacy_name or default_label or kind.title()

    if legacy_name:
        name = sanitize_name(legacy_name, kind)
    else:
        name = default_name(kind, item_id)

    return {
        "kind": kind,
        "id": item_id,
        "name": name,
        "label": text_type(label),
        "show_label": bool(data.get("show_label", True)),
        "tooltip": text_type(data.get("tooltip") or ""),
    }


def _button(data):
    item = base_item("button", data, "New Button")
    language = text_type(data.get("language", "python")).lower()

    if language not in ("python", "mel"):
        language = "python"

    item.update({
        "language": language,
        "click_script": text_type(data.get("click_script") or ""),
        "shift_script": text_type(data.get("shift_script") or ""),
        "color": safe_color(data.get("color")),
    })
    return item


def _string(data):
    item = base_item("string", data, "String")
    item["value"] = text_type(data.get("value") or "")
    return item


def _integer(data):
    item = base_item("integer", data, "Integer")
    minimum = safe_int(data.get("min"), -1000000)
    maximum = safe_int(data.get("max"), 1000000)

    if minimum > maximum:
        minimum, maximum = maximum, minimum

    item.update({
        "min": minimum,
        "max": maximum,
        "step": max(1, safe_int(data.get("step"), 1)),
        "value": clamp(
            safe_int(data.get("value"), 0),
            minimum,
            maximum,
        ),
    })
    return item


def _float(data):
    item = base_item("float", data, "Float")
    minimum = safe_float(data.get("min"), -1000000.0)
    maximum = safe_float(data.get("max"), 1000000.0)

    if minimum > maximum:
        minimum, maximum = maximum, minimum

    item.update({
        "min": minimum,
        "max": maximum,
        "step": max(0.000001, safe_float(data.get("step"), 0.1)),
        "decimals": clamp(safe_int(data.get("decimals"), 3), 0, 8),
        "value": clamp(
            safe_float(data.get("value"), 0.0),
            minimum,
            maximum,
        ),
    })
    return item


def _checkbox(data):
    item = base_item("checkbox", data, "Checkbox")

    position = text_type(
        data.get("label_position", "right")
    ).lower()

    if position not in ("left", "right"):
        position = "right"

    item.update({
        "value": bool(data.get("value", False)),
        "label_position": position,
    })
    return item


def _legacy_toggle(data):
    migrated = dict(data)
    migrated["kind"] = "checkbox"
    migrated.setdefault("label_position", "left")
    return _checkbox(migrated)


def _menu(data):
    item = base_item("menu", data, "Menu")
    values = safe_menu_items(data.get("items"))
    value = text_type(data.get("value") or "")

    if value not in values:
        value = values[0]

    item.update({
        "items": values,
        "value": value,
    })
    return item


def _color(data):
    item = base_item("color", data, "Color")
    item["value"] = safe_color(data.get("value"))
    return item


def _field(data):
    item = base_item("field", data, "Field")

    source = text_type(data.get("source", "value")).lower()

    if source not in ("value", "selection"):
        source = "value"

    value = data.get("value", "")

    if isinstance(value, tuple):
        value = list(value)

    item.update({
        "source": source,
        "value": value,
        "placeholder": text_type(data.get("placeholder") or ""),
        "selectable": bool(data.get("selectable", True)),
        "select_scene": bool(data.get("select_scene", False)),
        "multiple": bool(data.get("multiple", True)),
        "long_names": bool(data.get("long_names", False)),
    })
    return item


def _label(data):
    return base_item("label", data, "Label")


def _separator(data):
    item = base_item("separator", data, "Separator")
    item.pop("tooltip", None)
    return item


def _row(data):
    item = base_item("row", data, "Row")
    children = []

    for raw in data.get("items", []) or []:
        if not isinstance(raw, dict):
            continue

        kind = text_type(raw.get("kind", "button")).lower()

        if kind in ("row", "folder", "section"):
            continue

        children.append(create_item(kind, raw))

    item.update({
        "spacing": clamp(safe_int(data.get("spacing"), 4), 0, 30),
        "items": children,
    })
    return item


def _folder(data):
    item = base_item("folder", data, "Folder")
    folder_type = text_type(
        data.get("folder_type", "collapsible")
    ).lower()

    if folder_type not in FOLDER_TYPES:
        folder_type = "collapsible"

    children = []

    for raw in data.get("items", []) or []:
        if not isinstance(raw, dict):
            continue

        kind = text_type(raw.get("kind", "button")).lower()
        children.append(create_item(kind, raw))

    item.update({
        "folder_type": folder_type,
        "collapsed": bool(data.get("collapsed", False)),
        "items": children,
    })
    return item


_FACTORIES = {
    "button": _button,
    "string": _string,
    "integer": _integer,
    "float": _float,
    "toggle": _legacy_toggle,
    "checkbox": _checkbox,
    "menu": _menu,
    "color": _color,
    "field": _field,
    "label": _label,
    "separator": _separator,
    "row": _row,
    "folder": _folder,
    "section": _folder,
}


def create_item(kind, data=None):
    kind = text_type(kind or "button").lower()
    factory = _FACTORIES.get(kind, _button)
    return factory(data or {})


def default_document():
    return {
        "version": CONFIG_VERSION,
        "sections": [
            _folder({
                "name": "my_tools",
                "label": "My Tools",
                "folder_type": "collapsible",
            })
        ],
    }


def normalize_document(data):
    if not isinstance(data, dict):
        return default_document()

    raw_folders = data.get("sections")

    if raw_folders is None:
        raw_folders = data.get("folders")

    if not isinstance(raw_folders, list):
        raw_folders = []

    folders = []

    for raw in raw_folders:
        if not isinstance(raw, dict):
            continue

        migrated = dict(raw)
        migrated["kind"] = "folder"
        folders.append(_folder(migrated))

    if not folders:
        folders = default_document()["sections"]

    return {
        "version": CONFIG_VERSION,
        "sections": folders,
    }


def walk_items(document, include_folders=False):
    def walk(children):
        for item in children:
            if include_folders or item.get("kind") != "folder":
                yield item

            if item.get("kind") in ("folder", "row"):
                for child in walk(item.get("items", [])):
                    yield child

    for folder in document.get("sections", []):
        if include_folders:
            yield folder

        for item in walk(folder.get("items", [])):
            yield item
