# -*- coding: utf-8 -*-
from __future__ import print_function

import json
import os

from ..constants import BUILD_CHANNEL
from ..constants import BUILD_NUMBER
from ..constants import DEV_RELEASE_TAG
from ..constants import GITHUB_REPOSITORY
from ..constants import PLUGIN_VERSION
from ..hosts import HOST
from ..pycompat import text_type
from . import updater
from .preferences import UPDATE_CHANNEL_DEVELOPMENT
from .preferences import UPDATE_CHANNEL_STABLE
from .preferences import normalize_update_channel


DEV_PACKAGE_ASSET = "script-toolbox-dev.zip"
DEV_CHECKSUM_ASSET = "script-toolbox-dev.zip.sha256"
DEV_STANDALONE_PACKAGE_ASSET = "script-toolbox-standalone-dev.zip"
DEV_STANDALONE_CHECKSUM_ASSET = (
    "script-toolbox-standalone-dev.zip.sha256"
)
DEV_MANIFEST_ASSET = "dev-manifest.json"
STANDALONE_BUILD_MARKER = "standalone-build.json"


def _is_standalone():
    return HOST.key == "standalone"


def standalone_build_info():
    path = os.path.join(
        updater.repository_root(),
        STANDALONE_BUILD_MARKER
    )

    if not os.path.isfile(path):
        return {}

    try:
        with open(path, "rb") as handle:
            payload = handle.read()

        if not isinstance(payload, text_type):
            payload = payload.decode("utf-8")

        data = json.loads(payload)
    except Exception:
        return {}

    return data if isinstance(data, dict) else {}


def _asset_by_name(
    release_data,
    name
):
    for asset in release_data.get(
        "assets",
        []
    ) or []:
        if text_type(
            asset.get(
                "name",
                ""
            )
        ) == name:
            return asset

    return None


def _asset_url(
    asset
):
    return text_type(
        (asset or {}).get(
            "browser_download_url",
            ""
        ) or
        (asset or {}).get(
            "url",
            ""
        )
    ).strip()


def development_release(
    repository=GITHUB_REPOSITORY,
    token=None,
    timeout=8
):
    url = (
        "https://api.github.com/repos/"
        "{0}/releases/tags/{1}"
    ).format(
        repository,
        DEV_RELEASE_TAG
    )
    data = updater._read_json(
        url,
        token=token,
        timeout=timeout
    )

    standalone = _is_standalone()
    package_asset_name = (
        DEV_STANDALONE_PACKAGE_ASSET
        if standalone
        else DEV_PACKAGE_ASSET
    )
    checksum_asset_name = (
        DEV_STANDALONE_CHECKSUM_ASSET
        if standalone
        else DEV_CHECKSUM_ASSET
    )

    package_asset = _asset_by_name(
        data,
        package_asset_name
    )
    checksum_asset = _asset_by_name(
        data,
        checksum_asset_name
    )
    manifest_asset = _asset_by_name(
        data,
        DEV_MANIFEST_ASSET
    )

    package_url = _asset_url(
        package_asset
    )
    checksum_url = _asset_url(
        checksum_asset
    )
    manifest_url = _asset_url(
        manifest_asset
    )

    if not package_url:
        raise updater.UpdateError(
            "Development release has no {0} asset.".format(
                package_asset_name
            )
        )

    if not checksum_url:
        raise updater.UpdateError(
            "Development release has no {0} asset.".format(
                checksum_asset_name
            )
        )

    if not manifest_url:
        raise updater.UpdateError(
            "Development release has no {0} asset.".format(
                DEV_MANIFEST_ASSET
            )
        )

    manifest = updater._read_json(
        manifest_url,
        token=token,
        timeout=timeout
    )

    if not isinstance(
        manifest,
        dict
    ):
        raise updater.UpdateError(
            "Development manifest has an invalid format."
        )

    channel = normalize_update_channel(
        manifest.get(
            "channel"
        ),
        default=""
    )

    if channel != UPDATE_CHANNEL_DEVELOPMENT:
        raise updater.UpdateError(
            "Development manifest has an invalid channel."
        )

    version = text_type(
        manifest.get(
            "version",
            ""
        )
    ).strip()

    if not version:
        raise updater.UpdateError(
            "Development manifest has no version."
        )

    packages = manifest.get("packages")
    if packages is not None:
        kind = "standalone" if standalone else "plugin"
        expected_name = "script-toolbox-{0}{1}.zip".format(
            version, "-standalone-windows-x64" if standalone else "")
        record = packages.get(kind, {}) if isinstance(packages, dict) else {}
        if not isinstance(record, dict) or record.get("asset_name") != expected_name:
            raise updater.UpdateError("Development manifest has invalid versioned package metadata.")
        package_asset_name = expected_name
        package_url = _asset_url(_asset_by_name(data, expected_name))
        checksum_url = _asset_url(_asset_by_name(data, expected_name + ".sha256"))
        if not package_url or not checksum_url:
            raise updater.UpdateError("Development package publication is incomplete. Retry the update check.")

    try:
        build_number = int(
            manifest.get(
                "build_number",
                0
            )
        )
    except Exception:
        build_number = 0

    if build_number <= 0:
        raise updater.UpdateError(
            "Development manifest has an invalid build number."
        )

    commit = text_type(
        manifest.get(
            "commit",
            ""
        )
    ).strip()

    return {
        "tag": DEV_RELEASE_TAG,
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
        "download_url": package_url,
        "checksum_url": checksum_url,
        "asset_name": package_asset_name,
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
        "channel": UPDATE_CHANNEL_DEVELOPMENT,
        "build_number": build_number,
        "commit": commit,
        "package_kind": (
            "standalone"
            if standalone
            else "plugin"
        ),
    }


def check_for_update(
    channel=BUILD_CHANNEL,
    current_version=PLUGIN_VERSION,
    current_build_channel=BUILD_CHANNEL,
    current_build_number=BUILD_NUMBER,
    repository=GITHUB_REPOSITORY,
    token=None,
    timeout=8
):
    channel = normalize_update_channel(
        channel,
        default=BUILD_CHANNEL
    )

    if channel == UPDATE_CHANNEL_STABLE:
        package_kind = (
            "standalone"
            if _is_standalone()
            else "plugin"
        )
        effective_version = current_version

        if package_kind == "standalone":
            marker = standalone_build_info()
            effective_version = text_type(
                marker.get(
                    "version",
                    ""
                )
            ).strip() or current_version

        result = updater.check_for_update(
            current_version=effective_version,
            repository=repository,
            token=token,
            timeout=timeout,
            package_kind=package_kind
        )
        result[
            "channel"
        ] = UPDATE_CHANNEL_STABLE
        return result

    result = {
        "available": False,
        "current_version": current_version,
        "latest_version": None,
        "release": None,
        "error": None,
        "channel": UPDATE_CHANNEL_DEVELOPMENT,
    }

    try:
        release = development_release(
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

        current_build_channel = normalize_update_channel(
            current_build_channel,
            default=BUILD_CHANNEL
        )

        try:
            current_build_number = int(
                current_build_number or 0
            )
        except Exception:
            current_build_number = 0

        if _is_standalone():
            marker = standalone_build_info()
            marker_channel = normalize_update_channel(
                marker.get(
                    "channel"
                ),
                default=""
            )
            try:
                marker_build_number = int(
                    marker.get(
                        "build_number",
                        0
                    ) or 0
                )
            except Exception:
                marker_build_number = 0

            result[
                "available"
            ] = (
                marker_channel != UPDATE_CHANNEL_DEVELOPMENT or
                release[
                    "build_number"
                ] >
                marker_build_number
            )
        elif current_build_channel != UPDATE_CHANNEL_DEVELOPMENT:
            result[
                "available"
            ] = True
        else:
            result[
                "available"
            ] = (
                release[
                    "build_number"
                ] >
                current_build_number
            )

    except Exception as exc:
        result[
            "error"
        ] = text_type(
            exc
        )

    return result


__all__ = [
    "DEV_CHECKSUM_ASSET",
    "DEV_MANIFEST_ASSET",
    "DEV_PACKAGE_ASSET",
    "DEV_STANDALONE_CHECKSUM_ASSET",
    "DEV_STANDALONE_PACKAGE_ASSET",
    "STANDALONE_BUILD_MARKER",
    "check_for_update",
    "development_release",
    "standalone_build_info",
]
