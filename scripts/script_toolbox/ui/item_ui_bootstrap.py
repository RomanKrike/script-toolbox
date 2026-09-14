# -*- coding: utf-8 -*-
from __future__ import print_function

import importlib

from ..model.item_builtins import register_builtin_items
from ..model.item_registry import ITEM_TYPES


_BOOTSTRAPPED = False


def _resolve_ui_target(path):
    if not path:
        return None
    module_name, separator, attribute = path.partition(":")
    if not separator or not module_name or not attribute:
        raise ValueError(
            "Invalid Item UI target: {0!r}".format(path)
        )
    module = importlib.import_module(module_name, __package__)
    return getattr(module, attribute)


def ensure_builtin_item_ui_bindings():
    """Resolve declarative Qt-side bindings stored on Item definitions."""
    global _BOOTSTRAPPED
    if _BOOTSTRAPPED:
        return ITEM_TYPES

    register_builtin_items()

    for definition in ITEM_TYPES.all():
        renderer = (
            _resolve_ui_target(definition.renderer_path)
            if definition.renderer_path
            else definition.renderer
        )
        inspector = (
            _resolve_ui_target(definition.inspector_path)
            if definition.inspector_path
            else definition.inspector
        )
        if renderer is not None or inspector is not None:
            ITEM_TYPES.bind_ui(
                definition.kind,
                renderer=renderer,
                inspector=inspector
            )

    _BOOTSTRAPPED = True
    return ITEM_TYPES


__all__ = [
    "ensure_builtin_item_ui_bindings",
]
