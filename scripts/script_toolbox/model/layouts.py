# -*- coding: utf-8 -*-
from __future__ import print_function

from ..pycompat import text_type
from . import bindings as bindings_module
from . import items as items_module


LAYOUT_KINDS = (
    "row",
    "column",
)
CONTAINER_KINDS = (
    "folder",
    "row",
    "column",
)

ROW_DISTRIBUTIONS = (
    "left",
    "center",
    "right",
    "space_between",
)
COLUMN_DISTRIBUTIONS = (
    "top",
    "center",
    "bottom",
    "space_between",
)
COLUMN_HEIGHT_MODES = (
    "auto",
    "stretch",
    "fixed",
)

_ORIGINAL_CREATE_ITEM = items_module.create_item
_INSTALLED = False


def is_layout_kind(kind):
    return text_type(kind or "").lower() in LAYOUT_KINDS


def is_container_kind(kind):
    return text_type(kind or "").lower() in CONTAINER_KINDS


def _safe_choice(value, choices, fallback):
    value = text_type(value or fallback).lower()
    return value if value in choices else fallback


def _create_layout_child(raw):
    if not isinstance(raw, dict):
        return None

    kind = text_type(
        raw.get("kind", "button")
    ).lower()

    # Folders remain structural sections. Row / Column are composable
    # layout containers and may nest inside each other.
    if kind in ("folder", "section"):
        return None

    return create_item(
        kind,
        raw
    )


def _layout_children(data):
    children = []

    for raw in data.get("items", []) or []:
        child = _create_layout_child(raw)
        if child is not None:
            children.append(child)

    return children


def _legacy_row_distribution(data):
    """Infer the old per-child Row alignment when the intent is unambiguous."""
    raw_items = data.get("items", []) or []
    legacy = []

    for raw in raw_items:
        if not isinstance(raw, dict):
            continue

        value = text_type(
            raw.get("row_alignment", "")
        ).lower()
        if value in ("center", "right"):
            legacy.append(value)
        elif value == "left":
            legacy.append("left")

    if legacy and all(
        value == legacy[0]
        for value in legacy
    ):
        return legacy[0]

    return "left"


def _column_child_layout(child):
    child["column_height_mode"] = _safe_choice(
        child.get("column_height_mode", "auto"),
        COLUMN_HEIGHT_MODES,
        "auto"
    )
    child["column_height"] = items_module.clamp(
        items_module.safe_int(
            child.get("column_height"),
            28
        ),
        8,
        2000
    )
    child["column_stretch"] = items_module.clamp(
        items_module.safe_int(
            child.get("column_stretch"),
            1
        ),
        1,
        100
    )
    return child


def _row(data):
    item = items_module.base_item(
        "row",
        data,
        "Row"
    )

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
        # Pre-layout-contract configs stored horizontal intent on individual
        # children as row_alignment. Preserve a common value when possible.
        horizontal_distribution = _legacy_row_distribution(data)

    item.update({
        "spacing": items_module.clamp(
            items_module.safe_int(
                data.get("spacing"),
                4
            ),
            0,
            30
        ),
        "equal_widths": bool(
            data.get("equal_widths", False)
        ),
        "horizontal_distribution": horizontal_distribution,
        "vertical_alignment": vertical_alignment,
        "items": _layout_children(data),
    })
    return item


def _column(data):
    item = items_module.base_item(
        "column",
        data,
        "Column"
    )

    # A Column is most useful as a cell inside Row. Defaulting its Row width
    # mode to Stretch makes sibling columns share the available width without
    # requiring extra setup; users can still choose Auto / Fixed explicitly.
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

        # Base item factories intentionally ignore unknown layout-context
        # fields. Reapply the raw Column child settings before normalizing
        # them so Fixed/Stretch values survive item creation.
        for key in (
            "column_height_mode",
            "column_height",
            "column_stretch",
        ):
            if key in raw:
                child[key] = raw[key]

        children.append(
            _column_child_layout(child)
        )

    item.update({
        "spacing": items_module.clamp(
            items_module.safe_int(
                data.get("spacing"),
                4
            ),
            0,
            30
        ),
        "horizontal_alignment": horizontal_alignment,
        "vertical_distribution": vertical_distribution,
        "items": children,
    })
    return item


def create_item(kind, data=None):
    kind = text_type(
        kind or "button"
    ).lower()
    data = data or {}

    if kind == "row":
        return _row(data)
    if kind == "column":
        return _column(data)

    return _ORIGINAL_CREATE_ITEM(
        kind,
        data
    )


def walk_items(document, include_folders=False):
    def walk(children):
        for item in children:
            kind = text_type(
                item.get("kind", "")
            ).lower()

            if include_folders or kind != "folder":
                yield item

            if is_container_kind(kind):
                for child in walk(
                    item.get("items", []) or []
                ):
                    yield child

    for folder in (document or {}).get(
        "sections",
        []
    ) or []:
        if include_folders:
            yield folder

        for item in walk(
            folder.get("items", []) or []
        ):
            yield item


def install_layout_kinds():
    global _INSTALLED

    if _INSTALLED:
        return

    # Patch the items module itself so direct imports such as
    # ``from model.items import create_item`` also see Column support.
    items_module._FACTORIES["row"] = _row
    items_module._FACTORIES["column"] = _column
    items_module.create_item = create_item
    items_module.walk_items = walk_items

    # Layout items intentionally expose no event triggers for now.
    bindings_module.EVENT_CAPABILITIES.setdefault(
        "column",
        ()
    )

    _INSTALLED = True


__all__ = [
    "COLUMN_DISTRIBUTIONS",
    "COLUMN_HEIGHT_MODES",
    "CONTAINER_KINDS",
    "LAYOUT_KINDS",
    "ROW_DISTRIBUTIONS",
    "create_item",
    "install_layout_kinds",
    "is_container_kind",
    "is_layout_kind",
    "walk_items",
]
