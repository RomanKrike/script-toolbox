# -*- coding: utf-8 -*-
from __future__ import print_function

from ..pycompat import text_type


CALLBACK_EVENTS = {
    "button": ("on_click",),
    "icon": ("on_click",),
    "string": ("on_change",),
    "integer": ("on_change",),
    "float": ("on_change",),
    "checkbox": ("on_change",),
    "menu": ("on_change",),
    "color": ("on_change",),
    "field": ("on_change", "on_select", "on_double_click"),
    "label": ("on_click",),
    "folder": ("on_open", "on_close"),
    "row": (),
    "separator": (),
}

CALLBACK_LABELS = {
    "on_click": "Click",
    "on_change": "Change",
    "on_select": "Select",
    "on_double_click": "Double Click",
    "on_open": "Open",
    "on_close": "Close",
}


def callback_events(kind):
    return CALLBACK_EVENTS.get(
        text_type(kind or "").lower(),
        ()
    )


def normalize_callbacks(kind, data=None):
    data = data or {}
    raw = data.get("callbacks")
    raw = raw if isinstance(raw, dict) else {}
    result = {}

    for event in callback_events(kind):
        source = text_type(raw.get(event) or "")

        # Schema 16 compatibility. The v16->v17 migration performs the same
        # conversion, but create_item() also accepts legacy payloads directly.
        if (
            event == "on_change" and
            not source.strip()
        ):
            source = text_type(
                data.get("on_change_script") or ""
            )

        if source.strip():
            result[event] = source

    return result


def callback_script(item, event):
    if not isinstance(item, dict):
        return ""

    event = text_type(event or "")
    if event not in callback_events(
        item.get("kind")
    ):
        return ""

    callbacks = item.get("callbacks")
    if isinstance(callbacks, dict):
        source = text_type(
            callbacks.get(event) or ""
        )
        if source.strip():
            return source

    if event == "on_change":
        return text_type(
            item.get("on_change_script") or ""
        )

    return ""


def has_callback(item, event):
    return bool(
        callback_script(item, event).strip()
    )


__all__ = [
    "CALLBACK_EVENTS",
    "CALLBACK_LABELS",
    "callback_events",
    "callback_script",
    "has_callback",
    "normalize_callbacks",
]
