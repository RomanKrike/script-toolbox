"""Execute the actual PowerShell transaction with injected failures."""
import ctypes
import json
import os
import subprocess
import time

import pytest

from script_toolbox.core import standalone_update

pytestmark = pytest.mark.skipif(os.name != "nt", reason="Windows filesystem/PowerShell test")


def prepare(tmp_path):
    source, destination = tmp_path / "source", tmp_path / "destination"
    source.mkdir()
    destination.mkdir()
    (source / "README.md").write_text("new")
    (source / "runtime").mkdir()
    (source / "runtime" / "python311.dll").write_bytes(b"new dll")
    (destination / "README.md").write_text("old")
    (destination / "runtime").mkdir()
    (destination / "runtime" / "python311.dll").write_bytes(b"old dll")
    (destination / "docs").mkdir()
    (destination / "docs" / "obsolete.txt").write_text("obsolete")
    (destination / "user_notes.txt").write_text("keep")
    (destination / "standalone-manifest.json").write_text(json.dumps(
        standalone_update.package_manifest(str(destination))))
    # User notes are explicitly excluded from package ownership.
    old = json.loads((destination / "standalone-manifest.json").read_text())
    old.pop("user_notes.txt")
    (destination / "standalone-manifest.json").write_text(json.dumps(old))
    (source / "standalone-manifest.json").write_text(json.dumps(standalone_update.package_manifest(str(source))))
    standalone_update._prepare_apply_plan(str(source), str(destination), "1.0.2")
    return source, destination


def script_path(tmp_path, injection=None):
    script = standalone_update.render_apply_script()
    # Suppress only the external relaunch of a native EXE in this test fixture.
    script = "\n".join(line for line in script.splitlines() if "Start-Process -FilePath" not in line)
    if injection:
        marker = '    foreach ($entry in $plan.entries) {\n        $target = Safe-Path $Destination $entry.path'
        script = script.replace(marker, marker + "\n" + injection, 1)
    path = tmp_path / "apply.ps1"
    path.write_text(script, encoding="utf-8")
    return path


def command(script, destination, recover=False):
    result = ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
              "-File", str(script), "-Destination", str(destination),
              "-CleanupRoot", str(destination.parent / "cleanup")]
    if recover:
        result.append("-RecoverOnly")
    return result


def test_apply_removes_only_manifest_files(tmp_path):
    _, destination = prepare(tmp_path)
    result = subprocess.run(command(script_path(tmp_path), destination), capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr.decode(errors="replace")
    assert (destination / "README.md").read_text() == "new"
    assert not (destination / "docs" / "obsolete.txt").exists()
    assert (destination / "user_notes.txt").read_text() == "keep"
    assert json.loads((destination / "standalone-update-status.json").read_text())["state"] == "installed"


def test_partial_apply_rolls_back(tmp_path):
    _, destination = prepare(tmp_path)
    injection = '        if ($entry.path -eq "runtime/python311.dll") { throw "injected disk-full" }'
    result = subprocess.run(command(script_path(tmp_path, injection), destination), capture_output=True, timeout=30)
    assert result.returncode == 1
    assert (destination / "README.md").read_text() == "old"
    assert (destination / "runtime" / "python311.dll").read_bytes() == b"old dll"
    assert (destination / "docs" / "obsolete.txt").read_text() == "obsolete"
    assert json.loads((destination / "standalone-update-status.json").read_text())["rollback"] == "complete"


def test_killed_helper_recovers_from_durable_journal(tmp_path):
    _, destination = prepare(tmp_path)
    signal = tmp_path / "paused"
    injection = '        if ($entry.path -eq "runtime/python311.dll") { [IO.File]::WriteAllText(%s, "paused"); Start-Sleep -Seconds 300 }' % ("'" + str(signal).replace("'", "''") + "'")
    process = subprocess.Popen(command(script_path(tmp_path, injection), destination), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        deadline = time.monotonic() + 15
        while not signal.exists() and time.monotonic() < deadline and process.poll() is None:
            time.sleep(0.05)
        assert signal.exists()
        process.kill()
        process.wait()
        result = subprocess.run(command(script_path(tmp_path), destination, recover=True), capture_output=True, timeout=30)
        assert result.returncode == 0, result.stderr.decode(errors="replace")
        assert (destination / "README.md").read_text() == "old"
        assert (destination / "docs" / "obsolete.txt").exists()
        assert not (destination / standalone_update.PORTABLE_TRANSACTION_DIRECTORY).exists()
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()


def test_locked_runtime_dll_keeps_previous_installation(tmp_path):
    _, destination = prepare(tmp_path)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.restype = ctypes.c_void_p
    kernel.CreateFileW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p,
                                  ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p]
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    handle = kernel.CreateFileW(str(destination / "runtime" / "python311.dll"),
                                0x80000000, 1, None, 3, 0, None)
    assert handle != ctypes.c_void_p(-1).value
    try:
        result = subprocess.run(command(script_path(tmp_path), destination), capture_output=True, timeout=30)
        assert result.returncode == 1
    finally:
        kernel.CloseHandle(handle)
    # A failed rollback retains the journal; recovering after unlocking is safe.
    if (destination / standalone_update.PORTABLE_TRANSACTION_DIRECTORY).exists():
        result = subprocess.run(command(script_path(tmp_path), destination, recover=True), capture_output=True, timeout=30)
        assert result.returncode == 0, result.stderr.decode(errors="replace")
    assert (destination / "README.md").read_text() == "old"
    assert (destination / "runtime" / "python311.dll").read_bytes() == b"old dll"
