# -*- coding: utf-8 -*-
"""Publish readable host/category folders; synchronization remains read only."""
from __future__ import print_function
import copy
import os
import re
import shutil
import tempfile
from .config import _replace_file
from .file_lock import FileLock
from .preset_sources import technical_id
from .preset_sync import MANIFEST, HOST_FOLDERS, atomic_json, load_package, source_file
from ..pycompat import text_type


def path_component(value):
    """Validate a human-readable name portable to Windows network shares."""
    value = text_type(value).strip()
    if (not value or value in ('.', '..') or value.startswith('.') or
            value.endswith(('.', ' ')) or re.search(r'[<>:"/\\|?*\x00-\x1f]', value) or
            value.split('.')[0].upper() in ('CON', 'PRN', 'AUX', 'NUL') or
            re.match(r'^(COM|LPT)[1-9](\.|$)', value, re.I)):
        raise ValueError("Invalid library folder or filename: " + value)
    return value


def preset_path(preset):
    host = next((folder for folder, key in HOST_FOLDERS.items()
                 if key == preset.get('dcc', 'all')), None)
    if host is None:
        raise ValueError("Unknown preset host.")
    categories = [path_component(part) for part in
                  text_type(preset.get('category') or 'General').replace('\\', '/').split('/')]
    filename = path_component(preset.get('label') or preset['id']) + '.json'
    return '/'.join([host] + categories + [filename])


def publish_presets(presets, output_folder, source_id, name, merge=False):
    technical_id(source_id)
    if not os.path.isdir(output_folder):
        os.makedirs(output_folder)
    with FileLock(os.path.join(output_folder, '.publish.lock'), blocking=True):
        previous = load_package(output_folder, source_id) if os.path.isfile(os.path.join(output_folder, MANIFEST)) else None
        if previous is None and any(not entry.startswith('.') for entry in os.listdir(output_folder)):
            raise ValueError("Create a new library in an empty folder.")
        definitions = dict((p['id'], p) for p in previous['presets']) if merge and previous else {}
        incoming_ids = set()
        for preset in presets:
            preset_id = technical_id(preset['id'])
            if preset_id in incoming_ids:
                raise ValueError("Duplicate preset ID: " + preset_id)
            incoming_ids.add(preset_id)
            definitions[preset_id] = copy.deepcopy(preset)
        metadata = {'schema': 1, 'id': source_id,
                    'name': previous['library']['name'] if merge and previous else name}
        stage = tempfile.mkdtemp(prefix='.publish-', dir=output_folder)
        cleanup_stage = True
        try:
            candidate = os.path.join(stage, 'candidate')
            os.makedirs(candidate)
            atomic_json(os.path.join(candidate, MANIFEST), metadata)
            paths = set()
            existing = dict((entry['id'], entry['file']) for entry in previous['manifest']['presets']) if previous else {}
            reserved = dict((path.lower(), preset_id) for preset_id, path in existing.items()
                            if merge and preset_id not in incoming_ids)
            for preset_id, preset in sorted(definitions.items()):
                relative = existing[preset_id] if merge and preset_id not in incoming_ids else preset_path(preset)
                if relative.lower() in paths or reserved.get(relative.lower(), preset_id) != preset_id:
                    relative = relative[:-5] + '-' + preset_id + '.json'
                if relative.lower() in paths or reserved.get(relative.lower(), preset_id) != preset_id:
                    raise ValueError("Duplicate preset filename: " + relative)
                paths.add(relative.lower())
                # Host and categories are determined solely by the folders.
                definition = dict(preset)
                definition.pop('dcc', None)
                definition.pop('category', None)
                atomic_json(source_file(candidate, relative), definition)
            package = load_package(candidate, source_id)
            new_files = set(entry['file'] for entry in package['manifest']['presets'])
            old_files = set(existing.values())
            affected = sorted(new_files | old_files | set([MANIFEST]))
            backup = os.path.join(stage, 'backup')
            os.makedirs(backup)
            saved = set()
            for relative in affected:
                path = source_file(output_folder, relative)
                if os.path.isfile(path):
                    dest = source_file(backup, relative)
                    if not os.path.isdir(os.path.dirname(dest)):
                        os.makedirs(os.path.dirname(dest))
                    shutil.copyfile(path, dest)
                    saved.add(relative)
            changed = []
            try:
                for relative in sorted(new_files) + [MANIFEST]:
                    dest = source_file(output_folder, relative)
                    if not os.path.isdir(os.path.dirname(dest)):
                        os.makedirs(os.path.dirname(dest))
                    _replace_file(source_file(candidate, relative), dest)
                    changed.append(relative)
                for relative in sorted(old_files - new_files):
                    os.unlink(source_file(output_folder, relative))
                    changed.append(relative)
            except Exception:
                try:
                    for relative in reversed(changed):
                        dest = source_file(output_folder, relative)
                        if relative in saved:
                            _replace_file(source_file(backup, relative), dest)
                        elif os.path.exists(dest):
                            os.unlink(dest)
                except Exception:
                    # Retain backups and the publication marker. A partial
                    # rollback must never be mistaken for a complete library.
                    cleanup_stage = False
                    raise ValueError("Publication rollback failed; restore the backups in " + stage)
                raise
            return package['manifest']
        finally:
            if cleanup_stage:
                shutil.rmtree(stage, ignore_errors=True)
