# -*- coding: utf-8 -*-
from __future__ import print_function

import copy
import io
import json
import os

from ..model import create_item
from ..pycompat import text_type


_DCC_ALL = "all"
_SUPPORTED_DCCS = (
    "maya",
    "houdini",
    "nuke",
    "blender",
    "standalone",
)


def default_library_path():
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "presets")


def _load_default_presets():
    result = []
    root = default_library_path()
    for filename in sorted(os.listdir(root)):
        if filename.lower().endswith(".json"):
            with io.open(os.path.join(root, filename), encoding="utf-8") as handle:
                result.append(json.load(handle))
    return tuple(result)


_BUILTIN_PRESETS = _load_default_presets()



def _normalize_dcc(dcc):
    value = text_type(
        dcc or ""
    ).strip().lower()

    if value == _DCC_ALL or value in _SUPPORTED_DCCS:
        return value
    return ""


def _preset_matches_dcc(preset, target_dcc):
    preset_dcc = _normalize_dcc(
        preset.get("dcc", "")
    )

    if preset_dcc == _DCC_ALL:
        return True

    return bool(
        target_dcc and
        preset_dcc == target_dcc
    )


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
            _preset_matches_dcc(
                preset,
                target_dcc
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
