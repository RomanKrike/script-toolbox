# -*- coding: utf-8 -*-
from __future__ import print_function

from ..pycompat import text_type
from . import bindings as _bindings
from . import items as _items


_INSTALL_MARKER = "_script_toolbox_toggle_button_installed"

_ORIGINAL_NORMALIZE_BINDING = _bindings.normalize_binding
_ORIGINAL_NORMALIZE_BINDINGS = _bindings.normalize_bindings
_ORIGINAL_MODE_MATCHES = _bindings._mode_matches


def _normalize_binding(kind, value):
    kind = text_type(kind or "").lower()
    if kind == "toggle_button":
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

    if kind != "toggle_button":
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
    if text_type(item.get("kind") or "").lower() != "toggle_button":
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


def _action_button(data):
    normalized = dict(data or {})
    normalized["mode"] = "action"

    item = _items.base_item(
        "button",
        normalized,
        "New Button"
    )
    item.update({
        "color": _items.safe_color(
            data.get("color")
        ),
        "icon_path": text_type(
            data.get("icon_path") or ""
        ),
        "icon_size": _items.clamp(
            _items.safe_int(
                data.get("icon_size"),
                18
            ),
            8,
            256
        ),
        "icon_only": bool(
            data.get("icon_only", False)
        ),
    })
    return item


def _toggle_button(data):
    data = data or {}
    state_source = text_type(
        data.get("state_source", "internal")
    ).lower()
    if state_source not in ("internal", "script"):
        state_source = "internal"

    normalized = dict(data)
    normalized["mode"] = "state"

    item = _items.base_item(
        "toggle_button",
        normalized,
        "New Toggle Button"
    )

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

    default_label = text_type(
        item.get("label", "Toggle")
    )

    item.update({
        "state_source": state_source,
        "icon_path": text_type(
            data.get("icon_path") or ""
        ),
        "icon_size": _items.clamp(
            _items.safe_int(
                data.get("icon_size"),
                18
            ),
            8,
            256
        ),
        "icon_only": bool(
            data.get("icon_only", False)
        ),
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
        "state_on_label": text_type(
            data.get("state_on_label") or default_label
        ),
        "state_off_label": text_type(
            data.get("state_off_label") or default_label
        ),
        "state_on_color": _items.safe_color(
            data.get("state_on_color") or [0.22, 0.42, 0.26]
        ),
        "state_off_color": _items.safe_color(
            data.get("state_off_color") or [0.30, 0.30, 0.30]
        ),
    })

    # Internal state is persisted in the document. Script-backed state has no
    # stored value because its query is the only source of truth.
    if state_source == "internal":
        item["value"] = bool(
            data.get("value", False)
        )
    else:
        item.pop("value", None)

    return item


def install_toggle_button_kind():
    if getattr(
        _items,
        _INSTALL_MARKER,
        False
    ):
        return

    _bindings.EVENT_CAPABILITIES[
        "toggle_button"
    ] = (
        "click",
        "double_click",
    )

    _bindings.normalize_binding = _normalize_binding
    _bindings.normalize_bindings = _normalize_bindings
    _bindings._mode_matches = _mode_matches

    # items.py imported normalize_bindings directly, so replace that module
    # reference as well before any documents are normalized.
    _items.normalize_bindings = _normalize_bindings
    _items._FACTORIES["button"] = _action_button
    _items._FACTORIES["toggle_button"] = _toggle_button

    setattr(
        _items,
        _INSTALL_MARKER,
        True
    )


__all__ = [
    "install_toggle_button_kind",
]
