# -*- coding: utf-8 -*-
from __future__ import print_function

import json
import os
import shutil
import subprocess
import tempfile
import zipfile

from ..pycompat import text_type
from . import http_transport
from .updater import UpdateError
from .updater import _download_file
from .updater import _find_release_root
from .updater import _safe_extract
from .updater import _validate_installable_release
from .updater import _verify_checksum
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
    [int]$ParentProcessId,
    [string]$Source,
    [string]$Destination,
    [string]$CleanupRoot
)

$ErrorActionPreference = "Stop"

try {
    Wait-Process -Id $ParentProcessId -ErrorAction SilentlyContinue
} catch {
}

Start-Sleep -Milliseconds 250

$robocopy = Join-Path $env:SystemRoot "System32\\robocopy.exe"
& $robocopy $Source $Destination /E /R:3 /W:1 /COPY:DAT /DCOPY:DAT /NFL /NDL /NJH /NJS /NP

$copyCode = $LASTEXITCODE
if ($copyCode -ge 8) {
    exit $copyCode
}

$exe = Join-Path $Destination "ScriptToolbox.exe"
if (-not (Test-Path -LiteralPath $exe)) {
    exit 90
}

Start-Process -FilePath $exe -WorkingDirectory $Destination
Start-Sleep -Milliseconds 500

try {
    Remove-Item -LiteralPath $CleanupRoot -Recurse -Force -ErrorAction SilentlyContinue
} catch {
}

exit 0
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


def install_release(
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

    work_directory = tempfile.mkdtemp(
        prefix="script_toolbox_standalone_update_"
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
        "extracted"
    )

    scheduled = False

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
            "installed": True,
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
