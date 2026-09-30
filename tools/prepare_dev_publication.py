"""Validate both packages before publishing a shared development manifest."""
import hashlib
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path


def prepare(directory, version):
    directory = Path(directory)
    manifest = json.loads((directory / 'dev-manifest.json').read_text(encoding='utf-8'))
    if manifest['version'] != version:
        raise ValueError('Development manifest version mismatch')
    packages = {}
    for kind, alias, suffix in (
        ('plugin', 'script-toolbox-dev.zip', ''),
        ('standalone', 'script-toolbox-standalone-dev.zip', '-standalone-windows-x64'),
    ):
        path = directory / alias
        expected_hash = (directory / (alias + '.sha256')).read_text().split()[0].lower()
        with path.open('rb') as handle:
            digest = hashlib.sha256()
            for chunk in iter(lambda: handle.read(256 * 1024), b''):
                digest.update(chunk)
        actual = digest.hexdigest()
        if actual != expected_hash:
            raise ValueError(kind + ' package checksum mismatch')
        with zipfile.ZipFile(path) as archive:
            if kind == 'standalone':
                names = [name for name in archive.namelist() if name.endswith('/standalone-build.json')]
                if len(names) != 1:
                    raise ValueError('Standalone package needs one build marker')
                package_version = json.loads(archive.read(names[0]).decode('utf-8'))['version']
            else:
                names = [name for name in archive.namelist() if name.endswith('/scripts/script_toolbox/constants.py')]
                if len(names) != 1:
                    raise ValueError('Plugin package needs one constants module')
                match = re.search(r'^PLUGIN_VERSION\s*=\s*[\'"]([^\'"]+)',
                                  archive.read(names[0]).decode('utf-8'), re.M)
                package_version = match.group(1) if match else ''
        if package_version != version:
            raise ValueError(kind + ' package version mismatch: ' + package_version)
        packages[kind] = {'asset_name': 'script-toolbox-{0}{1}.zip'.format(version, suffix),
                          'sha256': actual}
    # Do not prepare any publishable files until all validation has passed.
    for kind, record in packages.items():
        alias = 'script-toolbox-standalone-dev.zip' if kind == 'standalone' else 'script-toolbox-dev.zip'
        name = record['asset_name']
        shutil.copyfile(str(directory / alias), str(directory / name))
        (directory / (name + '.sha256')).write_text(record['sha256'] + '  ' + name + '\n', encoding='utf-8')
    manifest['packages'] = packages
    (directory / 'dev-manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n', encoding='utf-8')


if __name__ == '__main__':
    prepare(sys.argv[1], sys.argv[2])
