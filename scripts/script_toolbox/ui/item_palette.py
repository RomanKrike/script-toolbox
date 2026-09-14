# -*- coding: utf-8 -*-
from __future__ import print_function

from collections import OrderedDict

from ..model.item_builtins import register_builtin_items
from ..model.item_registry import ITEM_TYPES


def palette_groups():
    """Build Interface Editor palette groups from ItemType metadata."""
    register_builtin_items()
    groups = OrderedDict()

    definitions = sorted(
        ITEM_TYPES.creatable(),
        key=lambda definition: (
            definition.category.lower(),
            definition.order,
            definition.title.lower(),
            definition.kind,
        )
    )

    for definition in definitions:
        label = definition.category.upper()
        groups.setdefault(label, []).append((
            definition.title,
            definition.kind,
            definition.description,
        ))

    return tuple(
        (label, tuple(entries))
        for label, entries in groups.items()
    )


__all__ = [
    "palette_groups",
]
