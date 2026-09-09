# -*- coding: utf-8 -*-
from __future__ import print_function

from ..pycompat import text_type
from . import bindings as _bindings
from . import items as _items


_INSTALL_MARKER = "_script_toolbox_toggle_icon_installed"

# toggle_button installs first, so these references deliberately preserve its
# compatibility wrappers while extending the same state-toggle contract to
# Toggle Icon.
_ORIGINAL_NORMALIZE_BINDING = _bindings.normalize_binding
_ORIGINAL_NORMALIZE_BINDINGS = _bindings.normalize_bindings
_ORIGINAL_MODE_MATCHES = _bindings._mode_matches


def _normalize_binding(kind, value):
    kind = text_type(kind or "").lower()
    if kind == "toggle_icon":
        return _ORIGINAL_NORMALIZE_BINDING(
            "button",
            value
        )
    return _ORIGINAL_NORMALIZE_BINDING(
        kind,
        value
    )


def _normalize_bindings(kind, data=None):
    kind = text_type(kind or "").lower()
    data = data or {}

    if kind != "toggle_icon":
        return _ORIGINAL_NORMALIZE_BINDINGS(
            kind,
            data
        )

    shadow = dict(data)
    shadow["mode"] = "state"
    return _ORIGINAL_NORMALIZE_BINDINGS(
        "button",
        shadow
    )


def _mode_matches(binding, item):
    if text_type(item.get("kind") or "").lower() != "toggle_icon":
        return _ORIGINAL_MODE_MATCHES(
            binding,
            item
        )

    shadow = dict(item)
    shadow["kind"] = "button"
    shadow["mode"] = "state"
    return _ORIGINAL_MODE_MATCHES(
        binding,
        shadow
    )


def _toggle_icon(data):
    data = data or {}
    state_source = text_type(
        data.get("state_source", "internal")
    ).lower()
    if state_source not in ("internal", "script"):
        state_source = "internal"

    normalized = dict(data)
    normalized["mode"] = "state"

    item = _items.base_item(
        "toggle_icon",
        normalized,
        "Toggle Icon"
    )

    alignment = text_type(
        data.get(
            "content_alignment",
            data.get("alignment", "left")
        )
    ).lower()
    if alignment not in ("left", "center", "right"):
        alignment = "left"

    legacy_language = text_type(
        data.get("language", "python")
    ).lower()
    if legacy_language not in ("python", "mel"):
        legacy_language = "python"

    state_on_language = text_type(
        data.get("state_on_language", legacy_language)
    ).lower()
    state_off_language = text_type(
        data.get("state_off_language", legacy_language)
    ).lower()
    if state_on_language not in ("python", "mel"):
        state_on_language = "python"
    if state_off_language not in ("python", "mel"):
        state_off_language = "python"

    fallback_path = text_type(
        data.get("path") or ""
    )

    item.update({
        "show_label": bool(data.get("show_label", False)),
        "state_source": state_source,
        "state_on_path": text_type(
            data.get("state_on_path") or fallback_path
        ),
        "state_off_path": text_type(
            data.get("state_off_path") or fallback_path
        ),
        "width": _items.clamp(
            _items.safe_int(data.get("width"), 24),
            8,
            512
        ),
        "height": _items.clamp(
            _items.safe_int(data.get("height"), 24),
            8,
            512
        ),
        "alignment": alignment,
        "content_alignment": alignment,
        "state_get_script": text_type(
            data.get("state_get_script") or ""
        ),
        "state_get_language": "python",
        "state_on_script": text_type(
            data.get("state_on_script") or ""
        ),
        "state_on_language": state_on_language,
        "state_off_script": text_type(
            data.get("state_off_script") or ""
        ),
        "state_off_language": state_off_language,
    })

    if state_source == "internal":
        item["value"] = bool(
            data.get("value", False)
        )
    else:
        item.pop("value", None)

    # Toggle Icon has explicit state-specific images; keep legacy Icon-only
    # fields out of the normalized payload.
    item.pop("path", None)
    item.pop("clickable", None)
    item.pop("mode", None)
    return item


def install_toggle_icon_kind():
    if getattr(
        _items,
        _INSTALL_MARKER,
        False
    ):
        return

    _bindings.EVENT_CAPABILITIES[
        "toggle_icon"
    ] = (
        "click",
        "double_click",
    )

    _bindings.normalize_binding = _normalize_binding
    _bindings.normalize_bindings = _normalize_bindings
    _bindings._mode_matches = _mode_matches

    # items.py imported normalize_bindings directly; keep its reference on the
    # final wrapper as well.
    _items.normalize_bindings = _normalize_bindings
    _items._FACTORIES["toggle_icon"] = _toggle_icon

    setattr(
        _items,
        _INSTALL_MARKER,
        True
    )


__all__ = [
    "install_toggle_icon_kind",
]
