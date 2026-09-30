# -*- coding: utf-8 -*-
from __future__ import print_function

import io
import copy
import shutil
import tempfile
import warnings
import json
import os

from ..constants import BUILD_CHANNEL
from ..pycompat import text_type
from .user_paths import settings_path
from .file_lock import FileLock
from .config import _replace_file
from .logging_utils import get_logger


UPDATE_CHANNEL_STABLE = "stable"
UPDATE_CHANNEL_DEVELOPMENT = "development"
UPDATE_CHANNELS = (
    UPDATE_CHANNEL_STABLE,
    UPDATE_CHANNEL_DEVELOPMENT,
)
INSPECTOR_SECTIONS_KEY = "inspector_sections"
TELEMETRY_CONSENT_KEY = "telemetry_consent"
TELEMETRY_INSTALLATION_ID_KEY = "telemetry_installation_id"
_TELEMETRY_INSTALLATION_ID_PREFIX = "stb-install-"


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


def normalize_telemetry_installation_id(value):
    """Return a valid random Script Toolbox installation id or ``None``."""
    value = text_type(
        value or ""
    ).strip().lower()

    if not value.startswith(_TELEMETRY_INSTALLATION_ID_PREFIX):
        return None

    token = value[len(_TELEMETRY_INSTALLATION_ID_PREFIX):]
    if len(token) != 32:
        return None

    for character in token:
        if character not in "0123456789abcdef":
            return None

    return _TELEMETRY_INSTALLATION_ID_PREFIX + token


def default_preferences():
    return {
        "update_channel": normalize_update_channel(
            BUILD_CHANNEL
        ),
        TELEMETRY_CONSENT_KEY: None,
        TELEMETRY_INSTALLATION_ID_KEY: None,
    }


def _load_preferences_unlocked(
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
    except Exception as exc:
        get_logger().warning("Preferences unreadable at %r: %s", path, exc)
        backup = path + ".bak"
        if os.path.isfile(backup):
            with io.open(backup, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            if not isinstance(data, dict):
                raise ValueError("Invalid preferences backup: " + backup)
            descriptor, corrupt_path = tempfile.mkstemp(
                prefix=os.path.basename(path) + ".corrupt-",
                dir=os.path.dirname(os.path.abspath(path)))
            os.close(descriptor)
            shutil.copy2(path, corrupt_path)
            _atomic_preferences_write(data, path)
            warnings.warn("Preferences recovered; damaged file: " + corrupt_path,
                          RuntimeWarning)
        else:
            raise RuntimeError("Preferences cannot be read; original preserved at " + path)

    if not isinstance(data, dict):
        raise ValueError("Preferences must contain an object: " + path)

    result.update(data)
    result["update_channel"] = normalize_update_channel(
        result.get("update_channel"),
        default=BUILD_CHANNEL
    )
    result[TELEMETRY_CONSENT_KEY] = normalize_telemetry_consent(
        result.get(TELEMETRY_CONSENT_KEY)
    )
    result[TELEMETRY_INSTALLATION_ID_KEY] = (
        normalize_telemetry_installation_id(
            result.get(TELEMETRY_INSTALLATION_ID_KEY)
        )
    )
    return result


class PreferencesSnapshot(dict):
    pass


def load_preferences(path=None):
    path = os.path.normpath(path or settings_path())
    if not os.path.exists(path):
        result = PreferencesSnapshot(default_preferences())
    else:
        with FileLock(path + ".lock", blocking=True):
            result = PreferencesSnapshot(_load_preferences_unlocked(path))
    result.original = copy.deepcopy(dict(result))
    result.source_path = os.path.normcase(os.path.realpath(path))
    return result


def _atomic_preferences_write(payload, path):
    serialized = json.dumps(payload, indent=2, sort_keys=True)
    if not isinstance(serialized, text_type):
        serialized = serialized.decode("utf-8")
    descriptor, temp_path = tempfile.mkstemp(
        prefix=".script_toolbox_preferences_", suffix=".tmp",
        dir=os.path.dirname(os.path.abspath(path)))
    try:
        with io.open(descriptor, "w", encoding="utf-8") as handle:
            handle.write(serialized + u"\n")
            handle.flush()
            os.fsync(handle.fileno())
        _replace_file(temp_path, path)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def _merge_changes(original, changed, current):
    result = dict(current)
    for key in set(original) | set(changed):
        if key not in changed:
            result.pop(key, None)
        elif key not in original or changed[key] != original[key]:
            if all(isinstance(value, dict) for value in
                   (original.get(key), changed[key], current.get(key))):
                result[key] = _merge_changes(original[key], changed[key], current[key])
            else:
                result[key] = copy.deepcopy(changed[key])
    return result


def save_preferences(preferences, path=None):
    path = os.path.normpath(path or settings_path())
    with FileLock(path + ".lock", blocking=True):
        current = _load_preferences_unlocked(path)
        if (isinstance(preferences, PreferencesSnapshot) and
                preferences.source_path == os.path.normcase(os.path.realpath(path))):
            payload = _merge_changes(preferences.original, preferences, current)
        else:
            payload = dict(current)
            payload.update(preferences or {})
        if os.path.isfile(path):
            _atomic_preferences_write(current, path + ".bak")
        result = _save_preferences_unlocked(payload, path)
        if isinstance(preferences, PreferencesSnapshot):
            preferences.clear()
            preferences.update(payload)
            preferences.original = copy.deepcopy(payload)
        return result


def _save_preferences_unlocked(
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
    payload[TELEMETRY_INSTALLATION_ID_KEY] = (
        normalize_telemetry_installation_id(
            payload.get(TELEMETRY_INSTALLATION_ID_KEY)
        )
    )

    _atomic_preferences_write(payload, path)

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


def get_telemetry_installation_id(path=None):
    """Return the persisted pseudonymous installation id, if one exists."""
    return load_preferences(
        path=path
    ).get(TELEMETRY_INSTALLATION_ID_KEY)


def set_telemetry_installation_id(installation_id, path=None):
    """Persist a validated random installation id without changing consent."""
    installation_id = normalize_telemetry_installation_id(
        installation_id
    )
    preferences = load_preferences(
        path=path
    )
    preferences[TELEMETRY_INSTALLATION_ID_KEY] = installation_id
    save_preferences(
        preferences,
        path=path
    )
    return installation_id


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
    "TELEMETRY_INSTALLATION_ID_KEY",
    "UPDATE_CHANNEL_DEVELOPMENT",
    "UPDATE_CHANNEL_STABLE",
    "UPDATE_CHANNELS",
    "default_preferences",
    "get_inspector_section_collapsed",
    "get_telemetry_consent",
    "get_telemetry_installation_id",
    "get_update_channel",
    "load_preferences",
    "normalize_telemetry_consent",
    "normalize_telemetry_installation_id",
    "normalize_update_channel",
    "save_preferences",
    "set_inspector_section_collapsed",
    "set_telemetry_consent",
    "set_telemetry_installation_id",
    "set_update_channel",
    "settings_path",
]
