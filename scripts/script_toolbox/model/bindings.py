# -*- coding: utf-8 -*-
from __future__ import print_function

import uuid

from ..constants import SUPPORTED_LANGUAGES
from ..pycompat import text_type


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

# Events exposed by the Interface Editor. Layout kinds intentionally expose no
# triggers in schema 18, while the model can still preserve compatible hidden
# bindings for future layout-event support.
EVENT_CAPABILITIES = {
    "button": ("click", "double_click"),
    "icon": ("click", "double_click"),
    "string": (
        "value_changed",
        "editing_finished",
        "click",
        "double_click",
    ),
    "integer": (
        "value_changed",
        "editing_finished",
        "click",
        "double_click",
    ),
    "float": (
        "value_changed",
        "editing_finished",
        "click",
        "double_click",
    ),
    "checkbox": ("value_changed", "click", "double_click"),
    "menu": ("value_changed", "click", "double_click"),
    "color": ("value_changed", "click", "double_click"),
    "field": (
        "value_changed",
        "selection_changed",
        "click",
        "double_click",
    ),
    "label": ("click", "double_click"),
    "folder": (),
    "row": (),
    "separator": (),
}

INTERNAL_EVENT_CAPABILITIES = {
    "folder": ("opened", "closed"),
}

LEGACY_CALLBACK_EVENT_MAP = {
    "on_change": "value_changed",
    "on_select": "selection_changed",
    "on_double_click": "double_click",
    "on_click": "click",
    "on_open": "opened",
    "on_close": "closed",
}


def new_binding_id():
    return uuid.uuid4().hex


def binding_events(kind, include_internal=False):
    kind = text_type(kind or "").lower()
    result = list(EVENT_CAPABILITIES.get(kind, ()))

    if include_internal:
        for event in INTERNAL_EVENT_CAPABILITIES.get(kind, ()):
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
    button_mode="all",
    modifier_policy="exact"
):
    event = text_type(event or "").lower()
    handler = text_type(handler or "script").lower()
    button_mode = text_type(button_mode or "all").lower()
    modifier_policy = text_type(
        modifier_policy or "exact"
    ).lower()

    if handler not in ("script", "state_toggle"):
        handler = "script"
    if button_mode not in ("all", "action", "state"):
        button_mode = "all"
    if modifier_policy not in ("exact", "any"):
        modifier_policy = "exact"

    result = {
        "id": text_type(binding_id or new_binding_id()),
        "event": event,
        "handler": handler,
        "button_mode": button_mode,
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

    event = text_type(value.get("event") or "").lower()
    allowed = binding_events(kind, include_internal=True)
    if event not in allowed:
        return None

    handler = value.get("handler", "script")
    if handler == "state_toggle" and text_type(kind) != "button":
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
        button_mode=value.get("button_mode", "all"),
        modifier_policy=value.get("modifier_policy", "exact")
    )


def _append_legacy_callback(result, kind, event, source):
    source = text_type(source or "")
    mapped = LEGACY_CALLBACK_EVENT_MAP.get(event)
    if not source.strip() or mapped not in binding_events(
        kind,
        include_internal=True
    ):
        return

    result.append(
        make_binding(
            mapped,
            language="python",
            script=source,
            mouse_button="left",
            modifiers=[],
            label=(
                "Click Callback"
                if mapped == "click" and kind == "button"
                else ""
            ),
            button_mode="all",
            # Schema 17 callbacks did not distinguish modifier state.
            modifier_policy=(
                "any"
                if is_mouse_event(mapped)
                else "exact"
            )
        )
    )


def _legacy_bindings(kind, data):
    result = []
    kind = text_type(kind or "").lower()
    mode = text_type(data.get("mode", "action")).lower()
    old_language = _normalize_language(
        data.get("language", "python")
    )

    if kind == "button":
        click_script = text_type(data.get("click_script") or "")
        shift_script = text_type(data.get("shift_script") or "")

        if click_script.strip():
            result.append(
                make_binding(
                    "click",
                    language=old_language,
                    script=click_script,
                    mouse_button="left",
                    modifiers=[],
                    button_mode="action"
                )
            )

        if shift_script.strip():
            result.append(
                make_binding(
                    "click",
                    language=old_language,
                    script=shift_script,
                    mouse_button="left",
                    modifiers=["shift"],
                    button_mode="action"
                )
            )

        if mode == "state":
            result.insert(
                0,
                make_binding(
                    "click",
                    mouse_button="left",
                    modifiers=[],
                    handler="state_toggle",
                    button_mode="state"
                )
            )

    callbacks = data.get("callbacks")
    if isinstance(callbacks, dict):
        for event, source in callbacks.items():
            _append_legacy_callback(
                result,
                kind,
                text_type(event or ""),
                source
            )

    # Pre-schema-17 direct payload compatibility.
    on_change = text_type(data.get("on_change_script") or "")
    if on_change.strip() and not any(
        entry.get("event") == "value_changed"
        for entry in result
    ):
        _append_legacy_callback(
            result,
            kind,
            "on_change",
            on_change
        )

    if kind == "icon" and data.get("clickable", False) and not any(
        is_mouse_event(entry.get("event"))
        for entry in result
    ):
        result.append(
            make_binding(
                "click",
                mouse_button="left",
                modifiers=[],
                modifier_policy="any"
            )
        )

    if kind == "button":
        if mode == "state":
            if not any(
                entry.get("handler") == "state_toggle"
                for entry in result
            ):
                result.insert(
                    0,
                    make_binding(
                        "click",
                        handler="state_toggle",
                        button_mode="state"
                    )
                )
        elif not any(
            entry.get("handler") == "script" and
            entry.get("button_mode") in ("all", "action")
            for entry in result
        ):
            result.insert(
                0,
                make_binding(
                    "click",
                    button_mode="action"
                )
            )

    return result


def normalize_bindings(kind, data=None):
    data = data or {}
    raw = data.get("bindings")

    if isinstance(raw, list):
        result = []
        for entry in raw:
            normalized = normalize_binding(kind, entry)
            if normalized is not None:
                result.append(normalized)
    else:
        result = _legacy_bindings(kind, data)

    kind = text_type(kind or "").lower()
    mode = text_type(data.get("mode", "action")).lower()

    if kind == "button":
        if mode == "state" and not any(
            entry.get("handler") == "state_toggle" and
            entry.get("button_mode") in ("all", "state")
            for entry in result
        ):
            result.insert(
                0,
                make_binding(
                    "click",
                    handler="state_toggle",
                    button_mode="state"
                )
            )
        elif mode != "state" and not any(
            entry.get("handler") == "script" and
            entry.get("button_mode") in ("all", "action")
            for entry in result
        ):
            result.insert(
                0,
                make_binding(
                    "click",
                    button_mode="action"
                )
            )

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


def _mode_matches(binding, item):
    if text_type(item.get("kind")) != "button":
        return True

    binding_mode = text_type(
        binding.get("button_mode", "all")
    )
    item_mode = text_type(
        item.get("mode", "action")
    )
    return binding_mode == "all" or binding_mode == item_mode


def binding_matches(
    binding,
    item,
    event,
    mouse_button="left",
    modifiers=None
):
    if text_type(binding.get("event") or "") != text_type(event or ""):
        return False
    if not _mode_matches(binding, item):
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
        is_mouse_event(binding.get("event")) and
        _mode_matches(binding, item)
        for binding in item.get("bindings", []) or []
    )


def bindings_for_editor(item):
    kind = text_type(item.get("kind") or "").lower()
    exposed = set(binding_events(kind))
    result = []

    for binding in item.get("bindings", []) or []:
        if binding.get("event") not in exposed:
            continue
        if not _mode_matches(binding, item):
            continue
        result.append(binding)

    return result


__all__ = [
    "EVENT_CAPABILITIES",
    "EVENT_LABELS",
    "INTERNAL_EVENT_CAPABILITIES",
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
