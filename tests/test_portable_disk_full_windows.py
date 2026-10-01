"""Opt-in Windows acceptance on a disposable 128 MiB NTFS virtual disk."""
import ctypes
import errno
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

import pytest

from script_toolbox.core import standalone_update
from test_portable_transaction_windows import command, script_path


pytestmark = pytest.mark.skipif(
    os.name != "nt" or os.environ.get("SCRIPT_TOOLBOX_TEST_VHD") != "1",
    reason="Requires an explicitly enabled Windows VHD acceptance runner",
)


def diskpart(tmp_path, commands):
    script = tmp_path / "diskpart.txt"
    script.write_text("\n".join(commands + ["exit", ""]), encoding="ascii")
    executable = Path(os.environ["SystemRoot"]) / "System32" / "diskpart.exe"
    result = subprocess.run([str(executable), "/s", str(script)],
                            capture_output=True, timeout=60)
    assert result.returncode == 0, (result.stdout, result.stderr)
    return result.stdout.decode(errors="replace")


@pytest.fixture
def small_volume(tmp_path):
    assert ctypes.windll.shell32.IsUserAnAdmin(), "VHD acceptance requires an elevated CI runner"
    image = tmp_path / "owned-test-disk.vhd"
    mount = tmp_path / "volume"
    mount.mkdir()
    assert not image.exists()
    try:
        output = diskpart(tmp_path, [
            'create vdisk file="{0}" maximum=128 type=expandable'.format(image),
            'select vdisk file="{0}"'.format(image),
            "attach vdisk",
            "create partition primary",
            "format fs=ntfs quick label=STB_DISKFULL",
            'assign mount="{0}"'.format(mount),
        ])
        # DiskPart can return zero after a command error. Never fill a normal
        # directory on the runner's system disk if attach/format/assign failed.
        assert os.path.ismount(str(mount)), output
        size = shutil.disk_usage(str(mount)).total
        assert 32 * 1024**2 < size <= 128 * 1024**2, (size, output)
        yield mount
    finally:
        if image.exists():
            diskpart(tmp_path, ['select vdisk file="{0}"'.format(image), "detach vdisk"])
            assert not os.path.ismount(str(mount)), "Test virtual disk remained mounted"


def exhaust_volume(mount):
    """Get a real disk-full error, then retain room only for status metadata."""
    assert os.path.ismount(str(mount))
    size = shutil.disk_usage(str(mount)).total
    assert 32 * 1024**2 < size <= 128 * 1024**2
    reserve = mount / "diagnostic-reserve.bin"
    reserve.write_bytes(b"R" * (512 * 1024))
    filler = mount / "owned-filler.bin"
    observed = None
    written = 0
    try:
        with open(str(filler), "wb", buffering=0) as handle:
            for block_size in (1024 * 1024, 4096):
                block = b"F" * block_size
                while written <= size:
                    try:
                        count = handle.write(block)
                        assert count, "Unexpected zero-byte write"
                        written += count
                    except OSError as exc:
                        assert exc.errno == errno.ENOSPC or getattr(exc, "winerror", None) in (39, 112), exc
                        observed = exc
                        break
                assert written <= size, "Write limit reached without a disk-full error"
        assert observed is not None, "The filesystem never reported disk full"
    finally:
        # Keep enough room for the real helper to record failure/recovery.
        reserve.unlink()
    free = shutil.disk_usage(str(mount)).free
    assert 0 < free < 2 * 1024**2, free
    print("NTFS reported disk full; diagnostic headroom: {0} bytes".format(free))
    return filler


@pytest.mark.parametrize("phase", ["backup", "apply"])
def test_actual_disk_full_preserves_or_recovers_previous_installation(tmp_path, small_volume, phase):
    source = tmp_path / "source"
    destination = small_volume / "installation"
    for root in (source, destination):
        (root / "runtime").mkdir(parents=True)
    (source / "README.md").write_text("new")
    (source / "runtime" / "python311.dll").write_bytes(b"N" * (16 * 1024**2))
    (destination / "README.md").write_text("old")
    old_dll = b"O" * (4 * 1024**2)
    (destination / "runtime" / "python311.dll").write_bytes(old_dll)
    old_manifest = standalone_update.package_manifest(str(destination))
    (destination / "standalone-manifest.json").write_text(json.dumps(old_manifest))
    (destination / "user_notes.txt").write_text("keep")
    (source / "standalone-manifest.json").write_text(json.dumps(
        standalone_update.package_manifest(str(source))))
    standalone_update._prepare_apply_plan(str(source), str(destination), "2.0.0")
    paused, resume = tmp_path / "paused", tmp_path / "resume"
    injection = None
    if phase == "apply":
        injection = (
            '        if ($entry.path -eq "runtime/python311.dll") { '
            '[IO.File]::WriteAllText(%s, "paused"); '
            'while (-not [IO.File]::Exists(%s)) { [Threading.Thread]::Sleep(20) } }'
        ) % ("'" + str(paused).replace("'", "''") + "'",
             "'" + str(resume).replace("'", "''") + "'")
    script = script_path(tmp_path, injection)
    process = None
    filler = None
    transaction = destination / standalone_update.PORTABLE_TRANSACTION_DIRECTORY
    try:
        if phase == "backup":
            filler = exhaust_volume(small_volume)
        process = subprocess.Popen(command(script, destination),
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if phase == "apply":
            deadline = time.monotonic() + 30
            while not paused.exists() and process.poll() is None and time.monotonic() < deadline:
                time.sleep(0.02)
            assert paused.exists(), "Helper did not reach the partial-apply barrier"
            assert (destination / "README.md").read_text() == "new"
            assert (transaction / "backup" / "runtime" / "python311.dll").read_bytes() == old_dll
            filler = exhaust_volume(small_volume)
            resume.write_text("continue")
        output, error = process.communicate(timeout=45)
        assert process.returncode == 1, (output, error)
        assert b"not enough space" in error.lower() or b"disk full" in error.lower(), error
        status = json.loads((destination / "standalone-update-status.json").read_text())
        assert status["state"] in ("failed", "recovery_required"), status
        assert (destination / "user_notes.txt").read_text() == "keep"
        if transaction.exists():
            assert phase == "apply"
            assert (transaction / "journal.json").exists()
            assert (transaction / "backup" / "runtime" / "python311.dll").read_bytes() == old_dll
        filler.unlink()
        filler = None
        if transaction.exists():
            result = subprocess.run(command(script_path(tmp_path), destination, recover=True),
                                    capture_output=True, timeout=45)
            assert result.returncode == 0, (result.stdout, result.stderr)
        assert not transaction.exists()
        assert (destination / "README.md").read_text() == "old"
        assert (destination / "runtime" / "python311.dll").read_bytes() == old_dll
        assert json.loads((destination / "standalone-manifest.json").read_text()) == old_manifest
        assert (destination / "user_notes.txt").read_text() == "keep"
        assert not list(destination.rglob("*.stb-update-tmp"))
    finally:
        if process is not None and process.poll() is None:
            process.kill()
            process.communicate(timeout=10)
        if filler is not None and filler.exists():
            filler.unlink()
