# -*- coding: utf-8 -*-
from __future__ import print_function

import copy

from ..model import create_item
from ..pycompat import text_type


_DCC_ALL = "all"
_SUPPORTED_DCCS = (
    "maya",
    "houdini",
    "nuke",
    "blender",
)


_BUILTIN_PRESETS = (
    {
        "id": "selection_set",
        "dcc": _DCC_ALL,
        "category": "SELECTION",
        "label": "Selection Set",
        "description": (
            "Object list with Add Selected, Remove, Select and Clear actions."
        ),
        "root": {
            "kind": "folder",
            "id": "preset_selection_set_root",
            "name": "selection_set",
            "label": "Selection Set",
            "folder_type": "collapsible",
            "collapsed": False,
            "items": [
                {
                    "kind": "field",
                    "id": "preset_selection_set_objects",
                    "name": "selection_set_objects",
                    "label": "Objects",
                    "source": "value",
                    "multiple": True,
                    "long_names": True,
                    "display_mode": "list",
                    "visible_rows": 5,
                    "placeholder": "Add scene objects...",
                },
                {
                    "kind": "row",
                    "id": "preset_selection_set_actions",
                    "name": "selection_set_actions",
                    "label": "Actions",
                    "items": [
                        {
                            "kind": "button",
                            "id": "preset_selection_set_add",
                            "name": "selection_set_add",
                            "label": "Add Selected",
                            "bindings": [
                                {
                                    "event": "click",
                                    "handler": "script",
                                    "language": "python",
                                    "script": (
                                        "toolbox.add_to_field("
                                        "\"selection_set_objects\", "
                                        "host.current_selection(long_names=True)"
                                        ")"
                                    ),
                                }
                            ],
                        },
                        {
                            "kind": "button",
                            "id": "preset_selection_set_remove",
                            "name": "selection_set_remove",
                            "label": "Remove",
                            "bindings": [
                                {
                                    "event": "click",
                                    "handler": "script",
                                    "language": "python",
                                    "script": (
                                        "toolbox.remove_from_field("
                                        "\"selection_set_objects\""
                                        ")"
                                    ),
                                }
                            ],
                        },
                        {
                            "kind": "button",
                            "id": "preset_selection_set_select",
                            "name": "selection_set_select",
                            "label": "Select",
                            "bindings": [
                                {
                                    "event": "click",
                                    "handler": "script",
                                    "language": "python",
                                    "script": (
                                        "toolbox.select_field_objects("
                                        "\"selection_set_objects\""
                                        ")"
                                    ),
                                }
                            ],
                        },
                        {
                            "kind": "button",
                            "id": "preset_selection_set_clear",
                            "name": "selection_set_clear",
                            "label": "Clear",
                            "bindings": [
                                {
                                    "event": "click",
                                    "handler": "script",
                                    "language": "python",
                                    "script": (
                                        "toolbox.clear_field("
                                        "\"selection_set_objects\""
                                        ")"
                                    ),
                                }
                            ],
                        },
                    ],
                },
            ],
        },
    },
)


def _normalize_dcc(dcc):
    value = text_type(
        dcc or ""
    ).strip().lower()

    if value == _DCC_ALL or value in _SUPPORTED_DCCS:
        return value
    return ""


def iter_presets(dcc=None):
    """Return immutable-order copies of built-in preset metadata.

    When dcc is provided, only presets for that DCC plus universal ``all``
    presets are returned. Unknown DCC identifiers therefore receive only
    universal presets. Omitting dcc preserves the original full-registry
    behavior.
    """
    target_dcc = (
        None
        if dcc is None
        else _normalize_dcc(dcc)
    )

    return tuple(
        copy.deepcopy(preset)
        for preset in _BUILTIN_PRESETS
        if (
            target_dcc is None or
            _normalize_dcc(preset.get("dcc", "")) in (
                _DCC_ALL,
                target_dcc,
            )
        )
    )


def get_preset(preset_id):
    preset_id = text_type(preset_id or "")
    for preset in _BUILTIN_PRESETS:
        if text_type(preset.get("id", "")) == preset_id:
            return copy.deepcopy(preset)
    return None


def build_preset_root(preset_id):
    """Return a normalized item subtree for a built-in preset."""
    preset = get_preset(preset_id)
    if preset is None:
        return None

    root = preset.get("root")
    if not isinstance(root, dict):
        return None

    kind = text_type(root.get("kind", "")).lower()
    if not kind:
        return None

    return create_item(
        kind,
        copy.deepcopy(root)
    )


__all__ = [
    "build_preset_root",
    "get_preset",
    "iter_presets",
]
