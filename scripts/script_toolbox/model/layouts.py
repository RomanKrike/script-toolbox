# -*- coding: utf-8 -*-
from __future__ import print_function

from .item_builtins import register_builtin_items
from .item_registry import ITEM_TYPES


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


def is_layout_kind(kind):
    register_builtin_items()
    definition = ITEM_TYPES.get(kind)
    return bool(definition and definition.is_layout)


def is_container_kind(kind):
    register_builtin_items()
    definition = ITEM_TYPES.get(kind)
    return bool(definition and definition.is_container)


__all__ = [
    "COLUMN_DISTRIBUTIONS",
    "COLUMN_HEIGHT_MODES",
    "ROW_DISTRIBUTIONS",
    "is_container_kind",
    "is_layout_kind",
]
