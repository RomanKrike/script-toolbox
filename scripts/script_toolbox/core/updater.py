# -*- coding: utf-8 -*-
from __future__ import print_function

import json
import os

from ..constants import GITHUB_REPOSITORY
from ..constants import PLUGIN_VERSION
from ..pycompat import text_type
from . import http_transport
from .update_package import UpdateError
from .update_package import github_token as _github_token
from .update_package import github_headers as _github_headers
from .update_package import expected_package_asset_name as _expected_package_asset_name
from .update_package import validate_installable_release as _validate_installable_release
from .update_package import download_file as _download_file
from .update_package import sha256_file as _sha256_file
from .update_package import read_checksum as _read_checksum
from .update_package import verify_checksum as _verify_checksum
from .update_package import safe_extract as _safe_extract
from .update_package import find_release_root as _find_release_root


USER_AGENT = "Script-Toolbox-Updater/{0}".format(
    PLUGIN_VERSION
)


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


def latest_release(
    repository=GITHUB_REPOSITORY,
    token=None,
    timeout=8,
    package_kind="plugin"
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
    package_kind = text_type(
        package_kind or "plugin"
    ).strip().lower()

    if package_kind == "standalone":
        package_asset_name = (
            "script-toolbox-{0}-standalone-windows-x64.zip"
        ).format(version)
    else:
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
        "package_kind": package_kind,
    }


def check_for_update(
    current_version=PLUGIN_VERSION,
    repository=GITHUB_REPOSITORY,
    token=None,
    timeout=8,
    package_kind="plugin"
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
            timeout=timeout,
            package_kind=package_kind
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


def install_release(release, token=None, timeout=30):
    """Compatibility wrapper for the transaction-v2 production installer."""
    # Keep the activation pipeline behind this legacy entry point.
    from .update_transaction import install_release as transaction_install_release

    return transaction_install_release(
        release,
        token=token,
        timeout=timeout
    )


__all__ = [
    "_github_token",
    "_expected_package_asset_name",
    "_download_file",
    "_safe_extract",
    "_find_release_root",
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
