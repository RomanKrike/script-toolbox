# -*- coding: utf-8 -*-
"""Shared package download, validation and extraction; activation belongs to installers."""
from __future__ import print_function

import hashlib
import os

from ..constants import GITHUB_TOKEN_ENV, PLUGIN_VERSION
from ..pycompat import text_type
from . import http_transport

USER_AGENT = "Script-Toolbox-Updater/{0}".format(PLUGIN_VERSION)


class UpdateError(RuntimeError):
    pass


def github_token(token=None):
    if token:
        return text_type(token).strip()
    return text_type(
        os.environ.get(GITHUB_TOKEN_ENV, "")
    ).strip()


def github_headers(
    token=None,
    accept="application/vnd.github+json"
):
    headers = {
        "Accept": accept,
        "User-Agent": USER_AGENT,
    }
    token = github_token(token)
    if token:
        headers["Authorization"] = "token {0}".format(token)
    return headers


def expected_package_asset_name(release):
    channel = text_type(
        release.get("channel", "")
    ).strip().lower()
    package_kind = text_type(
        release.get("package_kind", "plugin")
    ).strip().lower()

    if channel == "development":
        version = text_type(release.get("version", "")).strip()
        versioned = "script-toolbox-{0}{1}.zip".format(
            version, "-standalone-windows-x64" if package_kind == "standalone" else "")
        if version and release.get("asset_name") == versioned:
            return versioned
        if package_kind == "standalone":
            return "script-toolbox-standalone-dev.zip"
        return "script-toolbox-dev.zip"

    version = text_type(
        release.get("version", "")
    ).strip()
    if version.lower().startswith("v"):
        version = version[1:]
    if not version:
        return ""

    if package_kind == "standalone":
        return "script-toolbox-{0}-standalone-windows-x64.zip".format(
            version
        )

    return "script-toolbox-{0}.zip".format(version)


def validate_installable_release(release):
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
    expected_asset_name = expected_package_asset_name(release)

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
        "package_kind": text_type(
            release.get("package_kind", "plugin")
        ).strip().lower() or "plugin",
    }


def download_file(
    url,
    destination,
    token=None,
    timeout=30
):
    try:
        return http_transport.download_file(
            url,
            destination,
            headers=github_headers(
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


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(1024 * 256)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def read_checksum(path):
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


def verify_checksum(archive_path, checksum_path):
    expected = read_checksum(checksum_path)
    actual = sha256_file(archive_path)
    if actual.lower() != expected.lower():
        raise UpdateError(
            "Release checksum verification failed."
        )
    return True


def safe_extract(archive, destination):
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


def find_release_root(extracted_directory):
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



__all__ = ["UpdateError", "download_file", "verify_checksum", "safe_extract",
           "find_release_root", "validate_installable_release", "github_headers"]
