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

_ORIGINAL_CREATE_ITEM = items_module.create_item
_INSTALLED = False


def is_layout_kind(kind):
    return text_type(kind or "").lower() in LAYOUT_KINDS


def is_container_kind(kind):
    return text_type(kind or "").lower() in CONTAINER_KINDS


def _layout_children(data):
    children = []

    for raw in data.get("items", []) or []:
        if not isinstance(raw, dict):
            continue

        kind = text_type(
            raw.get("kind", "button")
        ).lower()

        # Folders remain structural sections. Row / Column are composable
        # layout containers and may nest inside each other.
        if kind in ("folder", "section"):
            continue

        children.append(
            create_item(
                kind,
                raw
            )
        )

    return children


def _row(data):
    item = items_module.base_item(
        "row",
        data,
        "Row"
    )

    vertical_alignment = text_type(
        data.get("vertical_alignment", "center")
    ).lower()
    if vertical_alignment not in (
        "top",
        "center",
        "bottom",
    ):
        vertical_alignment = "center"

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

    horizontal_alignment = text_type(
        data.get("horizontal_alignment", "stretch")
    ).lower()
    if horizontal_alignment not in (
        "stretch",
        "left",
        "center",
        "right",
    ):
        horizontal_alignment = "stretch"

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
        "items": _layout_children(data),
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
    "CONTAINER_KINDS",
    "LAYOUT_KINDS",
    "create_item",
    "install_layout_kinds",
    "is_container_kind",
    "is_layout_kind",
    "walk_items",
]
