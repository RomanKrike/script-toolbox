# -*- coding: utf-8 -*-
from __future__ import print_function

from ..pycompat import text_type
from . import service


ITEM_TYPES = (
    "button",
    "checkbox",
    "color",
    "column",
    "field",
    "float",
    "folder",
    "icon",
    "integer",
    "label",
    "menu",
    "row",
    "separator",
    "string",
    "text",
    "toggle_button",
    "toggle_icon",
    "other",
)

IMPORT_MODES = (
    "append",
    "insert",
    "replace",
)

SHARE_TYPES = (
    "config",
    "item",
)


# Every event/property/value admitted here is privacy-reviewed. Product code
# should use track_product_event() instead of sending arbitrary dictionaries to
# the provider facade.
_EVENT_ENUM_PROPERTIES = {
    "plugin_started": {},
    "editor_opened": {},
    "settings_opened": {},
    "item_created": {
        "item_type": ITEM_TYPES,
    },
    "item_duplicated": {
        "item_type": ITEM_TYPES,
    },
    "item_activated": {
        "item_type": ITEM_TYPES,
    },
    "config_imported": {
        "mode": IMPORT_MODES,
    },
    "config_exported": {},
    "share_created": {
        "share_type": SHARE_TYPES,
    },
    "share_pasted": {
        "share_type": SHARE_TYPES,
    },
}


def _normalized_enum(value, allowed):
    value = text_type(
        value or ""
    ).strip().lower()

    if value in allowed:
        return value

    if "other" in allowed:
        return "other"

    return None


def sanitize_product_event(
    event_name,
    properties=None
):
    """Return a reviewed event payload or ``None`` when it is not allowed.

    Unknown event names, unknown property keys and unapproved enum values are
    rejected. This is deliberately fail-closed so future UI code cannot leak a
    path, label, object name, script or other arbitrary user-controlled string
    by accidentally passing it to telemetry.
    """
    event_name = text_type(
        event_name or ""
    ).strip().lower()
    spec = _EVENT_ENUM_PROPERTIES.get(
        event_name
    )

    if spec is None:
        return None

    if properties is None:
        properties = {}

    if not isinstance(properties, dict):
        return None

    if set(properties.keys()) != set(spec.keys()):
        return None

    sanitized = {}
    for key, allowed in spec.items():
        value = _normalized_enum(
            properties.get(key),
            allowed
        )
        if value is None:
            return None
        sanitized[key] = value

    return event_name, sanitized


def track_product_event(
    event_name,
    properties=None
):
    """Capture one privacy-reviewed semantic product event."""
    payload = sanitize_product_event(
        event_name,
        properties
    )
    if payload is None:
        return False

    safe_name, safe_properties = payload
    return service.track(
        safe_name,
        safe_properties
    )


__all__ = [
    "IMPORT_MODES",
    "ITEM_TYPES",
    "SHARE_TYPES",
    "sanitize_product_event",
    "track_product_event",
]
