# -*- coding: utf-8 -*-
"""Filesystem package delivery with immutable generations and atomic pointers."""
from __future__ import print_function

import hashlib
import io
import json
import ntpath
import os
import shutil
import tempfile
import time
import uuid

from ..model import create_item
from ..pycompat import text_type
from .config import _replace_file
from .file_lock import FileLock
from .preset_sources import technical_id

MANIFEST = "library.json"
SNAPSHOT = ".snapshot.json"
HOST_FOLDERS = {"All": "all", "Maya": "maya", "Houdini": "houdini", "Nuke": "nuke", "Blender": "blender"}


class InvalidSource(ValueError):
    pass


def read_json(path):
    with io.open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def atomic_json(path, data):
    folder = os.path.dirname(path)
    if not os.path.isdir(folder):
        os.makedirs(folder)
    fd, temporary = tempfile.mkstemp(prefix=".preset-", dir=folder)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            handle.flush()
            os.fsync(handle.fileno())
        _replace_file(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def source_file(root, relative):
    relative = text_type(relative or "")
    parts = relative.replace("\\", "/").split("/")
    if (not relative or ntpath.splitdrive(relative)[0] or
            os.path.isabs(relative) or relative.startswith(("/", "\\")) or
            any(part in ("", ".", "..") or ":" in part for part in parts)):
        raise InvalidSource("Preset path must stay inside its source folder.")
    root = os.path.normcase(os.path.realpath(root))
    path = os.path.realpath(os.path.join(root, *parts))
    if not os.path.normcase(path).startswith(root + os.sep):
        raise InvalidSource("Preset path escapes the source folder.")
    return path


def validate_manifest(data, expected_id=None):
    if not isinstance(data, dict) or type(data.get("schema")) is not int or data.get("schema") != 1:
        raise InvalidSource("Unsupported source manifest schema.")
    technical_id(data.get("id"))
    if expected_id is not None and data["id"] != expected_id:
        raise InvalidSource("Source ID does not match the configured source.")
    if not isinstance(data.get("name"), text_type) or not data["name"].strip():
        raise InvalidSource("Library needs a nonempty name.")
    if "presets" in data or "revision" in data:
        raise InvalidSource("Library metadata must not contain a preset index or revision.")
    return data


def load_package(root, expected_id=None):
    manifest = validate_manifest(read_json(source_file(root, MANIFEST)), expected_id)
    if any(name.startswith(".publish-") for name in os.listdir(root)):
        raise InvalidSource("Library publication is in progress; retry shortly.")
    entries, presets, preset_ids, portable_paths = [], [], set(), set()
    def fail_walk(error):
        raise error
    for folder, dirs, files in os.walk(root, onerror=fail_walk):
        dirs[:] = sorted(d for d in dirs if not d.startswith("."))
        for directory in dirs:
            if os.path.islink(os.path.join(folder, directory)):
                raise InvalidSource("Library directories must not be symbolic links.")
            source_file(root, os.path.relpath(os.path.join(folder, directory), root))
        for filename in sorted(files):
            if filename.startswith(".") or not filename.lower().endswith(".json"):
                continue
            relative = os.path.relpath(os.path.join(folder, filename), root).replace(os.sep, "/")
            if relative == MANIFEST:
                continue
            parts = relative.split("/")
            if len(parts) < 2 or parts[0] not in HOST_FOLDERS:
                raise InvalidSource("Place presets inside All, Maya, Houdini, Nuke or Blender: " + relative)
            portable = relative.lower()
            if portable in portable_paths:
                raise InvalidSource("Duplicate portable preset path: " + relative)
            portable_paths.add(portable)
            path = source_file(root, relative)
            with open(path, "rb") as handle:
                payload = handle.read()
            preset = json.loads(payload.decode("utf-8"))
            if not isinstance(preset, dict):
                raise InvalidSource("Preset must be a JSON object: " + relative)
            preset_id = technical_id(preset.get("id"))
            if preset_id in preset_ids:
                raise InvalidSource("Duplicate preset ID: " + preset_id)
            preset_ids.add(preset_id)
            preset["dcc"] = HOST_FOLDERS[parts[0]]
            preset["category"] = "/".join(parts[1:-1]) or "General"
            entries.append({"id": preset_id, "file": relative,
                            "sha256": hashlib.sha256(payload).hexdigest()})
            presets.append(preset)
    for preset in presets:
        root_item = preset.get("root")
        if not isinstance(root_item, dict):
            raise InvalidSource("Preset needs an Item root.")
        ids = set()

        def validate_item(raw):
            if (not isinstance(raw, dict) or not isinstance(raw.get("id"), text_type)
                    or not raw["id"].strip()):
                raise InvalidSource("Every published Item needs a stable ID.")
            if raw["id"] in ids or raw.get("kind") == "reference":
                raise InvalidSource("Duplicate Item ID or nested reference.")
            ids.add(raw["id"])
            for child in raw.get("items", []):
                validate_item(child)

        validate_item(root_item)
        preset["root"] = create_item(root_item.get("kind"), root_item)
        if preset.get("dcc", "all") not in ("all", "maya", "nuke", "houdini", "blender"):
            raise InvalidSource("Unknown preset DCC.")
    entries.sort(key=lambda entry: entry["file"])
    fingerprint = hashlib.sha256(json.dumps({"library": manifest, "presets": entries},
                                sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    snapshot = dict(manifest, revision=fingerprint, presets=entries)
    return {"manifest": snapshot, "presets": sorted(presets, key=lambda preset: preset["id"]),
            "library": manifest}


class SyncService(object):
    def __init__(self, registry):
        self.registry = registry

    def installed(self, source_id):
        root = self.registry.cache_path(source_id)
        if not os.path.isdir(root):
            return None
        with FileLock(os.path.join(root, ".active.lock"), blocking=True):
            return self._installed_unlocked(root, source_id)

    def _installed_unlocked(self, root, source_id):
        try:
            pointer = read_json(os.path.join(root, "active.json"))
        except (IOError, OSError, ValueError):
            return None
        if not isinstance(pointer, dict):
            return None
        for key in ("current", "previous"):
            generation = pointer.get(key)
            if not generation:
                continue
            try:
                package = load_package(source_file(root, generation), source_id)
                if read_json(source_file(source_file(root, generation), SNAPSHOT)) != package["manifest"]:
                    raise InvalidSource("Local snapshot checksum mismatch.")
                package["generation"] = generation
                return package
            except (IOError, OSError, ValueError, TypeError, KeyError):
                continue
        return None

    def status(self, source_id):
        installed = self.installed(source_id)
        root = self.registry.cache_path(source_id)
        try:
            status = read_json(os.path.join(root, "status.json"))
        except (IOError, OSError, ValueError):
            status = {"state": "not_installed"}
        if not isinstance(status, dict) or "state" not in status:
            status = {"state": "not_installed"}
        status["local_revision"] = (installed["manifest"]["revision"]
                                    if installed else None)
        status["using_cache"] = bool(installed)
        return status

    def due(self, source, startup=False):
        if not source["enabled"] or source["update_policy"] == "manual":
            return False
        if source["update_policy"] == "on_start" and not startup:
            return False
        elapsed = time.time() - self.status(source["id"]).get("last_check", 0)
        threshold = 60 if source["update_policy"] == "on_start" else source["interval_minutes"] * 60
        return elapsed >= threshold

    def check(self, source_id, download=False):
        source = self.registry.get(source_id)
        if source is None:
            raise ValueError("Source not configured.")
        if not source["enabled"]:
            return self.status(source_id)
        root = self.registry.cache_path(source_id)
        with FileLock(os.path.join(root, ".sync.lock")):
            status = self.status(source_id)
            status["last_check"] = time.time()
            stage = None
            phase = "check"
            try:
                remote = source["remote_path"]
                package = load_package(remote, source_id)
                manifest = package["manifest"]
                installed = self.installed(source_id)
                status["remote_revision"] = manifest["revision"]
                if installed and installed["manifest"] == manifest:
                    status["state"] = "up_to_date"
                elif not download:
                    status["state"] = "update_available"
                else:
                    phase = "copy"
                    status["state"] = "syncing"
                    atomic_json(os.path.join(root, "status.json"), status)
                    stage = tempfile.mkdtemp(prefix=".staging-", dir=root)
                    for entry in manifest["presets"]:
                        destination = source_file(stage, entry["file"])
                        folder = os.path.dirname(destination)
                        if not os.path.isdir(folder):
                            os.makedirs(folder)
                        shutil.copyfile(source_file(remote, entry["file"]), destination)
                    atomic_json(os.path.join(stage, MANIFEST), package["library"])
                    if load_package(stage, source_id)["manifest"] != manifest:
                        raise InvalidSource("Preset changed while copying; retry shortly.")
                    atomic_json(os.path.join(stage, SNAPSHOT), manifest)
                    if load_package(remote, source_id)["manifest"] != manifest:
                        raise InvalidSource("Source changed during sync; retry after publication.")
                    old = installed.get("generation") if installed else None
                    generation = "generation-" + uuid.uuid4().hex
                    os.rename(stage, os.path.join(root, generation))
                    stage = None
                    with FileLock(os.path.join(root, ".active.lock"), blocking=True):
                        atomic_json(os.path.join(root, "active.json"),
                                    {"current": generation, "previous": old})
                        # Resolvers hold complete in-memory snapshots. Protect
                        # other processes loading a snapshot during cleanup.
                        for candidate in os.listdir(root):
                            if candidate.startswith("generation-") and candidate not in (generation, old):
                                shutil.rmtree(os.path.join(root, candidate), ignore_errors=True)
                    status.update(state="up_to_date", last_sync=time.time())
                status.pop("error", None)
            except (ValueError, TypeError, KeyError) as exc:
                status.update(state="invalid_source", error=text_type(exc))
            except (IOError, OSError) as exc:
                status.update(state="offline" if phase == "check" else "sync_failed",
                              error=text_type(exc))
            finally:
                if stage is not None:
                    shutil.rmtree(stage, ignore_errors=True)
            atomic_json(os.path.join(root, "status.json"), status)
            return self.status(source_id)
