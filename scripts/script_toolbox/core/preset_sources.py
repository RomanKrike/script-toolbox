# -*- coding: utf-8 -*-
"""User-owned source connections. No network access or cache writes here."""
from __future__ import print_function

import copy
import os
import re

from ..pycompat import text_type
from .preferences import load_preferences, save_preferences
from .user_paths import user_config_dir, settings_path
from .file_lock import FileLock

SOURCE_KEY = "preset_sources"
POLICIES = ("manual", "on_start", "periodic")


def technical_id(value):
    value = text_type(value or "")
    if not re.match(r"^[a-z0-9][a-z0-9_-]{0,127}$", value):
        raise ValueError("Invalid source/preset ID: {0!r}".format(value))
    return value


def normalize_source(source):
    result = {
        "id": technical_id(source.get("id")),
        "name": text_type(source.get("name") or source.get("id")),
        "remote_path": text_type(source.get("remote_path") or "").strip(),
        "enabled": bool(source.get("enabled", True)),
        "update_policy": source.get("update_policy", "manual"),
        "interval_minutes": int(source.get("interval_minutes", 60)),
    }
    if not result["remote_path"]:
        raise ValueError("A source folder is required.")
    if result["update_policy"] not in POLICIES:
        raise ValueError("Unknown update policy.")
    if result["interval_minutes"] < 1:
        raise ValueError("Check interval must be at least one minute.")
    return result


class SourceRegistry(object):
    def __init__(self, preferences_path=None, cache_root=None):
        # Host APIs (e.g. Maya internalVar) must run on the creating thread.
        # Background publishing/sync must use this same preferences file,
        # rather than resolving the host path again and falling back to home.
        self.preferences_path = preferences_path or settings_path()
        self.cache_root = cache_root or os.path.join(
            user_config_dir(), "presets", "managed")

    def sources(self):
        raw = load_preferences(self.preferences_path).get(SOURCE_KEY, [])
        if not isinstance(raw, list):
            raise ValueError("Preset sources must be a list.")
        result = [normalize_source(source) for source in raw]
        if len(set(source["id"] for source in result)) != len(result):
            raise ValueError("Duplicate source IDs.")
        return result

    def get(self, source_id):
        for source in self.sources():
            if source["id"] == source_id:
                return source
        return None

    def put(self, source):
        source = normalize_source(source)
        with FileLock(self.preferences_path + ".sources.lock", blocking=True):
            return self._put_unlocked(source)

    def _put_unlocked(self, source):
        preferences = load_preferences(self.preferences_path)
        sources = list(preferences.get(SOURCE_KEY, []))
        for index, old in enumerate(sources):
            if old["id"] == source["id"]:
                sources[index] = source
                break
        else:
            sources.append(source)
        preferences[SOURCE_KEY] = sources
        save_preferences(preferences, self.preferences_path)
        return copy.deepcopy(source)

    def remove(self, source_id):
        with FileLock(self.preferences_path + ".sources.lock", blocking=True):
            self._remove_unlocked(source_id)

    def _remove_unlocked(self, source_id):
        preferences = load_preferences(self.preferences_path)
        preferences[SOURCE_KEY] = [source for source in
                                   preferences.get(SOURCE_KEY, [])
                                   if source["id"] != source_id]
        save_preferences(preferences, self.preferences_path)
        # Cache is retained; user configs and network folders are never touched.

    def cache_path(self, source_id):
        return os.path.join(self.cache_root, technical_id(source_id))
