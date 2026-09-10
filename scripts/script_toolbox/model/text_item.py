# -*- coding: utf-8 -*-
from __future__ import print_function

from ..pycompat import text_type
from .items import base_item


DEFAULT_TEXT = "Text"


def create_text_item(data=None):
    """Normalize a static multiline explanatory text item."""
    data = data or {}
    item = base_item(
        "text",
        data,
        "Text"
    )

    content = data.get("text")
    if content is None:
        content = DEFAULT_TEXT

    item.update({
        "show_label": False,
        "text": text_type(content),
        "bindings": [],
    })
    return item


__all__ = [
    "DEFAULT_TEXT",
    "create_text_item",
]
