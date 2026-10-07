"""Reject incomplete or mismatched stable artifacts before publishing a release."""
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path


def shared_file_hash(name, payload):
    # Windows checkout/stamping may use CRLF; this does not change source.
    if Path(name).suffix.lower() in ('.py', '.json', '.svg', '.txt', '.md', '.mel', '.hscript', '.qss'):
        payload = payload.replace(b'\r\n', b'\n')
    return hashlib.sha256(payload).hexdigest()


def package_info(path, version, standalone=False):
    expected = path.with_name(path.name + '.sha256').read_text().split()
    if not expected:
        raise ValueError('Missing checksum: ' + path.name)
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(256 * 1024), b''):
            digest.update(chunk)
    actual = digest.hexdigest()
    if actual != expected[0].lower():
        raise ValueError('Checksum mismatch: ' + path.name)
    with zipfile.ZipFile(path) as archive:
        constants = [n for n in archive.namelist()
                     if n.endswith('/scripts/script_toolbox/constants.py')]
        if len(constants) != 1:
            raise ValueError('Package needs one constants module: ' + path.name)
        root = constants[0][:-len('scripts/script_toolbox/constants.py')]
        source = archive.read(constants[0]).decode('utf-8')
        match = re.search(r'^PLUGIN_VERSION\s*=\s*[\'"]([^\'"]+)', source, re.M)
        if not match or match.group(1) != version:
            raise ValueError('Package version mismatch: ' + path.name)
        scripts = {name[len(root):]: shared_file_hash(name, archive.read(name))
                   for name in archive.namelist()
                   if name.startswith(root + 'scripts/script_toolbox/')
                   and not name.endswith('/')}
        if standalone:
            marker = json.loads(archive.read(root + 'standalone-build.json').decode('utf-8'))
            if marker.get('version') != version or marker.get('package_kind') != 'standalone':
                raise ValueError('Standalone marker version/kind mismatch')
            if root + 'ScriptToolbox.exe' not in archive.namelist():
                raise ValueError('Standalone launcher is missing')
    return actual, scripts


def prepare(directory, version, source_sha):
    if not re.match(r'^\d+\.\d+\.\d+$', version):
        raise ValueError('Stable publication needs a stable SemVer version')
    if not re.match(r'^[0-9a-f]{40}$', source_sha):
        raise ValueError('Stable publication needs a full source commit SHA')
    directory = Path(directory)
    packages = {}
    shared_scripts = None
    for kind, suffix in (('plugin', ''), ('standalone', '-standalone-windows-x64')):
        name = 'script-toolbox-' + version + suffix + '.zip'
        digest, scripts = package_info(directory / name, version, kind == 'standalone')
        if shared_scripts is not None and scripts != shared_scripts:
            raise ValueError('Plugin and standalone contain different shared source files')
        shared_scripts = scripts
        packages[kind] = {'asset_name': name, 'sha256': digest}
    result = {'version': version, 'source_commit': source_sha, 'packages': packages}
    # This manifest is produced only after both complete artifacts validate.
    (directory / 'release-build.json').write_text(
        json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    prepare(sys.argv[1], sys.argv[2], sys.argv[3])
