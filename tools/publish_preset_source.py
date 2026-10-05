# -*- coding: utf-8 -*-
"""Administrator utility: publish canonical preset JSON files as one revision.

The Toolbox client never calls this utility or writes to source folders.
"""
from __future__ import print_function

import argparse
import hashlib
import io
import json
import os
import shutil
import sys
import tempfile
import uuid

SCRIPTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from script_toolbox.core.file_lock import FileLock
from script_toolbox.core.preset_sources import technical_id
from script_toolbox.core.preset_sync import MANIFEST, atomic_json, load_package, read_json, validate_manifest


def publish(input_folder, output_folder, source_id, name):
    technical_id(source_id)
    if not os.path.isdir(output_folder):
        os.makedirs(output_folder)
    with FileLock(os.path.join(output_folder, ".publish.lock")):
        manifest_path = os.path.join(output_folder, MANIFEST)
        previous = (validate_manifest(read_json(manifest_path), source_id)
                    if os.path.isfile(manifest_path) else None)
        revision = previous["revision"] + 1 if previous else 1
        generation = "revision-{0}-{1}".format(revision, uuid.uuid4().hex[:12])
        stage = tempfile.mkdtemp(prefix=".publish-", dir=output_folder)
        try:
            package_folder = os.path.join(stage, generation)
            os.makedirs(package_folder)
            entries = []
            for filename in sorted(os.listdir(input_folder)):
                if not filename.lower().endswith(".json"):
                    continue
                with io.open(os.path.join(input_folder, filename), encoding="utf-8") as handle:
                    preset = json.load(handle)
                preset_id = technical_id(preset.get("id"))
                payload = json.dumps(preset, ensure_ascii=False, indent=2).encode("utf-8")
                destination = preset_id + ".json"
                with open(os.path.join(package_folder, destination), "wb") as handle:
                    handle.write(payload)
                entries.append({"id": preset_id, "file": generation + "/" + destination,
                                "sha256": hashlib.sha256(payload).hexdigest()})
            manifest = {"schema": 1, "id": source_id, "name": name,
                        "revision": revision, "presets": entries}
            atomic_json(os.path.join(stage, MANIFEST), manifest)
            load_package(stage, source_id)
            os.rename(package_folder, os.path.join(output_folder, generation))
            # Publish the pointer last; readers only see complete packages.
            atomic_json(manifest_path, manifest)
            return manifest
        finally:
            shutil.rmtree(stage, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Folder containing canonical preset JSON files")
    parser.add_argument("--output", required=True, help="Shared Preset Source folder")
    parser.add_argument("--id", required=True, help="Stable lowercase source ID")
    parser.add_argument("--name", required=True, help="Source display name")
    arguments = parser.parse_args()
    manifest = publish(arguments.input, arguments.output, arguments.id, arguments.name)
    print("Published {0}, revision {1}, {2} preset(s).".format(
        manifest["id"], manifest["revision"], len(manifest["presets"])))


if __name__ == "__main__":
    main()
