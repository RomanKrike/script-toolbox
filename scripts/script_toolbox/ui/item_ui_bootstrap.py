# -*- coding: utf-8 -*-
from __future__ import print_function

import importlib

from ..model.item_builtins import register_builtin_items
from ..model.item_registry import ITEM_TYPES


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
    """Resolve Qt-side bindings for every currently registered Item type.

    The pass is intentionally re-entrant. Built-ins are registered before UI
    composition, while future/external Item definitions may be registered
    later. Already-bound callables are retained; only unresolved declarative
    paths are imported on subsequent passes.
    """
    register_builtin_items()

    for definition in ITEM_TYPES.all():
        renderer = definition.renderer
        inspector = definition.inspector

        if renderer is None and definition.renderer_path:
            renderer = _resolve_ui_target(definition.renderer_path)
        if inspector is None and definition.inspector_path:
            inspector = _resolve_ui_target(definition.inspector_path)

        if (
            renderer is not definition.renderer or
            inspector is not definition.inspector
        ):
            ITEM_TYPES.bind_ui(
                definition.kind,
                renderer=renderer,
                inspector=inspector
            )

    return ITEM_TYPES


__all__ = [
    "ensure_builtin_item_ui_bindings",
]
