# -*- coding: utf-8 -*-
from __future__ import print_function

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import zipfile

try:
    from urllib2 import HTTPError
    from urllib2 import Request
    from urllib2 import URLError
    from urllib2 import urlopen
except ImportError:
    from urllib.error import HTTPError
    from urllib.error import URLError
    from urllib.request import Request
    from urllib.request import urlopen

from ..constants import GITHUB_REPOSITORY
from ..constants import GITHUB_TOKEN_ENV
from ..constants import PLUGIN_VERSION
from ..pycompat import text_type


USER_AGENT = "Script-Toolbox-Updater/{0}".format(
    PLUGIN_VERSION
)


class UpdateError(RuntimeError):
    pass


def _version_parts(value):
    value = text_type(
        value or ""
    ).strip()

    if value.lower().startswith("v"):
        value = value[1:]

    main, separator, prerelease = value.partition("-")
    numbers = main.split(".")
    parsed = []

    for entry in numbers[:3]:
        digits = ""

        for character in entry:
            if character.isdigit():
                digits += character
            else:
                break

        parsed.append(
            int(digits or 0)
        )

    while len(parsed) < 3:
        parsed.append(
            0
        )

    # Stable release is newer than a prerelease with the same numeric version.
    stable_rank = 1 if not separator else 0

    return (
        parsed[0],
        parsed[1],
        parsed[2],
        stable_rank,
        prerelease.lower()
    )


def is_newer_version(
    candidate,
    current=PLUGIN_VERSION
):
    return _version_parts(
        candidate
    ) > _version_parts(
        current
    )


def _github_token(token=None):
    if token:
        return text_type(
            token
        ).strip()

    return text_type(
        os.environ.get(
            GITHUB_TOKEN_ENV,
            ""
        )
    ).strip()


def _is_windows():
    return os.name == "nt"


def _powershell_executable():
    if not _is_windows():
        return None

    candidates = [
        os.path.join(
            os.environ.get(
                "SystemRoot",
                r"C:\Windows"
            ),
            "System32",
            "WindowsPowerShell",
            "v1.0",
            "powershell.exe"
        ),
        "powershell.exe",
    ]

    for candidate in candidates:
        if os.path.isfile(
            candidate
        ):
            return candidate

        if candidate == "powershell.exe":
            return candidate

    return None


def _powershell_quote(
    value
):
    return text_type(
        value or ""
    ).replace(
        "'",
        "''"
    )


def _download_with_powershell(
    url,
    destination,
    token=None,
    timeout=30,
    accept="application/octet-stream"
):
    executable = _powershell_executable()

    if not executable:
        raise UpdateError(
            "PowerShell fallback is not available."
        )

    timeout_ms = max(
        1000,
        int(
            float(timeout) *
            1000.0
        )
    )

    token = _github_token(
        token
    )

    script = [
        "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12",
        "$request = [System.Net.HttpWebRequest]::Create('{0}')".format(
            _powershell_quote(
                url
            )
        ),
        "$request.UserAgent = '{0}'".format(
            _powershell_quote(
                USER_AGENT
            )
        ),
        "$request.Accept = '{0}'".format(
            _powershell_quote(
                accept
            )
        ),
        "$request.Timeout = {0}".format(
            timeout_ms
        ),
        "$request.ReadWriteTimeout = {0}".format(
            timeout_ms
        ),
    ]

    if token:
        script.append(
            "$request.Headers['Authorization'] = 'token {0}'".format(
                _powershell_quote(
                    token
                )
            )
        )

    script.extend([
        "$response = $request.GetResponse()",
        "$input = $response.GetResponseStream()",
        "$output = [System.IO.File]::Open('{0}', [System.IO.FileMode]::Create)".format(
            _powershell_quote(
                destination
            )
        ),
        "try { $input.CopyTo($output) } finally { $output.Close(); $input.Close(); $response.Close() }",
    ])

    command = "; ".join(
        script
    )

    process = subprocess.Popen(
        [
            executable,
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            command,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    stdout_value, stderr_value = process.communicate()

    if process.returncode != 0:
        try:
            error_text = stderr_value.decode(
                "utf-8",
                "replace"
            )
        except Exception:
            error_text = text_type(
                stderr_value
            )

        raise UpdateError(
            "PowerShell download failed: {0}".format(
                error_text.strip() or
                "exit code {0}".format(
                    process.returncode
                )
            )
        )

    if not os.path.isfile(
        destination
    ):
        raise UpdateError(
            "PowerShell download did not create the destination file."
        )

    return destination


def _request(
    url,
    token=None,
    timeout=8,
    accept="application/vnd.github+json"
):
    headers = {
        "Accept": accept,
        "User-Agent": USER_AGENT,
    }

    token = _github_token(
        token
    )

    if token:
        headers[
            "Authorization"
        ] = "token {0}".format(
            token
        )

    request = Request(
        url,
        headers=headers
    )

    return urlopen(
        request,
        timeout=timeout
    )


def _read_json(
    url,
    token=None,
    timeout=8
):
    urllib_error = None

    try:
        response = _request(
            url,
            token=token,
            timeout=timeout,
            accept="application/vnd.github+json"
        )

        try:
            payload = response.read()
        finally:
            try:
                response.close()
            except Exception:
                pass

    except Exception as exc:
        urllib_error = exc

        if not _is_windows():
            raise

        temp_directory = tempfile.mkdtemp(
            prefix="script_toolbox_http_"
        )
        temp_path = os.path.join(
            temp_directory,
            "response.json"
        )

        try:
            _download_with_powershell(
                url,
                temp_path,
                token=token,
                timeout=timeout,
                accept="application/vnd.github+json"
            )

            with open(
                temp_path,
                "rb"
            ) as handle:
                payload = handle.read()

        except Exception as fallback_exc:
            raise UpdateError(
                "GitHub request failed with Python urllib ({0}); "
                "PowerShell TLS fallback also failed ({1}).".format(
                    text_type(
                        urllib_error
                    ),
                    text_type(
                        fallback_exc
                    )
                )
            )

        finally:
            try:
                shutil.rmtree(
                    temp_directory
                )
            except Exception:
                pass

    if not isinstance(
        payload,
        text_type
    ):
        payload = payload.decode(
            "utf-8"
        )

    return json.loads(
        payload
    )


def latest_release(
    repository=GITHUB_REPOSITORY,
    token=None,
    timeout=8
):
    url = (
        "https://api.github.com/repos/"
        "{0}/releases/latest"
    ).format(
        repository
    )

    data = _read_json(
        url,
        token=token,
        timeout=timeout
    )

    tag = text_type(
        data.get(
            "tag_name",
            ""
        )
    ).strip()

    if not tag:
        raise UpdateError(
            "Latest GitHub release has no tag."
        )

    version = (
        tag[1:]
        if tag.lower().startswith("v")
        else tag
    )

    package_asset_name = (
        "script-toolbox-{0}.zip"
    ).format(
        version
    )
    checksum_asset_name = (
        package_asset_name +
        ".sha256"
    )

    package_asset = None
    checksum_asset = None

    for asset in data.get(
        "assets",
        []
    ) or []:
        name = text_type(
            asset.get(
                "name",
                ""
            )
        )

        if name == package_asset_name:
            package_asset = asset

        elif name == checksum_asset_name:
            checksum_asset = asset

    # Prefer our packaged release asset. Fall back to GitHub's source archive
    # so older releases remain installable.
    download_url = text_type(
        (
            package_asset or {}
        ).get(
            "browser_download_url",
            ""
        ) or
        (
            package_asset or {}
        ).get(
            "url",
            ""
        ) or
        data.get(
            "zipball_url",
            ""
        )
    )

    checksum_url = text_type(
        (
            checksum_asset or {}
        ).get(
            "browser_download_url",
            ""
        ) or
        (
            checksum_asset or {}
        ).get(
            "url",
            ""
        )
    )

    return {
        "tag": tag,
        "version": version,
        "name": text_type(
            data.get(
                "name",
                ""
            )
        ),
        "release_url": text_type(
            data.get(
                "html_url",
                ""
            )
        ),
        "download_url": download_url,
        "checksum_url": checksum_url,
        "asset_name": (
            package_asset_name
            if package_asset is not None
            else ""
        ),
        "published_at": text_type(
            data.get(
                "published_at",
                ""
            )
        ),
        "body": text_type(
            data.get(
                "body",
                ""
            )
        ),
    }



def check_for_update(
    current_version=PLUGIN_VERSION,
    repository=GITHUB_REPOSITORY,
    token=None,
    timeout=8
):
    result = {
        "available": False,
        "current_version": current_version,
        "latest_version": None,
        "release": None,
        "error": None,
    }

    try:
        release = latest_release(
            repository=repository,
            token=token,
            timeout=timeout
        )

        result[
            "release"
        ] = release
        result[
            "latest_version"
        ] = release[
            "version"
        ]
        result[
            "available"
        ] = is_newer_version(
            release["version"],
            current=current_version
        )

    except HTTPError as exc:
        # GitHub returns 404 for a private repository without credentials and
        # also when the repository has no releases yet.
        result["error"] = (
            "GitHub HTTP {0}".format(
                getattr(
                    exc,
                    "code",
                    "error"
                )
            )
        )
    except URLError as exc:
        result["error"] = text_type(
            exc
        )
    except Exception as exc:
        result["error"] = text_type(
            exc
        )

    return result


def package_directory():
    return os.path.normpath(
        os.path.dirname(
            os.path.dirname(
                os.path.abspath(
                    __file__
                )
            )
        )
    )


def repository_root():
    return os.path.normpath(
        os.path.dirname(
            os.path.dirname(
                package_directory()
            )
        )
    )


def _download_file(
    url,
    destination,
    token=None,
    timeout=30
):
    try:
        response = _request(
            url,
            token=token,
            timeout=timeout,
            accept="application/octet-stream"
        )

        try:
            with open(
                destination,
                "wb"
            ) as handle:
                while True:
                    chunk = response.read(
                        1024 * 256
                    )

                    if not chunk:
                        break

                    handle.write(
                        chunk
                    )
        finally:
            try:
                response.close()
            except Exception:
                pass

        return destination

    except Exception as urllib_error:
        if not _is_windows():
            raise

        try:
            return _download_with_powershell(
                url,
                destination,
                token=token,
                timeout=timeout,
                accept="application/octet-stream"
            )
        except Exception as fallback_exc:
            raise UpdateError(
                "Download failed with Python urllib ({0}); "
                "PowerShell TLS fallback also failed ({1}).".format(
                    text_type(
                        urllib_error
                    ),
                    text_type(
                        fallback_exc
                    )
                )
            )


def _sha256_file(
    path
):
    digest = hashlib.sha256()

    with open(
        path,
        "rb"
    ) as handle:
        while True:
            chunk = handle.read(
                1024 * 256
            )

            if not chunk:
                break

            digest.update(
                chunk
            )

    return digest.hexdigest()


def _read_checksum(
    path
):
    with open(
        path,
        "rb"
    ) as handle:
        value = handle.read()

    if not isinstance(
        value,
        text_type
    ):
        value = value.decode(
            "utf-8"
        )

    value = value.strip()

    if not value:
        raise UpdateError(
            "Release checksum file is empty."
        )

    checksum = value.split()[0].strip().lower()

    if (
        len(checksum) != 64 or
        any(
            character not in "0123456789abcdef"
            for character in checksum
        )
    ):
        raise UpdateError(
            "Release checksum has an invalid SHA-256 value."
        )

    return checksum


def _verify_checksum(
    archive_path,
    checksum_path
):
    expected = _read_checksum(
        checksum_path
    )
    actual = _sha256_file(
        archive_path
    )

    if actual.lower() != expected.lower():
        raise UpdateError(
            "Release checksum verification failed."
        )

    return True


def _safe_extract(
    archive,
    destination
):
    destination_abs = os.path.abspath(
        destination
    )

    for member in archive.infolist():
        member_path = os.path.abspath(
            os.path.join(
                destination,
                member.filename
            )
        )

        if not (
            member_path == destination_abs or
            member_path.startswith(
                destination_abs +
                os.sep
            )
        ):
            raise UpdateError(
                "Unsafe path in update archive."
            )

    archive.extractall(
        destination
    )


def _find_release_root(
    extracted_directory
):
    for name in os.listdir(
        extracted_directory
    ):
        candidate = os.path.join(
            extracted_directory,
            name
        )

        package_init = os.path.join(
            candidate,
            "scripts",
            "script_toolbox",
            "__init__.py"
        )

        if (
            os.path.isdir(candidate) and
            os.path.isfile(package_init)
        ):
            return candidate

    raise UpdateError(
        "The release archive does not contain scripts/script_toolbox."
    )


def install_release(
    release,
    token=None,
    timeout=30
):
    if not isinstance(
        release,
        dict
    ):
        raise UpdateError(
            "Invalid release metadata."
        )

    download_url = text_type(
        release.get(
            "download_url",
            ""
        )
    ).strip()

    if not download_url:
        raise UpdateError(
            "The release has no download URL."
        )

    destination_package = package_directory()
    destination_root = repository_root()

    if not os.path.isdir(
        destination_package
    ):
        raise UpdateError(
            "Cannot find the installed Script Toolbox package."
        )

    work_directory = tempfile.mkdtemp(
        prefix="script_toolbox_update_"
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

    backup_path = (
        destination_package +
        ".update_backup"
    )

    try:
        _download_file(
            download_url,
            archive_path,
            token=token,
            timeout=timeout
        )

        checksum_url = text_type(
            release.get(
                "checksum_url",
                ""
            )
        ).strip()

        if checksum_url:
            _download_file(
                checksum_url,
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
        source_package = os.path.join(
            source_root,
            "scripts",
            "script_toolbox"
        )

        if os.path.exists(
            backup_path
        ):
            shutil.rmtree(
                backup_path
            )

        os.rename(
            destination_package,
            backup_path
        )

        try:
            shutil.copytree(
                source_package,
                destination_package
            )

            source_mod = os.path.join(
                source_root,
                "MayaScriptToolbox.mod"
            )

            if os.path.isfile(
                source_mod
            ):
                shutil.copy2(
                    source_mod,
                    os.path.join(
                        destination_root,
                        "MayaScriptToolbox.mod"
                    )
                )

        except Exception:
            if os.path.isdir(
                destination_package
            ):
                shutil.rmtree(
                    destination_package
                )

            os.rename(
                backup_path,
                destination_package
            )
            raise

        if os.path.isdir(
            backup_path
        ):
            shutil.rmtree(
                backup_path
            )

        return {
            "installed": True,
            "version": release.get(
                "version"
            ),
            "restart_required": True,
        }

    except Exception as exc:
        if isinstance(
            exc,
            UpdateError
        ):
            raise

        raise UpdateError(
            text_type(
                exc
            )
        )

    finally:
        try:
            shutil.rmtree(
                work_directory
            )
        except Exception:
            pass


__all__ = [
    "UpdateError",
    "check_for_update",
    "install_release",
    "is_newer_version",
    "latest_release",
    "package_directory",
    "_download_with_powershell",
    "_powershell_executable",
    "_read_checksum",
    "_sha256_file",
    "_verify_checksum",
    "repository_root",
]
