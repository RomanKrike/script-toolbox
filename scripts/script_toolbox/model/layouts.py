# -*- coding: utf-8 -*-
from __future__ import print_function

from ..pycompat import text_type


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


def is_layout_kind(kind):
    return text_type(kind or "").lower() in LAYOUT_KINDS


def is_container_kind(kind):
    return text_type(kind or "").lower() in CONTAINER_KINDS


__all__ = [
    "COLUMN_DISTRIBUTIONS",
    "COLUMN_HEIGHT_MODES",
    "CONTAINER_KINDS",
    "LAYOUT_KINDS",
    "ROW_DISTRIBUTIONS",
    "is_container_kind",
    "is_layout_kind",
]
