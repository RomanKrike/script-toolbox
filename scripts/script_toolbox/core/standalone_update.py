# -*- coding: utf-8 -*-
from __future__ import print_function

import json
import hashlib
import os
import shutil
import subprocess
import tempfile
import zipfile

from ..pycompat import text_type
from .file_lock import installation_lock, FileLockError
from .config import _replace_file
from . import http_transport
from .update_package import UpdateError
from .update_package import download_file as _download_file
from .update_package import find_release_root as _find_release_root
from .update_package import safe_extract as _safe_extract
from .update_package import validate_installable_release as _validate_installable_release
from .update_package import verify_checksum as _verify_checksum
from .updater import repository_root


_REQUIRED_PORTABLE_PATHS = (
    "ScriptToolbox.exe",
    os.path.join(
        "standalone",
        "bootstrap.py"
    ),
    os.path.join(
        "scripts",
        "script_toolbox",
        "__init__.py"
    ),
)


def _validate_portable_root(
    root,
    require_marker=True
):
    root = os.path.abspath(
        root
    )

    required_paths = list(
        _REQUIRED_PORTABLE_PATHS
    )
    if require_marker:
        required_paths.append(
            "standalone-build.json"
        )

    for relative_path in required_paths:
        path = os.path.join(
            root,
            relative_path
        )
        if not os.path.isfile(path):
            raise UpdateError(
                "Standalone package is missing required file: {0}".format(
                    relative_path.replace(
                        os.sep,
                        "/"
                    )
                )
            )

    runtime = os.path.join(
        root,
        "runtime"
    )
    if not os.path.isdir(runtime):
        raise UpdateError(
            "Standalone package is missing the portable runtime."
        )

    versioned_dll = False
    for filename in os.listdir(runtime):
        lower = filename.lower()
        if (
            lower.startswith("python3") and
            lower.endswith(".dll") and
            lower != "python3.dll"
        ):
            versioned_dll = True
            break

    if not versioned_dll:
        raise UpdateError(
            "Standalone package is missing the versioned Python runtime DLL."
        )

    return True


def _read_build_marker(root):
    path = os.path.join(
        root,
        "standalone-build.json"
    )

    try:
        with open(path, "rb") as handle:
            payload = handle.read()

        if not isinstance(payload, text_type):
            payload = payload.decode(
                "utf-8"
            )

        data = json.loads(
            payload
        )
    except Exception as exc:
        raise UpdateError(
            "Standalone build marker is unreadable: {0}".format(
                text_type(exc)
            )
        )

    if not isinstance(data, dict):
        raise UpdateError(
            "Standalone build marker has an invalid format."
        )

    return data


def render_apply_script():
    return r"""param(
    [int]$ParentProcessId = 0,
    [string]$Source,
    [string]$Destination,
    [string]$CleanupRoot,
    [switch]$RecoverOnly
)
$ErrorActionPreference = "Stop"
$transaction = Join-Path $Destination ".script_toolbox_portable_update"
$planPath = Join-Path $transaction "plan.json"
$journalPath = Join-Path $transaction "journal.json"
$statusPath = Join-Path $Destination "standalone-update-status.json"
$lock = $null
$ownsLock = $false

function Write-JsonAtomic($path, $value) {
    $temporary = $path + ".tmp"
    $bytes = [Text.Encoding]::UTF8.GetBytes(($value | ConvertTo-Json -Depth 12))
    $stream = [IO.FileStream]::new($temporary, [IO.FileMode]::Create, [IO.FileAccess]::Write, [IO.FileShare]::None)
    try { $stream.Write($bytes, 0, $bytes.Length); $stream.Flush($true) } finally { $stream.Dispose() }
    if ([IO.File]::Exists($path)) { [IO.File]::Replace($temporary, $path, [NullString]::Value) }
    else { [IO.File]::Move($temporary, $path) }
}
function Safe-Path($root, $relative) {
    if ([IO.Path]::IsPathRooted($relative) -or $relative -match '(^|[\\/])\.\.([\\/]|$)') {
        throw "Unsafe package path: $relative"
    }
    $full = [IO.Path]::GetFullPath((Join-Path $root $relative))
    $prefix = [IO.Path]::GetFullPath($root).TrimEnd('\') + '\'
    if (-not $full.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) { throw "Path escapes root" }
    # Reject junctions/symlinks in both existing and future target paths.
    $cursor = $full
    while ($cursor.Length -ge $prefix.Length) {
        if (Test-Path -LiteralPath $cursor) {
            if ((Get-Item -LiteralPath $cursor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Reparse point: $cursor" }
        }
        $cursor = [IO.Path]::GetDirectoryName($cursor)
    }
    return $full
}
function Copy-Atomic($sourcePath, $targetPath) {
    [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($targetPath)) | Out-Null
    $temporary = $targetPath + ".stb-update-tmp"
    [IO.File]::Copy($sourcePath, $temporary, $true)
    if ([IO.File]::Exists($targetPath)) { [IO.File]::Replace($temporary, $targetPath, [NullString]::Value) }
    else { [IO.File]::Move($temporary, $targetPath) }
}
function File-Sha256($path) {
    $stream = [IO.File]::OpenRead($path)
    $hash = [Security.Cryptography.SHA256]::Create()
    try { return [BitConverter]::ToString($hash.ComputeHash($stream)).Replace('-', '').ToLowerInvariant() }
    finally { $hash.Dispose(); $stream.Dispose() }
}
function Restore-Previous($plan, $journal) {
    foreach ($entry in $plan.entries) {
        $target = Safe-Path $Destination $entry.path
        if ($entry.existed) {
            $saved = Safe-Path (Join-Path $transaction "backup") $entry.path
            Copy-Atomic $saved $target
        } elseif ([IO.File]::Exists($target)) { [IO.File]::Delete($target) }
        $temporary = $target + ".stb-update-tmp"
        if ([IO.File]::Exists($temporary)) { [IO.File]::Delete($temporary) }
    }
}
function Restart-Portable($state, $version) {
    $exe = Join-Path $Destination "ScriptToolbox.exe"
    $ackPath = Join-Path $Destination ".script_toolbox_restart_ack"
    try {
        $marker = Get-Content -LiteralPath (Join-Path $Destination "standalone-build.json") -Raw | ConvertFrom-Json
        $handshake = ($marker.restart_handshake_version -eq 1)
    } catch {
        Write-JsonAtomic $statusPath @{state=$state; version=$version; restart="failed"; message=$_.Exception.Message}
        return $false
    }
    $failure = "Restart did not complete."
    for ($attempt = 0; $attempt -lt 3; $attempt++) {
        $process = $null
        try {
            if ([IO.File]::Exists($ackPath)) { [IO.File]::Delete($ackPath) }
            $token = [Guid]::NewGuid().ToString("N")
            $start = [Diagnostics.ProcessStartInfo]::new()
            $start.FileName = $exe
            $start.WorkingDirectory = $Destination
            $start.UseShellExecute = $false
            $start.EnvironmentVariables["SCRIPT_TOOLBOX_RESTART_TOKEN"] = $token
            $start.EnvironmentVariables.Remove("PYTHONHOME")
            $start.EnvironmentVariables.Remove("PYTHONPATH")
            $process = [Diagnostics.Process]::Start($start)
            $deadline = [DateTime]::UtcNow.AddSeconds(30)
            $legacyReady = [DateTime]::UtcNow.AddSeconds(2)
            while (-not $process.HasExited -and [DateTime]::UtcNow -lt $deadline) {
                $ready = $false
                if ($handshake -and [IO.File]::Exists($ackPath)) {
                    $ready = ([IO.File]::ReadAllText($ackPath) -eq $token)
                } elseif (-not $handshake -and [DateTime]::UtcNow -gt $legacyReady) { $ready = $true }
                if ($ready) {
                    Write-JsonAtomic $statusPath @{state=$state; version=$version; restart="started"; restart_pid=$process.Id}
                    return $true
                }
                [Threading.Thread]::Sleep(100)
            }
            if (-not $process.HasExited) {
                # Avoid launching a duplicate when startup is merely slow.
                $failure = "Application startup acknowledgement timed out. Check the running process or start ScriptToolbox.exe manually."
                break
            }
            $failure = "Restarted application exited with code " + $process.ExitCode
        } catch {
            $failure = $_.Exception.Message
            if ($process -and -not $process.HasExited) { break }
        }
        [Threading.Thread]::Sleep(500)
    }
    # Restart failure is separate from the already committed installation.
    Write-JsonAtomic $statusPath @{state=$state; version=$version; restart="failed"; message=$failure}
    [Console]::Error.WriteLine($failure)
    return $false
}
try {
    $lockPath = Join-Path $Destination ".script_toolbox_update.lock"
    $lock = [IO.FileStream]::new($lockPath, [IO.FileMode]::OpenOrCreate, [IO.FileAccess]::ReadWrite, [IO.FileShare]::ReadWrite)
    # Byte lock is shared with Python msvcrt.locking; ownership dies on crash.
    $deadline = [DateTime]::UtcNow.AddSeconds(10)
    while (-not $ownsLock) {
        try { $lock.Lock(0, 1); $ownsLock = $true }
        catch { if ([DateTime]::UtcNow -gt $deadline) { throw }; Start-Sleep -Milliseconds 100 }
    }
    if ($ParentProcessId -gt 0) { Wait-Process -Id $ParentProcessId -ErrorAction SilentlyContinue }
    $plan = Get-Content -LiteralPath $planPath -Raw | ConvertFrom-Json
    if ($RecoverOnly) {
        if (Test-Path -LiteralPath $journalPath) {
            $journal = Get-Content -LiteralPath $journalPath -Raw | ConvertFrom-Json
            if ($journal.phase -ne "committed") { Restore-Previous $plan $journal }
            Write-JsonAtomic $statusPath @{state="recovered"; message="Interrupted portable update recovered."}
        } else {
            Write-JsonAtomic $statusPath @{state="cancelled"; message="Staged update was not applied."}
        }
        Remove-Item -LiteralPath $transaction -Recurse -Force
        $lock.Dispose(); $lock = $null
        if (-not (Restart-Portable "recovered" $plan.version)) { exit 2 }
        exit 0
    }
    $Source = $plan.source
    # Copy every previous file before journalling or touching the installation.
    foreach ($entry in $plan.entries) {
        if ($entry.existed) {
            Copy-Atomic (Safe-Path $Destination $entry.path) (Safe-Path (Join-Path $transaction "backup") $entry.path)
        }
        if ($entry.sha256) {
            $actual = File-Sha256 (Safe-Path $Source $entry.path)
            if ($actual -ne $entry.sha256) { throw "Staged checksum mismatch: $($entry.path)" }
        }
    }
    Write-JsonAtomic $journalPath @{phase="applying"}
    foreach ($entry in $plan.entries) {
        $target = Safe-Path $Destination $entry.path
        if ($entry.sha256) { Copy-Atomic (Safe-Path $Source $entry.path) $target }
        elseif ([IO.File]::Exists($target)) { [IO.File]::Delete($target) }
    }
    foreach ($entry in $plan.entries) {
        if ($entry.sha256) {
            if ((File-Sha256 (Safe-Path $Destination $entry.path)) -ne $entry.sha256) { throw "Installed checksum mismatch" }
        }
    }
    Write-JsonAtomic $journalPath @{phase="committed"}
    Write-JsonAtomic $statusPath @{state="installed"; version=$plan.version}
    Remove-Item -LiteralPath $transaction -Recurse -Force
    $lock.Dispose(); $lock = $null
    if (-not (Restart-Portable "installed" $plan.version)) { exit 2 }
    Remove-Item -LiteralPath $CleanupRoot -Recurse -Force -ErrorAction SilentlyContinue
    exit 0
} catch {
    $failure = $_.Exception.Message
    [Console]::Error.WriteLine($failure)
    if ($ownsLock -and (Test-Path -LiteralPath $journalPath)) {
        try {
            $journal = Get-Content -LiteralPath $journalPath -Raw | ConvertFrom-Json
            if ($journal.phase -ne "committed") { Restore-Previous $plan $journal }
            Write-JsonAtomic $statusPath @{state="failed"; message=$failure; rollback="complete"}
            Remove-Item -LiteralPath $transaction -Recurse -Force
        } catch {
            Write-JsonAtomic $statusPath @{state="recovery_required"; message=$failure; rollback=$_.Exception.Message}
        }
    } elseif ($ownsLock) {
        Write-JsonAtomic $statusPath @{state="failed"; message=$failure; rollback="not_needed"}
        Remove-Item -LiteralPath $transaction -Recurse -Force -ErrorAction SilentlyContinue
    }
    exit 1
} finally { if ($lock) { $lock.Dispose() } }
"""


def _write_apply_script(work_directory):
    path = os.path.join(
        work_directory,
        "apply-standalone-update.ps1"
    )
    with open(path, "wb") as handle:
        handle.write(
            render_apply_script().encode(
                "utf-8"
            )
        )
    return path


def _launch_apply_helper(
    script_path,
    source_root,
    destination_root,
    cleanup_root
):
    if os.name != "nt":
        raise UpdateError(
            "Standalone package replacement is only supported on Windows."
        )

    powershell = http_transport.powershell_executable()
    if not powershell:
        raise UpdateError(
            "Windows PowerShell is required to apply the standalone update."
        )

    command = [
        powershell,
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-WindowStyle",
        "Hidden",
        "-File",
        script_path,
        "-ParentProcessId",
        text_type(
            os.getpid()
        ),
        "-Source",
        source_root,
        "-Destination",
        destination_root,
        "-CleanupRoot",
        cleanup_root,
    ]

    kwargs = http_transport.hidden_process_kwargs()
    kwargs["cwd"] = destination_root

    try:
        process = subprocess.Popen(
            command,
            **kwargs
        )
    except Exception as exc:
        raise UpdateError(
            "Could not start the standalone update helper: {0}".format(
                text_type(exc)
            )
        )

    return process.pid


PORTABLE_TRANSACTION_DIRECTORY = ".script_toolbox_portable_update"
MANIFEST_FILENAME = "standalone-manifest.json"


def package_manifest(root):
    result = {}
    for folder, directories, files in os.walk(root):
        directories[:] = [name for name in directories if name != "__pycache__"]
        for name in files:
            relative = os.path.relpath(os.path.join(folder, name), root).replace(os.sep, "/")
            if relative == MANIFEST_FILENAME or relative.endswith((".pyc", ".pyo")):
                continue
            with open(os.path.join(folder, name), "rb") as handle:
                result[relative] = hashlib.sha256(handle.read()).hexdigest()
    return result


def _safe_manifest(root):
    path = os.path.join(root, MANIFEST_FILENAME)
    if not os.path.isfile(path):
        return {}
    with open(path, "rb") as handle:
        data = json.loads(handle.read().decode("utf-8"))
    if not isinstance(data, dict):
        raise UpdateError("Invalid portable manifest.")
    for relative in data:
        # The manifest may own package files, never transaction/user paths.
        parts = relative.replace("\\", "/").split("/")
        if (not relative or relative.startswith(("/", "\\")) or
                ":" in relative or ".." in parts or "." in parts or
                parts[0] not in ("runtime", "scripts", "standalone", "docs", "nuke", "houdini",
                    "ScriptToolbox.exe", "MayaScriptToolbox.mod", "README.md", "standalone-build.json")):
            raise UpdateError("Unsafe portable manifest path: " + relative)
    return data


def _prepare_apply_plan(source, destination, version):
    new_files = package_manifest(source)
    old_files = _safe_manifest(destination)
    declared = _safe_manifest(source)
    if not declared or declared != new_files:
        raise UpdateError("Portable update needs a complete, verified file manifest.")
    new_files[MANIFEST_FILENAME] = hashlib.sha256(
        open(os.path.join(source, MANIFEST_FILENAME), "rb").read()).hexdigest()
    entries = [{"path": relative, "sha256": new_files.get(relative),
                "existed": os.path.isfile(os.path.join(destination, relative))}
               for relative in sorted(set(new_files) | set(old_files))]
    transaction = os.path.join(destination, PORTABLE_TRANSACTION_DIRECTORY)
    if os.path.exists(transaction):
        raise UpdateError("A portable update is pending. Restart to recover it first.")
    os.makedirs(transaction)
    try:
        with open(os.path.join(transaction, "plan.json"), "w") as handle:
            json.dump({"source": source, "version": version, "entries": entries}, handle)
            handle.flush()
            os.fsync(handle.fileno())
        recovery = os.path.join(destination, ".script_toolbox_recover.ps1")
        temporary = recovery + ".tmp"
        with open(temporary, "wb") as handle:
            handle.write(render_apply_script().encode("utf-8"))
        _replace_file(temporary, recovery)
    except Exception:
        shutil.rmtree(transaction)
        raise
    return transaction


def install_release(release, token=None, timeout=30):
    try:
        with installation_lock(repository_root()):
            return _install_release_locked(release, token=token, timeout=timeout)
    except FileLockError as exc:
        raise UpdateError("An update is already running: {0}".format(exc))


def _install_release_locked(
    release,
    token=None,
    timeout=30
):
    """Stage a verified portable build and replace it after this process exits."""
    install_metadata = _validate_installable_release(
        release
    )

    if install_metadata.get(
        "package_kind"
    ) != "standalone":
        raise UpdateError(
            "Standalone updater received a non-standalone package."
        )

    destination_root = repository_root()
    _validate_portable_root(
        destination_root,
        require_marker=False
    )

    if _read_build_marker(destination_root).get("portable_transaction_version") != 1:
        raise UpdateError("This portable launcher cannot recover interrupted updates. "
                          "Install this recovery-capable portable build manually once.")

    work_directory = tempfile.mkdtemp(
        prefix="sbt_u_"
    )
    archive_path = os.path.join(
        work_directory,
        "release.zip"
    )
    checksum_path = os.path.join(
        work_directory,
        "release.zip.sha256"
    )
    extracted_path = os.path.join(
        work_directory,
        "x"
    )

    scheduled = False
    transaction_path = None

    try:
        _download_file(
            install_metadata[
                "download_url"
            ],
            archive_path,
            token=token,
            timeout=timeout
        )
        _download_file(
            install_metadata[
                "checksum_url"
            ],
            checksum_path,
            token=token,
            timeout=timeout
        )
        _verify_checksum(
            archive_path,
            checksum_path
        )

        os.makedirs(
            extracted_path
        )

        archive = zipfile.ZipFile(
            archive_path,
            "r"
        )
        try:
            _safe_extract(
                archive,
                extracted_path
            )
        finally:
            archive.close()

        source_root = _find_release_root(
            extracted_path
        )
        _validate_portable_root(
            source_root
        )

        marker = _read_build_marker(
            source_root
        )
        marker_version = text_type(
            marker.get(
                "version",
                ""
            )
        ).strip()
        expected_version = text_type(
            install_metadata[
                "version"
            ]
        ).strip()

        if marker_version != expected_version:
            raise UpdateError(
                (
                    "Standalone package version mismatch: expected {0}, "
                    "got {1}."
                ).format(
                    expected_version,
                    marker_version or "<missing>"
                )
            )

        transaction_path = _prepare_apply_plan(source_root, destination_root, marker_version)
        script_path = _write_apply_script(
            work_directory
        )
        helper_pid = _launch_apply_helper(
            script_path,
            source_root,
            destination_root,
            work_directory
        )
        scheduled = True

        return {
            "installed": False,
            "staged": True,
            "version": install_metadata[
                "version"
            ],
            "restart_required": True,
            "hot_reload_supported": False,
            "external_restart_scheduled": True,
            "helper_pid": helper_pid,
            "package_kind": "standalone",
        }

    except Exception as exc:
        if isinstance(
            exc,
            UpdateError
        ):
            raise
        raise UpdateError(
            text_type(exc)
        )

    finally:
        if not scheduled:
            if transaction_path and os.path.isdir(transaction_path):
                shutil.rmtree(transaction_path)
            try:
                shutil.rmtree(
                    work_directory
                )
            except Exception:
                pass


__all__ = [
    "install_release",
    "render_apply_script",
]
