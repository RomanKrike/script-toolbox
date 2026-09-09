# -*- coding: utf-8 -*-

from . import items as _items
from .layouts import CONTAINER_KINDS
from .layouts import LAYOUT_KINDS
from .layouts import install_layout_kinds
from .layouts import is_container_kind
from .layouts import is_layout_kind
from .toggle_button import install_toggle_button_kind


# Install Toggle Button first because Toggle Icon deliberately chains on top of
# its state-binding compatibility wrappers.
install_toggle_button_kind()

from .toggle_icon import install_toggle_icon_kind

install_toggle_icon_kind()
install_layout_kinds()

# Import after kind installation so DocumentIndex binds the extended
# walk_items implementation that traverses Row / Column subtrees and sees the
# dedicated stateful item kinds as first-class controls.
from .index import DocumentIndex

create_item = _items.create_item
normalize_document = _items.normalize_document
walk_items = _items.walk_items


__all__ = [
    "CONTAINER_KINDS",
    "DocumentIndex",
    "LAYOUT_KINDS",
    "create_item",
    "is_container_kind",
    "is_layout_kind",
    "normalize_document",
    "walk_items",
]
