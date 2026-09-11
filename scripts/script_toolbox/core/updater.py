# -*- coding: utf-8 -*-
from __future__ import print_function

import hashlib
import json
import os

from ..constants import GITHUB_REPOSITORY
from ..constants import GITHUB_TOKEN_ENV
from ..constants import PLUGIN_VERSION
from ..pycompat import text_type
from . import http_transport


USER_AGENT = "Script-Toolbox-Updater/{0}".format(
    PLUGIN_VERSION
)


class UpdateError(RuntimeError):
    pass


def _version_parts(value):
    value = text_type(value or "").strip()
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
        parsed.append(int(digits or 0))

    while len(parsed) < 3:
        parsed.append(0)

    stable_rank = 1 if not separator else 0
    return (
        parsed[0],
        parsed[1],
        parsed[2],
        stable_rank,
        prerelease.lower()
    )


def is_newer_version(candidate, current=PLUGIN_VERSION):
    return _version_parts(candidate) > _version_parts(current)


def _github_token(token=None):
    if token:
        return text_type(token).strip()
    return text_type(
        os.environ.get(GITHUB_TOKEN_ENV, "")
    ).strip()


def _github_headers(
    token=None,
    accept="application/vnd.github+json"
):
    headers = {
        "Accept": accept,
        "User-Agent": USER_AGENT,
    }
    token = _github_token(token)
    if token:
        headers["Authorization"] = "token {0}".format(token)
    return headers


# ----------------------------------------------------------------------
# Deprecated transport compatibility wrappers
# ----------------------------------------------------------------------
# These names were exported by older Script Toolbox versions. Keep them as
# forwarding wrappers so direct imports do not break while production updater
# flow depends only on core.http_transport.


def _is_windows():
    return http_transport.is_windows()


def _hidden_process_kwargs():
    return http_transport.hidden_process_kwargs()


def _powershell_executable():
    return http_transport.powershell_executable()


def _download_with_powershell(
    url,
    destination,
    token=None,
    timeout=30,
    accept="application/octet-stream"
):
    try:
        return http_transport.powershell_download(
            url,
            destination,
            headers=_github_headers(
                token=token,
                accept=accept
            ),
            timeout=timeout
        )
    except http_transport.TransportError as exc:
        raise UpdateError(text_type(exc))


def _read_json(url, token=None, timeout=8):
    try:
        payload = http_transport.request_bytes(
            url,
            headers=_github_headers(
                token=token,
                accept="application/vnd.github+json"
            ),
            timeout=timeout
        )
    except http_transport.TransportError as exc:
        raise UpdateError(
            "GitHub request failed: {0}".format(
                text_type(exc)
            )
        )

    if not isinstance(payload, text_type):
        payload = payload.decode("utf-8")
    return json.loads(payload)


def _expected_package_asset_name(release):
    channel = text_type(
        release.get("channel", "")
    ).strip().lower()
    if channel == "development":
        return "script-toolbox-dev.zip"

    version = text_type(
        release.get("version", "")
    ).strip()
    if version.lower().startswith("v"):
        version = version[1:]
    if not version:
        return ""
    return "script-toolbox-{0}.zip".format(version)


def _validate_installable_release(release):
    """Validate metadata required by the production installer."""
    if not isinstance(release, dict):
        raise UpdateError("Invalid release metadata.")

    asset_name = text_type(
        release.get("asset_name", "")
    ).strip()
    download_url = text_type(
        release.get("download_url", "")
    ).strip()
    checksum_url = text_type(
        release.get("checksum_url", "")
    ).strip()
    expected_asset_name = _expected_package_asset_name(release)

    if not expected_asset_name:
        raise UpdateError("The release metadata has no version.")
    if not asset_name or not download_url:
        raise UpdateError(
            "The release does not contain the official Script Toolbox package."
        )
    if asset_name != expected_asset_name:
        raise UpdateError(
            "Refusing to install an unrecognized release package: {0}.".format(
                asset_name
            )
        )
    if not checksum_url:
        raise UpdateError(
            "The release package has no required SHA-256 checksum."
        )

    return {
        "asset_name": asset_name,
        "download_url": download_url,
        "checksum_url": checksum_url,
        "version": text_type(
            release.get("version", "")
        ).strip(),
    }


def latest_release(
    repository=GITHUB_REPOSITORY,
    token=None,
    timeout=8
):
    url = (
        "https://api.github.com/repos/"
        "{0}/releases/latest"
    ).format(repository)
    data = _read_json(
        url,
        token=token,
        timeout=timeout
    )

    tag = text_type(data.get("tag_name", "")).strip()
    if not tag:
        raise UpdateError("Latest GitHub release has no tag.")

    version = tag[1:] if tag.lower().startswith("v") else tag
    package_asset_name = "script-toolbox-{0}.zip".format(version)
    checksum_asset_name = package_asset_name + ".sha256"
    package_asset = None
    checksum_asset = None

    for asset in data.get("assets", []) or []:
        name = text_type(asset.get("name", ""))
        if name == package_asset_name:
            package_asset = asset
        elif name == checksum_asset_name:
            checksum_asset = asset

    download_url = text_type(
        (package_asset or {}).get("browser_download_url", "") or
        (package_asset or {}).get("url", "")
    ).strip()
    checksum_url = text_type(
        (checksum_asset or {}).get("browser_download_url", "") or
        (checksum_asset or {}).get("url", "")
    ).strip()

    return {
        "tag": tag,
        "version": version,
        "name": text_type(data.get("name", "")),
        "release_url": text_type(data.get("html_url", "")),
        "download_url": download_url,
        "checksum_url": checksum_url,
        "asset_name": (
            package_asset_name
            if package_asset is not None
            else ""
        ),
        # Retained only for metadata/read-only consumers. The production
        # installer never installs GitHub's unsigned source archive.
        "source_archive_url": text_type(
            data.get("zipball_url", "")
        ).strip(),
        "published_at": text_type(data.get("published_at", "")),
        "body": text_type(data.get("body", "")),
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
        result["release"] = release
        result["latest_version"] = release["version"]
        newer = is_newer_version(
            release["version"],
            current=current_version
        )

        if newer:
            try:
                _validate_installable_release(release)
            except UpdateError as exc:
                result["error"] = text_type(exc)
            else:
                result["available"] = True
    except Exception as exc:
        result["error"] = text_type(exc)

    return result


def package_directory():
    return os.path.normpath(
        os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file__)
            )
        )
    )


def repository_root():
    return os.path.normpath(
        os.path.dirname(
            os.path.dirname(package_directory())
        )
    )


def _download_file(
    url,
    destination,
    token=None,
    timeout=30
):
    try:
        return http_transport.download_file(
            url,
            destination,
            headers=_github_headers(
                token=token,
                accept="application/octet-stream"
            ),
            timeout=timeout
        )
    except http_transport.TransportError as exc:
        raise UpdateError(
            "Download failed: {0}".format(
                text_type(exc)
            )
        )


def _sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(1024 * 256)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _read_checksum(path):
    with open(path, "rb") as handle:
        value = handle.read()

    if not isinstance(value, text_type):
        value = value.decode("utf-8")
    value = value.strip()

    if not value:
        raise UpdateError("Release checksum file is empty.")

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


def _verify_checksum(archive_path, checksum_path):
    expected = _read_checksum(checksum_path)
    actual = _sha256_file(archive_path)
    if actual.lower() != expected.lower():
        raise UpdateError(
            "Release checksum verification failed."
        )
    return True


def _safe_extract(archive, destination):
    destination_abs = os.path.abspath(destination)
    for member in archive.infolist():
        member_path = os.path.abspath(
            os.path.join(destination, member.filename)
        )
        if not (
            member_path == destination_abs or
            member_path.startswith(destination_abs + os.sep)
        ):
            raise UpdateError("Unsafe path in update archive.")
    archive.extractall(destination)


def _find_release_root(extracted_directory):
    for name in os.listdir(extracted_directory):
        candidate = os.path.join(extracted_directory, name)
        package_init = os.path.join(
            candidate,
            "scripts",
            "script_toolbox",
            "__init__.py"
        )
        if os.path.isdir(candidate) and os.path.isfile(package_init):
            return candidate
    raise UpdateError(
        "The release archive does not contain scripts/script_toolbox."
    )


def install_release(release, token=None, timeout=30):
    """Compatibility wrapper for the transaction-v2 production installer."""
    # Import lazily because update_transaction imports updater utilities.
    from .update_transaction import install_release as transaction_install_release

    return transaction_install_release(
        release,
        token=token,
        timeout=timeout
    )


__all__ = [
    "UpdateError",
    "check_for_update",
    "install_release",
    "is_newer_version",
    "latest_release",
    "package_directory",
    "_download_with_powershell",
    "_hidden_process_kwargs",
    "_powershell_executable",
    "_read_checksum",
    "_sha256_file",
    "_validate_installable_release",
    "_verify_checksum",
    "repository_root",
]
