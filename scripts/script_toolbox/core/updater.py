# -*- coding: utf-8 -*-
from __future__ import print_function

import json
import os
import shutil
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


def _request(
    url,
    token=None,
    timeout=8
):
    headers = {
        "Accept": "application/vnd.github+json",
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
    response = _request(
        url,
        token=token,
        timeout=timeout
    )

    try:
        payload = response.read()
    finally:
        try:
            response.close()
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

    return {
        "tag": tag,
        "version": (
            tag[1:]
            if tag.lower().startswith("v")
            else tag
        ),
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
        "download_url": text_type(
            data.get(
                "zipball_url",
                ""
            )
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
    response = _request(
        url,
        token=token,
        timeout=timeout
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
    "repository_root",
]
