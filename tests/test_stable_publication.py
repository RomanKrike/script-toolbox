import hashlib
import json
import zipfile
from pathlib import Path

import pytest

from tools.prepare_stable_publication import prepare
from script_toolbox.core import updater

VERSION = '1.1.0'
COMMIT = 'a' * 40


def packages(root, failure=None):
    for kind, suffix in (('plugin', ''), ('standalone', '-standalone-windows-x64')):
        if kind == 'standalone' and failure == 'missing':
            continue
        name = 'script-toolbox-' + VERSION + suffix + '.zip'
        path = root / name
        version = '1.0.1' if kind == 'standalone' and failure == 'version' else VERSION
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr('ScriptToolbox/scripts/script_toolbox/constants.py',
                             'PLUGIN_VERSION = "' + version + ('"\r\n' if kind == 'standalone' and failure == 'crlf' else '"\n'))
            archive.writestr('ScriptToolbox/scripts/script_toolbox/__init__.py',
                             '# different' if kind == 'standalone' and failure == 'source' else '# same')
            if kind == 'standalone':
                archive.writestr('ScriptToolbox/standalone-build.json', json.dumps({
                    'version': '1.0.1' if failure == 'marker' else VERSION,
                    'package_kind': 'standalone'}))
                archive.writestr('ScriptToolbox/ScriptToolbox.exe', b'fixture')
        checksum = hashlib.sha256(path.read_bytes()).hexdigest()
        if kind == 'standalone' and failure == 'checksum':
            checksum = '0' * 64
        (root / (name + '.sha256')).write_text(checksum + '  ' + name + '\n')


def test_complete_stable_release_supports_both_updaters(tmp_path, monkeypatch):
    packages(tmp_path)
    result = prepare(tmp_path, VERSION, COMMIT)
    assert result['source_commit'] == COMMIT
    assert json.loads((tmp_path / 'release-build.json').read_text()) == result
    assets = []
    for info in result['packages'].values():
        for name in (info['asset_name'], info['asset_name'] + '.sha256'):
            assets.append({'name': name, 'browser_download_url': 'https://example.invalid/' + name})
    monkeypatch.setattr(updater, '_read_json', lambda *a, **k: {'tag_name': 'v' + VERSION, 'assets': assets})
    for kind in ('plugin', 'standalone'):
        update = updater.check_for_update(current_version='1.0.1', package_kind=kind)
        assert update['available'] and update['error'] is None
        assert update['release']['asset_name'] == result['packages'][kind]['asset_name']


@pytest.mark.parametrize('failure', ['missing', 'checksum', 'version', 'marker', 'source'])
def test_bad_stable_package_never_prepares_publication(tmp_path, failure):
    packages(tmp_path, failure)
    with pytest.raises((ValueError, FileNotFoundError)):
        prepare(tmp_path, VERSION, COMMIT)
    assert not (tmp_path / 'release-build.json').exists()


def test_stable_workflow_waits_for_both_artifacts_and_publishes_draft_last():
    workflow = (Path(__file__).parents[1] / '.github/workflows/release.yml').read_text()
    source = workflow.split('  source:', 1)[1].split('  plugin:', 1)[0]
    assert "github.event.workflow_run.event == 'push'" in source
    assert "github.event.workflow_run.head_branch == 'main'" in source
    assert 'github.event.workflow_run.head_repository.full_name == github.repository' in source
    publish = workflow.split('  publish:', 1)[1]
    assert 'needs: [source, plugin, portable]' in publish
    assert "needs.portable.result == 'success'" in publish
    assert 'tools/prepare_stable_publication.py' in publish
    assert publish.index('standalone-windows-x64.zip.sha256') < publish.index('--draft=false')
    reusable = (Path(__file__).parents[1] / '.github/workflows/standalone-build.yml').read_text()
    assert 'workflow_call:' in reusable and 'inputs.source_sha || github.sha' in reusable


def test_windows_checkout_line_endings_preserve_shared_source_identity(tmp_path):
    packages(tmp_path, 'crlf')
    assert prepare(tmp_path, VERSION, COMMIT)['version'] == VERSION


def test_real_builders_produce_matching_shared_source(tmp_path):
    from tools.build_release import build_release
    from tools.build_standalone_portable import build_portable
    root = str(Path(__file__).parents[1])
    runtime = tmp_path / 'runtime'
    runtime.mkdir()
    (runtime / 'python311.dll').write_bytes(b'fixture-runtime')
    launcher = tmp_path / 'ScriptToolbox.exe'
    launcher.write_bytes(b'fixture-launcher')
    output = tmp_path / 'dist'
    build_release(root=root, output_dir=str(output), version=VERSION)
    portable = build_portable(root=root, output_dir=str(tmp_path / 'portable'),
                              runtime_dir=str(runtime), launcher_path=str(launcher), version=VERSION)
    import shutil
    for key in ('archive_path', 'checksum_path'):
        shutil.copy2(portable[key], output)
    assert len(prepare(output, VERSION, COMMIT)['packages']) == 2
