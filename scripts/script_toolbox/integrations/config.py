# -*- coding: utf-8 -*-
from __future__ import print_function

import hashlib
import io
import json
import os
import tempfile

from ..pycompat import text_type


INTEGRATION_CONFIG_VERSION = 2
INTEGRATION_CONFIG_FILENAME = "dcc_integrations.json"
DEFAULT_PROFILE_ID = "default"


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
        "dcc_profile_roots": {},
    }


def _normalize_root_record(record):
    if not isinstance(record, dict):
        return None

    raw_path = text_type(record.get("path") or "").strip()
    if not raw_path:
        return None

    normalized_path = os.path.normpath(
        os.path.expanduser(raw_path)
    )
    profile_id = text_type(
        record.get("id") or profile_id_for_path(normalized_path)
    ).strip()
    label = text_type(record.get("label") or "").strip()
    if not label:
        label = os.path.basename(normalized_path.rstrip("\\/")) or "Custom"

    return {
        "id": profile_id,
        "label": label,
        "path": normalized_path,
    }


def _normalize_document(raw):
    if not isinstance(raw, dict):
        return default_integration_config()

    result = default_integration_config()

    integrations = raw.get("dcc_integrations", {})
    if isinstance(integrations, dict):
        result["dcc_integrations"] = integrations

    roots = raw.get("dcc_profile_roots", {})
    if isinstance(roots, dict):
        normalized_roots = {}
        for dcc, records in roots.items():
            if not isinstance(records, list):
                continue
            cleaned = []
            seen = set()
            for record in records:
                normalized = _normalize_root_record(record)
                if normalized is None:
                    continue
                profile_id = normalized["id"]
                if profile_id in seen:
                    continue
                seen.add(profile_id)
                cleaned.append(normalized)
            if cleaned:
                normalized_roots[text_type(dcc).lower()] = cleaned
        result["dcc_profile_roots"] = normalized_roots

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


def profile_id_for_path(profile_path):
    normalized = os.path.normcase(
        os.path.normpath(
            os.path.expanduser(
                text_type(profile_path or "").strip()
            )
        )
    )
    encoded = normalized.encode("utf-8")
    return "custom-{0}".format(
        hashlib.sha1(encoded).hexdigest()[:12]
    )


def integration_target_key(version, profile_id=None):
    version = text_type(version)
    profile_id = text_type(
        profile_id or DEFAULT_PROFILE_ID
    ).strip()
    if not profile_id or profile_id == DEFAULT_PROFILE_ID:
        return version
    return "{0}::{1}".format(version, profile_id)


def get_integration_settings(
    dcc,
    version,
    path=None,
    profile_id=None
):
    document = load_integration_config(path=path)
    dcc_data = document.get("dcc_integrations", {}).get(
        text_type(dcc).lower(),
        {}
    )
    if not isinstance(dcc_data, dict):
        return None

    key = integration_target_key(version, profile_id)
    value = dcc_data.get(key)
    return dict(value) if isinstance(value, dict) else None


def set_integration_settings(
    dcc,
    version,
    settings,
    path=None,
    profile_id=None
):
    document = load_integration_config(path=path)
    integrations = document.setdefault("dcc_integrations", {})
    dcc_key = text_type(dcc).lower()
    dcc_data = integrations.setdefault(dcc_key, {})
    target_key = integration_target_key(version, profile_id)
    dcc_data[target_key] = dict(settings or {})
    save_integration_config(document, path=path)
    return dict(dcc_data[target_key])


def remove_integration_settings(
    dcc,
    version,
    path=None,
    profile_id=None
):
    document = load_integration_config(path=path)
    integrations = document.setdefault("dcc_integrations", {})
    dcc_key = text_type(dcc).lower()
    dcc_data = integrations.get(dcc_key)
    if not isinstance(dcc_data, dict):
        return False

    target_key = integration_target_key(version, profile_id)
    removed = dcc_data.pop(target_key, None) is not None
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

    versions = set()
    for value in dcc_data.keys():
        versions.add(text_type(value).split("::", 1)[0])
    return sorted(versions)


def get_profile_roots(dcc, path=None):
    document = load_integration_config(path=path)
    roots = document.get("dcc_profile_roots", {}).get(
        text_type(dcc).lower(),
        []
    )
    return [dict(item) for item in roots if isinstance(item, dict)]


def add_profile_root(
    dcc,
    profile_path,
    label="",
    path=None
):
    normalized_path = os.path.normpath(
        os.path.expanduser(
            text_type(profile_path or "").strip()
        )
    )
    if not normalized_path:
        raise ValueError("Profile path is empty.")

    record = {
        "id": profile_id_for_path(normalized_path),
        "label": text_type(label or "").strip(),
        "path": normalized_path,
    }
    record = _normalize_root_record(record)

    document = load_integration_config(path=path)
    roots_by_dcc = document.setdefault("dcc_profile_roots", {})
    dcc_key = text_type(dcc).lower()
    roots = roots_by_dcc.setdefault(dcc_key, [])

    replaced = False
    for index, existing in enumerate(roots):
        if existing.get("id") == record["id"]:
            roots[index] = record
            replaced = True
            break
    if not replaced:
        roots.append(record)

    save_integration_config(document, path=path)
    return dict(record)


def remove_profile_root(dcc, profile_id, path=None):
    document = load_integration_config(path=path)
    roots_by_dcc = document.setdefault("dcc_profile_roots", {})
    dcc_key = text_type(dcc).lower()
    roots = roots_by_dcc.get(dcc_key)
    if not isinstance(roots, list):
        return False

    profile_id = text_type(profile_id)
    filtered = [
        item for item in roots
        if text_type(item.get("id") or "") != profile_id
    ]
    if len(filtered) == len(roots):
        return False

    if filtered:
        roots_by_dcc[dcc_key] = filtered
    else:
        roots_by_dcc.pop(dcc_key, None)
    save_integration_config(document, path=path)
    return True


def find_profile_id_for_paths(dcc, candidate_paths, path=None):
    normalized_candidates = set()
    for candidate in candidate_paths or []:
        value = text_type(candidate or "").strip()
        if not value:
            continue
        normalized_candidates.add(
            os.path.normcase(
                os.path.normpath(
                    os.path.expanduser(value)
                )
            )
        )

    for record in get_profile_roots(dcc, path=path):
        root_path = os.path.normcase(
            os.path.normpath(record["path"])
        )
        if root_path in normalized_candidates:
            return record["id"]

    return DEFAULT_PROFILE_ID


__all__ = [
    "DEFAULT_PROFILE_ID",
    "INTEGRATION_CONFIG_FILENAME",
    "INTEGRATION_CONFIG_VERSION",
    "add_profile_root",
    "configured_versions",
    "default_integration_config",
    "find_profile_id_for_paths",
    "get_integration_settings",
    "get_profile_roots",
    "integration_config_dir",
    "integration_config_path",
    "integration_target_key",
    "load_integration_config",
    "profile_id_for_path",
    "remove_integration_settings",
    "remove_profile_root",
    "save_integration_config",
    "set_integration_settings",
]
