# -*- coding: utf-8 -*-
from __future__ import print_function

import re
import uuid

from ..pycompat import text_type
from ..constants import CONFIG_VERSION
from ..constants import FOLDER_TYPES
from .bindings import normalize_bindings
from .layouts import COLUMN_DISTRIBUTIONS
from .layouts import COLUMN_HEIGHT_MODES
from .layouts import ROW_DISTRIBUTIONS
from .layouts import is_container_kind


DEFAULT_COMPONENT_LABELS = (
    "X",
    "Y",
    "Z",
    "W",
)


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


def safe_numeric_size(value):
    return clamp(
        safe_int(value, 1),
        1,
        4
    )


def safe_component_labels(value, size):
    size = safe_numeric_size(size)

    if isinstance(value, (list, tuple)):
        labels = [
            text_type(entry).strip()
            for entry in value
        ]
    else:
        raw = text_type(value or "")
        labels = [
            part.strip()
            for part in raw.replace(";", ",").split(",")
        ] if raw.strip() else []

    result = []
    for index in range(size):
        if index < len(labels) and labels[index]:
            result.append(labels[index])
        else:
            result.append(DEFAULT_COMPONENT_LABELS[index])

    return result


def normalize_numeric_value(
    value,
    size,
    minimum,
    maximum,
    caster,
    fallback
):
    """Normalize scalar/vector numeric values using one shared contract."""
    size = safe_numeric_size(size)

    if isinstance(value, (list, tuple)):
        incoming = list(value)
    else:
        incoming = [value] * size

    if isinstance(fallback, (list, tuple)):
        fallback_values = list(fallback)
    else:
        fallback_values = [fallback] * size

    normalized = []
    for index in range(size):
        current_fallback = (
            fallback_values[index]
            if index < len(fallback_values)
            else 0
        )
        current = (
            incoming[index]
            if index < len(incoming)
            else current_fallback
        )
        normalized.append(
            clamp(
                caster(current, current_fallback),
                minimum,
                maximum
            )
        )

    if size == 1:
        return normalized[0]

    return normalized


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
        "bindings": normalize_bindings(kind, data),
        "row_width_mode": (
            text_type(data.get("row_width_mode", "auto")).lower()
            if text_type(data.get("row_width_mode", "auto")).lower()
            in ("auto", "stretch", "fixed")
            else "auto"
        ),
        "row_width": clamp(safe_int(data.get("row_width"), 120), 20, 2000),
        "row_stretch": clamp(safe_int(data.get("row_stretch"), 1), 1, 100),
        "row_alignment": (
            text_type(data.get("row_alignment", "left")).lower()
            if text_type(data.get("row_alignment", "left")).lower()
            in ("left", "center", "right")
            else "left"
        ),
    }


def _button(data):
    mode = text_type(data.get("mode", "action")).lower()

    if mode not in ("action", "state"):
        mode = "action"

    normalized_data = dict(data)
    normalized_data["mode"] = mode
    item = base_item("button", normalized_data, "New Button")

    legacy_language = text_type(
        data.get("language", "python")
    ).lower()
    if legacy_language not in ("python", "mel"):
        legacy_language = "python"

    state_on_language = text_type(
        data.get("state_on_language", legacy_language)
    ).lower()
    state_off_language = text_type(
        data.get("state_off_language", legacy_language)
    ).lower()

    if state_on_language not in ("python", "mel"):
        state_on_language = "python"
    if state_off_language not in ("python", "mel"):
        state_off_language = "python"

    item.update({
        "mode": mode,
        "color": safe_color(data.get("color")),
        "icon_path": text_type(data.get("icon_path") or ""),
        "icon_size": clamp(safe_int(data.get("icon_size"), 18), 8, 256),
        "icon_only": bool(data.get("icon_only", False)),
        "state_get_script": text_type(data.get("state_get_script") or ""),
        "state_get_language": "python",
        "state_on_script": text_type(data.get("state_on_script") or ""),
        "state_on_language": state_on_language,
        "state_off_script": text_type(data.get("state_off_script") or ""),
        "state_off_language": state_off_language,
        "state_on_label": text_type(
            data.get("state_on_label") or
            "{0}: ON".format(item.get("label", "State"))
        ),
        "state_off_label": text_type(
            data.get("state_off_label") or
            "{0}: OFF".format(item.get("label", "State"))
        ),
        "state_on_color": safe_color(
            data.get("state_on_color") or [0.22, 0.42, 0.26]
        ),
        "state_off_color": safe_color(
            data.get("state_off_color") or [0.30, 0.30, 0.30]
        ),
    })
    return item


def _icon(data):
    item = base_item("icon", data, "Icon")
    alignment = text_type(
        data.get(
            "content_alignment",
            data.get("alignment", "left")
        )
    ).lower()
    if alignment not in ("left", "center", "right"):
        alignment = "left"

    item.update({
        "show_label": bool(data.get("show_label", False)),
        "path": text_type(data.get("path") or ""),
        "width": clamp(safe_int(data.get("width"), 24), 8, 512),
        "height": clamp(safe_int(data.get("height"), 24), 8, 512),
        "content_alignment": alignment,
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

    size = safe_numeric_size(data.get("size", 1))
    item.update({
        "min": minimum,
        "max": maximum,
        "step": max(1, safe_int(data.get("step"), 1)),
        "size": size,
        "component_labels": safe_component_labels(
            data.get("component_labels"),
            size
        ),
        "show_slider": bool(data.get("show_slider", False)),
        "value": normalize_numeric_value(
            data.get("value", 0),
            size,
            minimum,
            maximum,
            safe_int,
            0
        ),
    })
    return item


def _float(data):
    item = base_item("float", data, "Float")
    minimum = safe_float(data.get("min"), -1000000.0)
    maximum = safe_float(data.get("max"), 1000000.0)

    if minimum > maximum:
        minimum, maximum = maximum, minimum

    size = safe_numeric_size(data.get("size", 1))
    item.update({
        "min": minimum,
        "max": maximum,
        "step": max(0.000001, safe_float(data.get("step"), 0.1)),
        "decimals": clamp(safe_int(data.get("decimals"), 3), 0, 8),
        "size": size,
        "component_labels": safe_component_labels(
            data.get("component_labels"),
            size
        ),
        "show_slider": bool(data.get("show_slider", False)),
        "value": normalize_numeric_value(
            data.get("value", 0.0),
            size,
            minimum,
            maximum,
            safe_float,
            0.0
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

    multiple = bool(data.get("multiple", True))

    if not multiple and isinstance(value, list):
        value = value[0] if value else ""

    display_mode = text_type(
        data.get(
            "display_mode",
            "list" if multiple else "single"
        )
    ).lower()

    if display_mode not in ("single", "list"):
        display_mode = "list" if multiple else "single"

    if not multiple:
        display_mode = "single"

    item.update({
        "source": source,
        "value": value,
        "placeholder": text_type(data.get("placeholder") or ""),
        "selectable": bool(data.get("selectable", True)),
        "select_scene": bool(data.get("select_scene", False)),
        "multiple": multiple,
        "long_names": bool(data.get("long_names", False)),
        "display_mode": display_mode,
        "visible_rows": clamp(
            safe_int(data.get("visible_rows"), 4),
            1,
            20
        ),
    })
    return item


def _label(data):
    return base_item("label", data, "Label")


def _separator(data):
    item = base_item("separator", data, "Separator")
    item.pop("tooltip", None)
    return item


def _safe_choice(value, choices, fallback):
    value = text_type(value or fallback).lower()
    return value if value in choices else fallback


def _create_layout_child(raw):
    if not isinstance(raw, dict):
        return None

    kind = text_type(raw.get("kind", "button")).lower()
    if kind in ("folder", "section"):
        return None

    return create_item(kind, raw)


def _layout_children(data):
    children = []
    for raw in data.get("items", []) or []:
        child = _create_layout_child(raw)
        if child is not None:
            children.append(child)
    return children


def _legacy_row_distribution(data):
    raw_items = data.get("items", []) or []
    legacy = []

    for raw in raw_items:
        if not isinstance(raw, dict):
            continue
        value = text_type(raw.get("row_alignment", "")).lower()
        if value in ("left", "center", "right"):
            legacy.append(value)

    if legacy and all(value == legacy[0] for value in legacy):
        return legacy[0]
    return "left"


def _column_child_layout(child):
    child["column_height_mode"] = _safe_choice(
        child.get("column_height_mode", "auto"),
        COLUMN_HEIGHT_MODES,
        "auto"
    )
    child["column_height"] = clamp(
        safe_int(child.get("column_height"), 28),
        8,
        2000
    )
    child["column_stretch"] = clamp(
        safe_int(child.get("column_stretch"), 1),
        1,
        100
    )
    return child


def _row(data):
    item = base_item("row", data, "Row")
    vertical_alignment = _safe_choice(
        data.get("vertical_alignment", "center"),
        ("top", "center", "bottom"),
        "center"
    )

    if "horizontal_distribution" in data:
        horizontal_distribution = _safe_choice(
            data.get("horizontal_distribution"),
            ROW_DISTRIBUTIONS,
            "left"
        )
    else:
        horizontal_distribution = _legacy_row_distribution(data)

    item.update({
        "spacing": clamp(safe_int(data.get("spacing"), 4), 0, 30),
        "equal_widths": bool(data.get("equal_widths", False)),
        "horizontal_distribution": horizontal_distribution,
        "vertical_alignment": vertical_alignment,
        "items": _layout_children(data),
    })
    return item


def _column(data):
    item = base_item("column", data, "Column")

    if "row_width_mode" not in data:
        item["row_width_mode"] = "stretch"

    horizontal_alignment = _safe_choice(
        data.get("horizontal_alignment", "stretch"),
        ("stretch", "left", "center", "right"),
        "stretch"
    )
    vertical_distribution = _safe_choice(
        data.get("vertical_distribution", "top"),
        COLUMN_DISTRIBUTIONS,
        "top"
    )

    children = []
    for raw in data.get("items", []) or []:
        child = _create_layout_child(raw)
        if child is None:
            continue

        for key in (
            "column_height_mode",
            "column_height",
            "column_stretch",
        ):
            if key in raw:
                child[key] = raw[key]

        children.append(_column_child_layout(child))

    item.update({
        "spacing": clamp(safe_int(data.get("spacing"), 4), 0, 30),
        "horizontal_alignment": horizontal_alignment,
        "vertical_distribution": vertical_distribution,
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
    "icon": _icon,
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
    "column": _column,
    "folder": _folder,
    "section": _folder,
}


def register_item_factory(kind, factory, replace=False):
    """Register an item factory through the public model registry API."""
    kind = text_type(kind or "").lower()
    if not kind:
        raise ValueError("Item kind must not be empty.")
    if not callable(factory):
        raise TypeError("Item factory must be callable.")
    if kind in _FACTORIES and not replace:
        raise ValueError(
            "Item factory already registered: {0}".format(kind)
        )
    _FACTORIES[kind] = factory
    return factory


def get_item_factory(kind):
    return _FACTORIES.get(text_type(kind or "").lower())


def create_item(kind, data=None):
    kind = text_type(kind or "button").lower()
    factory = get_item_factory(kind) or _button
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
    """Yield document items using the canonical container-kind contract."""
    def walk(children):
        for item in children:
            kind = text_type(item.get("kind", "")).lower()
            if include_folders or kind != "folder":
                yield item

            if is_container_kind(kind):
                for child in walk(item.get("items", []) or []):
                    yield child

    for folder in (document or {}).get("sections", []) or []:
        if include_folders:
            yield folder

        for item in walk(folder.get("items", []) or []):
            yield item


__all__ = [
    "DEFAULT_COMPONENT_LABELS",
    "base_item",
    "clamp",
    "create_item",
    "default_document",
    "get_item_factory",
    "is_container_kind",
    "new_id",
    "normalize_document",
    "normalize_numeric_value",
    "register_item_factory",
    "safe_color",
    "safe_component_labels",
    "safe_float",
    "safe_int",
    "safe_menu_items",
    "safe_numeric_size",
    "sanitize_name",
    "walk_items",
]
