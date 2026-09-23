# -*- coding: utf-8 -*-
from __future__ import print_function

from ..constants import BUILD_CHANNEL
from ..constants import BUILD_NUMBER
from ..constants import DEV_RELEASE_TAG
from ..constants import GITHUB_REPOSITORY
from ..constants import PLUGIN_VERSION
from ..pycompat import text_type
from . import updater
from .preferences import UPDATE_CHANNEL_DEVELOPMENT
from .preferences import UPDATE_CHANNEL_STABLE
from .preferences import normalize_update_channel


DEV_PACKAGE_ASSET = "script-toolbox-dev.zip"
DEV_CHECKSUM_ASSET = "script-toolbox-dev.zip.sha256"
DEV_MANIFEST_ASSET = "dev-manifest.json"


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

    package_asset = _asset_by_name(
        data,
        DEV_PACKAGE_ASSET
    )
    checksum_asset = _asset_by_name(
        data,
        DEV_CHECKSUM_ASSET
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
                DEV_PACKAGE_ASSET
            )
        )

    if not checksum_url:
        raise updater.UpdateError(
            "Development release has no {0} asset.".format(
                DEV_CHECKSUM_ASSET
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
        "asset_name": DEV_PACKAGE_ASSET,
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
        result = updater.check_for_update(
            current_version=current_version,
            repository=repository,
            token=token,
            timeout=timeout
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

        if current_build_channel != UPDATE_CHANNEL_DEVELOPMENT:
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
    "check_for_update",
    "development_release",
]
