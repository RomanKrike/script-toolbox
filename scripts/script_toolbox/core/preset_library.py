# -*- coding: utf-8 -*-
"""Publish readable host/category folders; synchronization remains read only."""
from __future__ import print_function
import copy
import os
import re
import shutil
import tempfile
import uuid
from .config import _replace_file
from .file_lock import FileLock
from .preset_sources import technical_id
from .preset_sync import (MANIFEST, HOST_FOLDERS, InvalidSource, atomic_json,
                          load_package, read_json, source_file)
from .update_package import sha256_file
from ..pycompat import text_type

PUBLICATION_JOURNAL = '.transaction.json'


def _recover_publication(root, stage):
    """Rollback is restartable: never consume the only copy of a backup."""
    journal = read_json(os.path.join(stage, PUBLICATION_JOURNAL))
    if (not isinstance(journal, dict) or journal.get('schema') != 1 or
            journal.get('phase') not in ('building', 'prepared', 'committed')):
        raise InvalidSource('Invalid publication recovery journal: ' + stage)
    if journal['phase'] == 'prepared':
        entries = journal.get('entries')
        if not isinstance(entries, list):
            raise InvalidSource('Invalid publication recovery entries: ' + stage)
        seen = set()
        # Validate every recovery path and backup before changing any file.
        for entry in entries:
            relative = entry['file']
            parts = relative.split('/')
            if (relative in seen or type(entry.get('existed')) is not bool or
                    (relative != MANIFEST and (len(parts) < 2 or
                     parts[0] not in HOST_FOLDERS or not relative.endswith('.json')))):
                raise InvalidSource('Invalid publication recovery path: ' + relative)
            seen.add(relative)
            source_file(root, relative)
            if entry['existed']:
                backup = source_file(os.path.join(stage, 'backup'), relative)
                if sha256_file(backup) != entry['sha256']:
                    raise InvalidSource('Publication backup checksum mismatch: ' + relative)
        for entry in reversed(entries):
            dest = source_file(root, entry['file'])
            if entry['existed']:
                backup = source_file(os.path.join(stage, 'backup'), entry['file'])
                fd, temporary = tempfile.mkstemp(prefix='.restore-', dir=os.path.dirname(backup))
                os.close(fd)
                try:
                    shutil.copyfile(backup, temporary)
                    if not os.path.isdir(os.path.dirname(dest)):
                        os.makedirs(os.path.dirname(dest))
                    _replace_file(temporary, dest)
                finally:
                    if os.path.exists(temporary):
                        os.unlink(temporary)
            elif os.path.isfile(dest):
                os.unlink(dest)
    shutil.rmtree(stage)


def _recover_publications_unlocked(root):
    for name in sorted(os.listdir(root)):
        if name.startswith('.publish-'):
            stage = source_file(root, name)
            if os.path.islink(os.path.join(root, name)):
                raise InvalidSource('Publication recovery directories must not be symbolic links.')
            try:
                _recover_publication(root, stage)
            except Exception as exc:
                raise InvalidSource('Publication recovery failed; backups retained at {0}: {1}'.format(stage, exc))


def recover_publications(root):
    """A reader may recover a crashed writer, but must not interrupt a live one."""
    from .file_lock import FileLockError
    try:
        with FileLock(os.path.join(root, '.publish.lock')):
            _recover_publications_unlocked(root)
    except FileLockError:
        raise InvalidSource('Library publication is in progress; retry shortly.')


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
        _recover_publications_unlocked(output_folder)
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
        # Only expose a publication marker after its recovery journal exists.
        stage = tempfile.mkdtemp(prefix='.prepare-', dir=output_folder)
        cleanup_stage = True
        try:
            atomic_json(os.path.join(stage, PUBLICATION_JOURNAL), {'schema': 1, 'phase': 'building'})
            published_stage = os.path.join(output_folder, '.publish-' + uuid.uuid4().hex)
            os.rename(stage, published_stage)
            stage = published_stage
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
            entries = []
            for relative in affected:
                path = source_file(output_folder, relative)
                if os.path.isfile(path):
                    dest = source_file(backup, relative)
                    if not os.path.isdir(os.path.dirname(dest)):
                        os.makedirs(os.path.dirname(dest))
                    shutil.copyfile(path, dest)
                entries.append({'file': relative, 'existed': os.path.isfile(path),
                                'sha256': sha256_file(path) if os.path.isfile(path) else None})
            atomic_json(os.path.join(stage, PUBLICATION_JOURNAL),
                        {'schema': 1, 'phase': 'prepared', 'entries': entries})
            try:
                for relative in sorted(new_files) + [MANIFEST]:
                    dest = source_file(output_folder, relative)
                    if not os.path.isdir(os.path.dirname(dest)):
                        os.makedirs(os.path.dirname(dest))
                    _replace_file(source_file(candidate, relative), dest)
                for relative in sorted(old_files - new_files):
                    os.unlink(source_file(output_folder, relative))
                atomic_json(os.path.join(stage, PUBLICATION_JOURNAL),
                            {'schema': 1, 'phase': 'committed'})
            except Exception:
                try:
                    _recover_publication(output_folder, stage)
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
