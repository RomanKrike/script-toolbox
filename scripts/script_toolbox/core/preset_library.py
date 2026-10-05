# -*- coding: utf-8 -*-
"""Explicit user publishing; background sync itself remains read only."""
from __future__ import print_function
import copy
import hashlib
import json
import os
import shutil
import tempfile
import uuid
from .file_lock import FileLock
from .preset_sources import technical_id
from .preset_sync import MANIFEST, atomic_json, load_package, read_json, validate_manifest


def publish_presets(presets, output_folder, source_id, name, merge=False):
    technical_id(source_id)
    if not os.path.isdir(output_folder):
        os.makedirs(output_folder)
    with FileLock(os.path.join(output_folder, '.publish.lock'), blocking=True):
        manifest_path = os.path.join(output_folder, MANIFEST)
        previous = (validate_manifest(read_json(manifest_path), source_id)
                    if os.path.isfile(manifest_path) else None)
        definitions = {}
        if merge and previous:
            for preset in load_package(output_folder, source_id)['presets']:
                definitions[preset['id']] = preset
        incoming_ids = set()
        for preset in presets:
            preset_id = technical_id(preset['id'])
            if preset_id in incoming_ids:
                raise ValueError("Duplicate preset ID: " + preset_id)
            incoming_ids.add(preset_id)
            definitions[preset_id] = copy.deepcopy(preset)
        revision = previous['revision'] + 1 if previous else 1
        generation = 'revision-{0}-{1}'.format(revision, uuid.uuid4().hex[:12])
        stage = tempfile.mkdtemp(prefix='.publish-', dir=output_folder)
        try:
            package_folder = os.path.join(stage, generation)
            os.makedirs(package_folder)
            entries = []
            for preset_id, preset in sorted(definitions.items()):
                filename = preset_id + '.json'
                payload = json.dumps(preset, ensure_ascii=False, indent=2).encode('utf-8')
                with open(os.path.join(package_folder, filename), 'wb') as handle:
                    handle.write(payload)
                entries.append({'id': preset_id, 'file': generation + '/' + filename,
                                'sha256': hashlib.sha256(payload).hexdigest()})
            library_name = previous['name'] if merge and previous else name
            manifest = {'schema': 1, 'id': source_id, 'name': library_name,
                        'revision': revision, 'presets': entries}
            atomic_json(os.path.join(stage, MANIFEST), manifest)
            load_package(stage, source_id)
            os.rename(package_folder, os.path.join(output_folder, generation))
            atomic_json(manifest_path, manifest)
            return manifest
        finally:
            shutil.rmtree(stage, ignore_errors=True)
