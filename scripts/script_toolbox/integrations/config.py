# -*- coding: utf-8 -*-
from __future__ import print_function

import io
import json
import os
import tempfile

from ..pycompat import text_type


INTEGRATION_CONFIG_VERSION = 1
INTEGRATION_CONFIG_FILENAME = "dcc_integrations.json"


def integration_config_dir():
    if os.name == "nt":
        base = (
            os.environ.get("APPDATA") or
            os.environ.get("LOCALAPPDATA") or
            os.path.expanduser("~")
        )
        return os.path.normpath(
            os.path.join(base, "ScriptToolbox")
        )

    if os.sys.platform == "darwin":
        return os.path.normpath(
            os.path.expanduser(
                "~/Library/Application Support/ScriptToolbox"
            )
        )

    base = os.environ.get("XDG_CONFIG_HOME")
    if not base:
        base = os.path.expanduser("~/.config")
    return os.path.normpath(
        os.path.join(base, "ScriptToolbox")
    )


def integration_config_path():
    return os.path.join(
        integration_config_dir(),
        INTEGRATION_CONFIG_FILENAME
    )


def default_integration_config():
    return {
        "version": INTEGRATION_CONFIG_VERSION,
        "dcc_integrations": {},
    }


def _normalize_document(raw):
    if not isinstance(raw, dict):
        return default_integration_config()

    result = default_integration_config()
    integrations = raw.get("dcc_integrations", {})
    if isinstance(integrations, dict):
        result["dcc_integrations"] = integrations
    return result


def load_integration_config(path=None):
    path = os.path.normpath(
        path or integration_config_path()
    )
    if not os.path.isfile(path):
        return default_integration_config()

    try:
        with io.open(path, "r", encoding="utf-8") as handle:
            raw = json.load(handle)
    except Exception:
        return default_integration_config()

    return _normalize_document(raw)



def _replace_file_windows(source, destination):
    import ctypes

    move_file_ex = ctypes.windll.kernel32.MoveFileExW
    flags = 0x00000001 | 0x00000008
    result = move_file_ex(
        text_type(os.path.abspath(source)),
        text_type(os.path.abspath(destination)),
        flags
    )
    if not result:
        raise ctypes.WinError()


def _replace_file(source, destination):
    replace = getattr(os, "replace", None)
    if replace is not None:
        replace(source, destination)
        return
    if os.name == "nt":
        _replace_file_windows(source, destination)
        return
    os.rename(source, destination)


def save_integration_config(document, path=None):
    path = os.path.normpath(
        path or integration_config_path()
    )
    folder = os.path.dirname(path)
    if folder and not os.path.isdir(folder):
        os.makedirs(folder)

    payload = _normalize_document(document)
    serialized = json.dumps(
        payload,
        indent=2,
        sort_keys=True
    )
    if not isinstance(serialized, text_type):
        serialized = serialized.decode("utf-8")

    descriptor, temp_path = tempfile.mkstemp(
        prefix=".dcc_integrations_",
        suffix=".tmp",
        dir=(folder or ".")
    )
    os.close(descriptor)

    try:
        with io.open(temp_path, "w", encoding="utf-8") as handle:
            handle.write(serialized)
            handle.write(u"\n")
            handle.flush()
            os.fsync(handle.fileno())

        _replace_file(temp_path, path)
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass

    return path


def get_integration_settings(dcc, version, path=None):
    document = load_integration_config(path=path)
    dcc_data = document.get("dcc_integrations", {}).get(
        text_type(dcc).lower(),
        {}
    )
    if not isinstance(dcc_data, dict):
        return None
    value = dcc_data.get(text_type(version))
    return dict(value) if isinstance(value, dict) else None


def set_integration_settings(dcc, version, settings, path=None):
    document = load_integration_config(path=path)
    integrations = document.setdefault("dcc_integrations", {})
    dcc_key = text_type(dcc).lower()
    dcc_data = integrations.setdefault(dcc_key, {})
    dcc_data[text_type(version)] = dict(settings or {})
    save_integration_config(document, path=path)
    return dict(dcc_data[text_type(version)])


def remove_integration_settings(dcc, version, path=None):
    document = load_integration_config(path=path)
    integrations = document.setdefault("dcc_integrations", {})
    dcc_key = text_type(dcc).lower()
    dcc_data = integrations.get(dcc_key)
    if not isinstance(dcc_data, dict):
        return False

    removed = dcc_data.pop(text_type(version), None) is not None
    if not dcc_data:
        integrations.pop(dcc_key, None)
    if removed:
        save_integration_config(document, path=path)
    return removed


def configured_versions(dcc, path=None):
    document = load_integration_config(path=path)
    dcc_data = document.get("dcc_integrations", {}).get(
        text_type(dcc).lower(),
        {}
    )
    if not isinstance(dcc_data, dict):
        return []
    return sorted(
        [text_type(value) for value in dcc_data.keys()]
    )


__all__ = [
    "INTEGRATION_CONFIG_FILENAME",
    "INTEGRATION_CONFIG_VERSION",
    "configured_versions",
    "default_integration_config",
    "get_integration_settings",
    "integration_config_dir",
    "integration_config_path",
    "load_integration_config",
    "remove_integration_settings",
    "save_integration_config",
    "set_integration_settings",
]
