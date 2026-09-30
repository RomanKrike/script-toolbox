import hashlib
import json
import zipfile

import pytest

from tools.prepare_dev_publication import prepare
from script_toolbox.core import update_channels, update_package

VERSION = '1.0.1-dev.500'


def make_packages(root, standalone_version=VERSION):
    (root / 'dev-manifest.json').write_text(json.dumps({'version': VERSION}))
    for name, member, content in (
        ('script-toolbox-dev.zip', 'package/scripts/script_toolbox/constants.py', 'PLUGIN_VERSION = "' + VERSION + '"'),
        ('script-toolbox-standalone-dev.zip', 'package/standalone-build.json', json.dumps({'version': standalone_version})),
    ):
        path = root / name
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr(member, content)
        (root / (name + '.sha256')).write_text(hashlib.sha256(path.read_bytes()).hexdigest())


def test_prepare_validates_both_packages_before_announcing(tmp_path):
    make_packages(tmp_path)
    prepare(tmp_path, VERSION)
    manifest = json.loads((tmp_path / 'dev-manifest.json').read_text())
    for record in manifest['packages'].values():
        path = tmp_path / record['asset_name']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record['sha256']
        assert (tmp_path / (path.name + '.sha256')).exists()


@pytest.mark.parametrize('failure', ['version', 'checksum'])
def test_incomplete_or_mismatched_build_never_prepares_publication(tmp_path, failure):
    make_packages(tmp_path, '1.0.1-dev.499' if failure == 'version' else VERSION)
    if failure == 'checksum':
        (tmp_path / 'script-toolbox-standalone-dev.zip.sha256').write_text('0' * 64)
    before = (tmp_path / 'dev-manifest.json').read_bytes()
    with pytest.raises(ValueError, match='mismatch'):
        prepare(tmp_path, VERSION)
    assert (tmp_path / 'dev-manifest.json').read_bytes() == before
    assert not list(tmp_path.glob('script-toolbox-1*.zip'))


@pytest.mark.parametrize('standalone', [False, True])
def test_development_check_uses_manifest_pinned_assets(monkeypatch, standalone):
    versioned = 'script-toolbox-' + VERSION + ('-standalone-windows-x64' if standalone else '') + '.zip'
    aliases = ['script-toolbox-dev.zip', 'script-toolbox-standalone-dev.zip']
    names = aliases + [x + '.sha256' for x in aliases] + [versioned, versioned + '.sha256', 'dev-manifest.json']
    data = {'assets': [{'name': name, 'browser_download_url': 'https://example.invalid/' + name} for name in names]}
    manifest = {'channel': 'development', 'version': VERSION, 'build_number': 500,
                'packages': {'standalone' if standalone else 'plugin': {'asset_name': versioned}}}
    monkeypatch.setattr(update_channels, '_is_standalone', lambda: standalone)
    monkeypatch.setattr(update_channels.updater, '_read_json',
                        lambda url, **kw: manifest if url.endswith('dev-manifest.json') else data)
    result = update_channels.development_release()
    assert result['asset_name'] == versioned
    assert result['download_url'].endswith(versioned)
    assert update_package.validate_installable_release(result)['asset_name'] == versioned


def test_publication_jobs_wait_for_both_builds():
    from pathlib import Path
    source = (Path(__file__).parents[1] / '.github/workflows/dev-build.yml').read_text()
    publish = source.split('  publish:', 1)[1]
    assert 'needs: [package, portable]' in publish
    assert publish.index('dist-publish/script-toolbox-standalone-dev.zip.sha256') < publish.index('dist-publish/dev-manifest.json')
