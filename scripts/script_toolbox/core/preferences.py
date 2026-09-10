# -*- coding: utf-8 -*-
from __future__ import print_function

import io
import json
import os

from ..constants import BUILD_CHANNEL
from ..pycompat import text_type
from .user_paths import settings_path


UPDATE_CHANNEL_STABLE = "stable"
UPDATE_CHANNEL_DEVELOPMENT = "development"
UPDATE_CHANNELS = (
    UPDATE_CHANNEL_STABLE,
    UPDATE_CHANNEL_DEVELOPMENT,
)
INSPECTOR_SECTIONS_KEY = "inspector_sections"
TELEMETRY_CONSENT_KEY = "telemetry_consent"


def normalize_update_channel(
    value,
    default=UPDATE_CHANNEL_STABLE
):
    value = text_type(
        value or ""
    ).strip().lower()

    if value in UPDATE_CHANNELS:
        return value

    default = text_type(
        default or UPDATE_CHANNEL_STABLE
    ).strip().lower()

    if default not in UPDATE_CHANNELS:
        default = UPDATE_CHANNEL_STABLE

    return default


def normalize_telemetry_consent(value):
    """Return True, False, or None when the user has not decided yet."""
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if value == 1:
        return True
    if value == 0:
        return False

    normalized = text_type(value).strip().lower()
    if normalized in ("true", "yes", "1", "enabled"):
        return True
    if normalized in ("false", "no", "0", "disabled"):
        return False
    return None


def default_preferences():
    return {
        "update_channel": normalize_update_channel(
            BUILD_CHANNEL
        ),
        TELEMETRY_CONSENT_KEY: None,
    }


def load_preferences(
    path=None
):
    path = os.path.normpath(
        path or settings_path()
    )
    result = default_preferences()

    if not os.path.isfile(path):
        return result

    try:
        with io.open(
            path,
            "r",
            encoding="utf-8"
        ) as handle:
            data = json.load(handle)
    except Exception:
        return result

    if not isinstance(data, dict):
        return result

    result.update(data)
    result["update_channel"] = normalize_update_channel(
        result.get("update_channel"),
        default=BUILD_CHANNEL
    )
    result[TELEMETRY_CONSENT_KEY] = normalize_telemetry_consent(
        result.get(TELEMETRY_CONSENT_KEY)
    )
    return result


def save_preferences(
    preferences,
    path=None
):
    path = os.path.normpath(
        path or settings_path()
    )
    folder = os.path.dirname(path)

    if folder and not os.path.isdir(folder):
        os.makedirs(folder)

    payload = dict(preferences or {})
    payload["update_channel"] = normalize_update_channel(
        payload.get("update_channel"),
        default=BUILD_CHANNEL
    )
    payload[TELEMETRY_CONSENT_KEY] = normalize_telemetry_consent(
        payload.get(TELEMETRY_CONSENT_KEY)
    )

    serialized = json.dumps(
        payload,
        indent=2,
        sort_keys=True
    )

    if not isinstance(serialized, text_type):
        serialized = serialized.decode("utf-8")

    with io.open(
        path,
        "w",
        encoding="utf-8"
    ) as handle:
        handle.write(serialized)
        handle.write(u"\n")

    return path


def get_update_channel(
    path=None
):
    return load_preferences(
        path=path
    )["update_channel"]


def set_update_channel(
    channel,
    path=None
):
    channel = normalize_update_channel(
        channel,
        default=BUILD_CHANNEL
    )
    preferences = load_preferences(
        path=path
    )
    preferences["update_channel"] = channel
    save_preferences(
        preferences,
        path=path
    )
    return channel


def get_telemetry_consent(path=None):
    """Return explicit telemetry consent state: True, False, or None."""
    return load_preferences(
        path=path
    ).get(TELEMETRY_CONSENT_KEY)


def set_telemetry_consent(consent, path=None):
    """Persist explicit opt-in/opt-out state without enabling telemetry itself."""
    consent = normalize_telemetry_consent(consent)
    preferences = load_preferences(
        path=path
    )
    preferences[TELEMETRY_CONSENT_KEY] = consent
    save_preferences(
        preferences,
        path=path
    )
    return consent


def _inspector_section_states(preferences):
    states = preferences.get(
        INSPECTOR_SECTIONS_KEY,
        {}
    )
    if not isinstance(states, dict):
        return {}
    return states


def get_inspector_section_collapsed(
    key,
    default=False,
    path=None
):
    """Return editor-only collapsed state for one stable Inspector section."""
    preferences = load_preferences(
        path=path
    )
    states = _inspector_section_states(preferences)
    key = text_type(key or "").strip()
    if not key:
        return bool(default)
    return bool(
        states.get(key, default)
    )


def set_inspector_section_collapsed(
    key,
    collapsed,
    path=None
):
    """Persist Inspector presentation state outside the config document."""
    key = text_type(key or "").strip()
    if not key:
        return bool(collapsed)

    preferences = load_preferences(
        path=path
    )
    states = dict(
        _inspector_section_states(preferences)
    )
    states[key] = bool(collapsed)
    preferences[INSPECTOR_SECTIONS_KEY] = states
    save_preferences(
        preferences,
        path=path
    )
    return bool(collapsed)


__all__ = [
    "INSPECTOR_SECTIONS_KEY",
    "TELEMETRY_CONSENT_KEY",
    "UPDATE_CHANNEL_DEVELOPMENT",
    "UPDATE_CHANNEL_STABLE",
    "UPDATE_CHANNELS",
    "default_preferences",
    "get_inspector_section_collapsed",
    "get_telemetry_consent",
    "get_update_channel",
    "load_preferences",
    "normalize_telemetry_consent",
    "normalize_update_channel",
    "save_preferences",
    "set_inspector_section_collapsed",
    "set_telemetry_consent",
    "set_update_channel",
    "settings_path",
]
