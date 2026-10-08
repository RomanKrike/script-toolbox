import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from script_toolbox.core.preset_library import publish_presets
from script_toolbox.core.preset_sync import load_package, InvalidSource
from script_toolbox.core.file_lock import FileLock
from script_toolbox.model import create_item


def preset(preset_id, label):
    return {'id': preset_id, 'label': label,
            'root': create_item('string', {'id': 'value', 'name': 'value'})}


CHILD = '''
import os
from script_toolbox.core import preset_library as p
from script_toolbox.model import create_item
root = os.environ['AUDIT_REMOTE']
boundary = os.environ['AUDIT_BOUNDARY']
real_replace, real_json, real_unlink = p._replace_file, p.atomic_json, os.unlink
calls = [0]
def replace(source, dest):
    real_replace(source, dest)
    calls[0] += 1
    if boundary == 'replace-' + str(calls[0]) or boundary == 'recovery':
        os._exit(73)
def atomic_json(path, data):
    real_json(path, data)
    if data.get('phase') == boundary:
        os._exit(73)
def unlink(path, *args, **kwargs):
    real_unlink(path, *args, **kwargs)
    if boundary == 'delete' and path.endswith('Old.json'):
        os._exit(73)
p._replace_file, p.atomic_json, os.unlink = replace, atomic_json, unlink
if boundary == 'recovery':
    p.recover_publications(root)
else:
    p.publish_presets([{'id': key, 'label': key.upper(),
        'root': create_item('string', {'id':'value', 'name':'value'})}
        for key in ('a', 'b')], root, 'studio', 'Studio')
'''


def interrupt(root, boundary):
    env = dict(os.environ, AUDIT_REMOTE=str(root), AUDIT_BOUNDARY=boundary,
               PYTHONPATH=str(Path(__file__).parents[1] / 'scripts'))
    result = subprocess.run([sys.executable, '-c', CHILD], env=env,
                            capture_output=True, text=True, timeout=15)
    assert result.returncode == 73, result.stdout + result.stderr


@pytest.mark.parametrize('boundary', ['prepared', 'replace-1', 'replace-2', 'replace-3', 'delete', 'committed'])
def test_crash_at_publication_boundary_recovers_complete_generation(tmp_path, boundary):
    root = tmp_path / 'library'
    publish_presets([preset('old', 'Old')], str(root), 'studio', 'Studio')
    interrupt(root, boundary)
    assert list(root.glob('.publish-*'))
    package = load_package(str(root))
    assert [p['id'] for p in package['presets']] == (['a', 'b'] if boundary == 'committed' else ['old'])
    assert not list(root.glob('.publish-*'))
    publish_presets([preset('final', 'Final')], str(root), 'studio', 'Studio')
    assert [p['id'] for p in load_package(str(root))['presets']] == ['final']


def test_recovery_can_itself_be_interrupted_and_retried(tmp_path):
    root = tmp_path / 'library'
    publish_presets([preset('old', 'Old')], str(root), 'studio', 'Studio')
    interrupt(root, 'delete')
    interrupt(root, 'recovery')
    assert [p['id'] for p in load_package(str(root))['presets']] == ['old']
    assert not list(root.glob('.publish-*'))


def test_reader_never_recovers_live_publication(tmp_path):
    root = tmp_path / 'library'
    publish_presets([preset('old', 'Old')], str(root), 'studio', 'Studio')
    marker = root / '.publish-fixture'
    marker.mkdir()
    (marker / '.transaction.json').write_text(json.dumps({'schema':1, 'phase':'building'}))
    with FileLock(str(root / '.publish.lock')):
        with pytest.raises(InvalidSource, match='in progress'):
            load_package(str(root))
        assert marker.exists()
    assert [p['id'] for p in load_package(str(root))['presets']] == ['old']


def test_tampered_backup_is_preserved_without_partial_recovery(tmp_path):
    root = tmp_path / 'library'
    publish_presets([preset('old', 'Old')], str(root), 'studio', 'Studio')
    interrupt(root, 'replace-1')
    stage = next(root.glob('.publish-*'))
    (stage / 'backup/All/General/Old.json').write_text('damaged')
    before = (root / 'All/General/A.json').read_bytes()
    with pytest.raises(InvalidSource, match='checksum'):
        load_package(str(root))
    assert (root / 'All/General/A.json').read_bytes() == before
    assert stage.exists()
