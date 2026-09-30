"""Windows acceptance: update a running native portable app and confirm its new window."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def main(root):
    root = Path(root).resolve()
    sys.path.insert(0, str(root / 'scripts'))
    from script_toolbox.core import standalone_update
    from script_toolbox.core.file_lock import installation_lock
    temporary = Path(tempfile.mkdtemp(prefix='sbt_restart_'))
    source, destination = temporary / 's', temporary / 'd'
    old_process = helper = None
    restarted_pid = None
    try:
        shutil.copytree(str(root), str(source))
        shutil.copytree(str(root), str(destination))
        # The replacement carries a measurable payload change while retaining
        # the real native launcher, Python and Qt from this workflow build.
        readme = source / 'README.md'
        expected = readme.read_bytes() + b'\nPortable update smoke verified.\n'
        readme.write_bytes(expected)
        (source / standalone_update.MANIFEST_FILENAME).write_text(json.dumps(
            standalone_update.package_manifest(str(source))))
        old_process = subprocess.Popen([str(destination / 'ScriptToolbox.exe')], cwd=str(destination))
        import time
        time.sleep(3)
        if old_process.poll() is not None:
            raise RuntimeError('Initial native app exited before the update')
        with installation_lock(str(destination)):
            standalone_update._prepare_apply_plan(str(source), str(destination), 'smoke')
        script = temporary / 'apply.ps1'
        script.write_text(standalone_update.render_apply_script(), encoding='utf-8')
        powershell = Path(os.environ['SystemRoot']) / 'System32/WindowsPowerShell/v1.0/powershell.exe'
        helper = subprocess.Popen([str(powershell), '-NoProfile', '-NonInteractive', '-ExecutionPolicy',
                                   'Bypass', '-File', str(script), '-Destination', str(destination),
                                   '-ParentProcessId', str(old_process.pid), '-CleanupRoot', str(source)])
        old_process.terminate()
        old_process.wait(timeout=10)
        code = helper.wait(timeout=90)
        status = json.loads((destination / 'standalone-update-status.json').read_text())
        restarted_pid = status.get('restart_pid')
        if code != 0 or status.get('restart') != 'started' or not restarted_pid:
            raise RuntimeError('Native portable restart was not acknowledged: ' + repr(status))
        assert (destination / 'README.md').read_bytes() == expected
        assert not (destination / standalone_update.PORTABLE_TRANSACTION_DIRECTORY).exists()
        print('Native portable replacement and window acknowledgement passed.')
    finally:
        if helper is not None and helper.poll() is None:
            helper.kill()
            helper.wait()
        if old_process is not None and old_process.poll() is None:
            old_process.kill()
            old_process.wait()
        if restarted_pid:
            subprocess.run(['taskkill', '/PID', str(restarted_pid), '/F'], check=False)
        shutil.rmtree(str(temporary), ignore_errors=True)


if __name__ == '__main__':
    main(sys.argv[1])
