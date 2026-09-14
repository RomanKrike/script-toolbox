# -*- coding: utf-8 -*-
from __future__ import print_function

import re
import uuid

from ..constants import CONFIG_VERSION
from ..pycompat import text_type
from .fields import BoolField
from .fields import ChoiceField
from .fields import IntField
from .fields import TextField
from .item_builtins import register_builtin_items
from .item_registry import ITEM_TYPES


DEFAULT_COMPONENT_LABELS = ("X", "Y", "Z", "W")


_UI_FIELDS = {
    "label": TextField(default=""),
    "show_label": BoolField(default=True),
    "tooltip": TextField(default=""),
    "width_mode": ChoiceField(("auto", "stretch", "fixed"), default="auto"),
    "width": IntField(default=120, minimum=20, maximum=2000),
    "stretch": IntField(default=1, minimum=1, maximum=100),
    "alignment": ChoiceField(("left", "center", "right"), default="left"),
    "height_mode": ChoiceField(("auto", "stretch", "fixed"), default="auto"),
    "height": IntField(default=28, minimum=8, maximum=2000),
    "vertical_stretch": IntField(default=1, minimum=1, maximum=100),
}


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


def safe_menu_items(value):
    if isinstance(value, (list, tuple)):
        result = [
            text_type(item)
            for item in value
            if text_type(item).strip()
        ]
    else:
        raw = text_type(value or "")
        result = [
            line.strip()
            for line in raw.replace(",", "\n").splitlines()
            if line.strip()
        ]
    return result or ["Option 1", "Option 2"]


def safe_numeric_size(value):
    return clamp(safe_int(value, 1), 1, 4)


def safe_component_labels(value, size):
    size = safe_numeric_size(size)
    if isinstance(value, (list, tuple)):
        labels = [text_type(entry).strip() for entry in value]
    else:
        raw = text_type(value or "")
        labels = [
            part.strip()
            for part in raw.replace(";", ",").split(",")
        ] if raw.strip() else []
    return [
        labels[index] if index < len(labels) and labels[index]
        else DEFAULT_COMPONENT_LABELS[index]
        for index in range(size)
    ]


def normalize_numeric_value(
    value,
    size,
    minimum,
    maximum,
    caster,
    fallback
):
    size = safe_numeric_size(size)
    incoming = list(value) if isinstance(value, (list, tuple)) else [value] * size
    fallback_values = (
        list(fallback)
        if isinstance(fallback, (list, tuple))
        else [fallback] * size
    )
    result = []
    for index in range(size):
        current_fallback = (
            fallback_values[index]
            if index < len(fallback_values)
            else 0
        )
        current = incoming[index] if index < len(incoming) else current_fallback
        result.append(
            clamp(
                caster(current, current_fallback),
                minimum,
                maximum
            )
        )
    return result[0] if size == 1 else result


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


def _normalize_ui(definition, raw_ui=None):
    raw_ui = raw_ui if isinstance(raw_ui, dict) else {}
    defaults = dict(definition.ui_defaults or {})
    normalized = {}
    for name, field in _UI_FIELDS.items():
        if name == "label":
            fallback = defaults.get(name, definition.default_label)
            value = raw_ui.get(name, fallback)
            normalized[name] = text_type(value if value is not None else fallback)
            continue
        value = raw_ui.get(name, defaults.get(name))
        normalized[name] = field.normalize(value)
    return normalized


def base_item(kind, data=None, default_label=None):
    """Create the stable universal Item envelope for a registered type."""
    register_builtin_items()
    data = data if isinstance(data, dict) else {}
    definition = ITEM_TYPES.get(kind, required=True)
    item_id = text_type(data.get("id") or new_id())
    name = sanitize_name(
        data.get("name") or default_name(definition.kind, item_id),
        definition.kind
    )
    raw_ui = dict(data.get("ui") or {})
    if default_label is not None and "label" not in raw_ui:
        raw_ui["label"] = text_type(default_label)
    ui = _normalize_ui(definition, raw_ui)

    return {
        "kind": definition.kind,
        "id": item_id,
        "name": name,
        "ui": ui,
        "props": definition.normalize_props(data.get("props")),
        "bindings": [],
    }


def create_item(kind, data=None):
    register_builtin_items()
    data = data if isinstance(data, dict) else {}
    definition = ITEM_TYPES.get(kind, required=True)
    item = base_item(definition.kind, data)

    raw_bindings = data.get("bindings")
    if raw_bindings is None:
        raw_bindings = definition.default_bindings()

    from .bindings import normalize_bindings
    item["bindings"] = normalize_bindings(
        definition.kind,
        {"bindings": raw_bindings}
    )

    if definition.is_container:
        children = []
        for raw in data.get("items", []) or []:
            if not isinstance(raw, dict):
                continue
            child_kind = text_type(raw.get("kind") or "").lower()
            if not child_kind:
                continue
            children.append(create_item(child_kind, raw))
        item["items"] = children

    return item


def default_document():
    return {
        "version": CONFIG_VERSION,
        "sections": [
            create_item(
                "folder",
                {
                    "name": "my_tools",
                    "ui": {"label": "My Tools"},
                    "props": {"folder_type": "collapsible"},
                }
            )
        ],
    }


def normalize_document(data):
    register_builtin_items()
    if not isinstance(data, dict):
        return default_document()

    raw_sections = data.get("sections")
    if not isinstance(raw_sections, list):
        raw_sections = []

    sections = []
    for raw in raw_sections:
        if not isinstance(raw, dict):
            continue
        kind = text_type(raw.get("kind") or "").lower()
        definition = ITEM_TYPES.get(kind)
        if definition is None or not definition.has_capability("section"):
            continue
        sections.append(create_item(kind, raw))

    if not sections:
        sections = default_document()["sections"]

    return {
        "version": CONFIG_VERSION,
        "sections": sections,
    }


def walk_items(document, include_folders=False):
    register_builtin_items()

    def walk(children):
        for item in children:
            kind = text_type(item.get("kind") or "").lower()
            definition = ITEM_TYPES.get(kind)
            if definition is None:
                continue
            if include_folders or not definition.has_capability("section"):
                yield item
            if definition.is_container:
                for child in walk(item.get("items", []) or []):
                    yield child

    for section in (document or {}).get("sections", []) or []:
        definition = ITEM_TYPES.get(section.get("kind"))
        if definition is None:
            continue
        if include_folders:
            yield section
        if definition.is_container:
            for item in walk(section.get("items", []) or []):
                yield item


register_builtin_items()


__all__ = [
    "DEFAULT_COMPONENT_LABELS",
    "base_item",
    "clamp",
    "create_item",
    "default_document",
    "default_name",
    "new_id",
    "normalize_document",
    "normalize_numeric_value",
    "safe_color",
    "safe_component_labels",
    "safe_float",
    "safe_int",
    "safe_menu_items",
    "safe_numeric_size",
    "sanitize_name",
    "walk_items",
]
