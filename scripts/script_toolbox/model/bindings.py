# -*- coding: utf-8 -*-
from __future__ import print_function

import uuid

from ..constants import SUPPORTED_LANGUAGES
from ..pycompat import text_type
from .item_builtins import register_builtin_items
from .item_registry import ITEM_TYPES


MOUSE_EVENTS = (
    "click",
    "double_click",
)

MOUSE_BUTTONS = (
    "left",
    "middle",
    "right",
)

MODIFIERS = (
    "ctrl",
    "alt",
    "shift",
)

EVENT_LABELS = {
    "click": "Click",
    "double_click": "Double Click",
    "value_changed": "Value Changed",
    "editing_finished": "Editing Finished",
    "selection_changed": "Selection Changed",
    "opened": "Opened",
    "closed": "Closed",
}


def new_binding_id():
    return uuid.uuid4().hex


def binding_events(kind, include_internal=False):
    register_builtin_items()
    definition = ITEM_TYPES.get(kind)
    if definition is None:
        return ()
    result = list(definition.events)
    if include_internal:
        for event in definition.internal_events:
            if event not in result:
                result.append(event)
    return tuple(result)


def supports_bindings(kind):
    return bool(binding_events(kind))


def is_mouse_event(event):
    return text_type(event or "").lower() in MOUSE_EVENTS


def _normalize_language(value):
    value = text_type(value or "python").lower()
    if value not in SUPPORTED_LANGUAGES:
        value = "python"
    return value


def _normalize_mouse_button(value):
    value = text_type(value or "left").lower()
    if value not in MOUSE_BUTTONS:
        value = "left"
    return value


def normalize_modifiers(value):
    if isinstance(value, (list, tuple, set)):
        raw = value
    elif value:
        raw = [value]
    else:
        raw = []

    selected = set(
        text_type(entry or "").lower()
        for entry in raw
    )
    return [
        modifier
        for modifier in MODIFIERS
        if modifier in selected
    ]


def make_binding(
    event,
    language="python",
    script="",
    mouse_button="left",
    modifiers=None,
    label="",
    binding_id=None,
    handler="script",
    modifier_policy="exact"
):
    event = text_type(event or "").lower()
    handler = text_type(handler or "script").lower()
    modifier_policy = text_type(
        modifier_policy or "exact"
    ).lower()

    if handler not in ("script", "state_toggle"):
        handler = "script"
    if modifier_policy not in ("exact", "any"):
        modifier_policy = "exact"

    result = {
        "id": text_type(binding_id or new_binding_id()),
        "event": event,
        "handler": handler,
        "language": _normalize_language(language),
        "script": text_type(script or ""),
        "label": text_type(label or ""),
    }

    if is_mouse_event(event):
        result["mouse_button"] = _normalize_mouse_button(mouse_button)
        result["modifiers"] = normalize_modifiers(modifiers)
        result["modifier_policy"] = modifier_policy

    return result


def normalize_binding(kind, value):
    if not isinstance(value, dict):
        return None

    register_builtin_items()
    definition = ITEM_TYPES.get(kind)
    if definition is None:
        return None

    event = text_type(value.get("event") or "").lower()
    allowed = binding_events(definition.kind, include_internal=True)
    if event not in allowed:
        return None

    handler = text_type(value.get("handler", "script")).lower()
    if (
        handler == "state_toggle" and
        not definition.has_capability("state_toggle")
    ):
        handler = "script"

    return make_binding(
        event,
        language=value.get("language", "python"),
        script=value.get("script", ""),
        mouse_button=value.get("mouse_button", "left"),
        modifiers=value.get("modifiers", []),
        label=value.get("label", ""),
        binding_id=value.get("id"),
        handler=handler,
        modifier_policy=value.get("modifier_policy", "exact")
    )


def normalize_bindings(kind, data=None):
    register_builtin_items()
    definition = ITEM_TYPES.get(kind)
    if definition is None:
        return []

    data = data or {}
    raw = data.get("bindings")
    result = []

    if isinstance(raw, list):
        for entry in raw:
            normalized = normalize_binding(definition.kind, entry)
            if normalized is not None:
                result.append(normalized)

    for default_spec in definition.default_bindings():
        default_binding = normalize_binding(definition.kind, default_spec)
        if default_binding is None:
            continue
        if any(
            entry.get("event") == default_binding.get("event") and
            entry.get("handler") == default_binding.get("handler")
            for entry in result
        ):
            continue
        result.insert(0, default_binding)

    return result


def binding_signature(binding):
    event = text_type(binding.get("event") or "")
    if is_mouse_event(event):
        return (
            event,
            text_type(binding.get("mouse_button", "left")),
            tuple(normalize_modifiers(binding.get("modifiers", []))),
            text_type(binding.get("modifier_policy", "exact")),
        )
    return (event,)


def binding_display_name(binding):
    custom = text_type(binding.get("label") or "").strip()
    if custom:
        return custom

    event = text_type(binding.get("event") or "")
    if not is_mouse_event(event):
        return EVENT_LABELS.get(event, event.replace("_", " ").title())

    parts = []
    labels = {
        "ctrl": "Ctrl",
        "alt": "Alt",
        "shift": "Shift",
    }
    for modifier in normalize_modifiers(binding.get("modifiers", [])):
        parts.append(labels[modifier])

    mouse_button = text_type(
        binding.get("mouse_button", "left")
    ).lower()
    if mouse_button == "middle":
        parts.append("Middle")
    elif mouse_button == "right":
        parts.append("Right")

    parts.append(EVENT_LABELS.get(event, event.title()))
    return " + ".join(parts)


def binding_matches(
    binding,
    item,
    event,
    mouse_button="left",
    modifiers=None
):
    if text_type(binding.get("event") or "") != text_type(event or ""):
        return False

    if not is_mouse_event(event):
        return True

    if text_type(binding.get("mouse_button", "left")) != text_type(
        mouse_button or "left"
    ):
        return False

    if binding.get("modifier_policy", "exact") == "any":
        return True

    return normalize_modifiers(
        binding.get("modifiers", [])
    ) == normalize_modifiers(modifiers)


def matching_bindings(
    item,
    event,
    mouse_button="left",
    modifiers=None
):
    return [
        binding
        for binding in item.get("bindings", []) or []
        if binding_matches(
            binding,
            item,
            event,
            mouse_button=mouse_button,
            modifiers=modifiers
        )
    ]


def has_mouse_binding(item):
    return any(
        is_mouse_event(binding.get("event"))
        for binding in item.get("bindings", []) or []
    )


def bindings_for_editor(item):
    kind = text_type(item.get("kind") or "").lower()
    exposed = set(binding_events(kind))
    return [
        binding
        for binding in item.get("bindings", []) or []
        if binding.get("event") in exposed
    ]


__all__ = [
    "EVENT_LABELS",
    "MODIFIERS",
    "MOUSE_BUTTONS",
    "MOUSE_EVENTS",
    "binding_display_name",
    "binding_events",
    "binding_matches",
    "binding_signature",
    "bindings_for_editor",
    "has_mouse_binding",
    "is_mouse_event",
    "make_binding",
    "matching_bindings",
    "new_binding_id",
    "normalize_binding",
    "normalize_bindings",
    "normalize_modifiers",
    "supports_bindings",
]
