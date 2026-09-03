# -*- coding: utf-8 -*-
from __future__ import print_function

import argparse
import hashlib
import os
import re
import shutil
import zipfile


VERSION_PATTERN = re.compile(
    r'^PLUGIN_VERSION\s*=\s*"([^"]+)"',
    re.M
)


class ReleaseBuildError(RuntimeError):
    pass


def repository_root():
    return os.path.dirname(
        os.path.dirname(
            os.path.abspath(
                __file__
            )
        )
    )


def read_plugin_version(
    root
):
    constants_path = os.path.join(
        root,
        "scripts",
        "script_toolbox",
        "constants.py"
    )

    with open(
        constants_path,
        "r"
    ) as handle:
        content = handle.read()

    match = VERSION_PATTERN.search(
        content
    )

    if not match:
        raise ReleaseBuildError(
            "PLUGIN_VERSION not found in constants.py"
        )

    return match.group(
        1
    )


def sha256_file(
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


def _copy_tree(
    source,
    destination
):
    if os.path.exists(
        destination
    ):
        shutil.rmtree(
            destination
        )

    shutil.copytree(
        source,
        destination
    )


def _remove_runtime_junk(
    root
):
    for current_root, directories, files in os.walk(
        root,
        topdown=False
    ):
        for filename in files:
            if filename.endswith(
                (
                    ".pyc",
                    ".pyo",
                )
            ):
                os.remove(
                    os.path.join(
                        current_root,
                        filename
                    )
                )

        for directory in directories:
            if directory == "__pycache__":
                shutil.rmtree(
                    os.path.join(
                        current_root,
                        directory
                    )
                )


def validate_archive(
    archive_path,
    version
):
    package_name = (
        "script-toolbox-{0}"
    ).format(
        version
    )
    root = package_name + "/"

    required = set([
        root + "MayaScriptToolbox.mod",
        root + "nuke/menu.py.example",
        root + "scripts/script_toolbox/__init__.py",
        root + "scripts/script_toolbox/constants.py",
        root + "scripts/script_toolbox/core/updater.py",
        root + "scripts/script_toolbox/hosts/nuke.py",
    ])

    with zipfile.ZipFile(
        archive_path,
        "r"
    ) as archive:
        names = set(
            archive.namelist()
        )

    missing = sorted(
        required - names
    )

    if missing:
        raise ReleaseBuildError(
            "Release archive is missing: {0}".format(
                ", ".join(
                    missing
                )
            )
        )

    return True


def build_release(
    root=None,
    output_dir=None,
    version=None
):
    root = os.path.abspath(
        root or repository_root()
    )
    version = version or read_plugin_version(
        root
    )

    output_dir = os.path.abspath(
        output_dir or os.path.join(
            root,
            "dist"
        )
    )

    package_name = (
        "script-toolbox-{0}"
    ).format(
        version
    )
    staging_root = os.path.join(
        output_dir,
        package_name
    )
    scripts_destination = os.path.join(
        staging_root,
        "scripts",
        "script_toolbox"
    )

    if os.path.isdir(
        output_dir
    ):
        shutil.rmtree(
            output_dir
        )

    os.makedirs(
        os.path.dirname(
            scripts_destination
        )
    )

    _copy_tree(
        os.path.join(
            root,
            "scripts",
            "script_toolbox"
        ),
        scripts_destination
    )

    readme_path = os.path.join(
        root,
        "README.md"
    )

    if os.path.isfile(
        readme_path
    ):
        shutil.copy2(
            readme_path,
            os.path.join(
                staging_root,
                "README.md"
            )
        )

    nuke_path = os.path.join(
        root,
        "nuke"
    )

    if os.path.isdir(
        nuke_path
    ):
        _copy_tree(
            nuke_path,
            os.path.join(
                staging_root,
                "nuke"
            )
        )

    docs_path = os.path.join(
        root,
        "docs"
    )

    if os.path.isdir(
        docs_path
    ):
        _copy_tree(
            docs_path,
            os.path.join(
                staging_root,
                "docs"
            )
        )

    module_path = os.path.join(
        staging_root,
        "MayaScriptToolbox.mod"
    )

    with open(
        module_path,
        "w"
    ) as handle:
        handle.write(
            "+ MayaScriptToolbox {0} .\n"
            "PYTHONPATH +:= scripts\n".format(
                version
            )
        )

    _remove_runtime_junk(
        staging_root
    )

    archive_path = os.path.join(
        output_dir,
        package_name + ".zip"
    )

    with zipfile.ZipFile(
        archive_path,
        "w",
        zipfile.ZIP_DEFLATED
    ) as archive:
        for current_root, directories, files in os.walk(
            staging_root
        ):
            directories.sort()
            files.sort()

            for filename in files:
                source_path = os.path.join(
                    current_root,
                    filename
                )
                archive_name = os.path.relpath(
                    source_path,
                    output_dir
                ).replace(
                    os.sep,
                    "/"
                )
                archive.write(
                    source_path,
                    archive_name
                )

    validate_archive(
        archive_path,
        version
    )

    checksum = sha256_file(
        archive_path
    )
    checksum_path = (
        archive_path +
        ".sha256"
    )

    with open(
        checksum_path,
        "w"
    ) as handle:
        handle.write(
            "{0}  {1}\n".format(
                checksum,
                os.path.basename(
                    archive_path
                )
            )
        )

    return {
        "version": version,
        "package_name": package_name,
        "archive_path": archive_path,
        "checksum_path": checksum_path,
        "sha256": checksum,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Build Script Toolbox GitHub release assets."
    )
    parser.add_argument(
        "--root",
        default=repository_root()
    )
    parser.add_argument(
        "--output",
        default=None
    )
    parser.add_argument(
        "--version",
        default=None
    )

    args = parser.parse_args()

    result = build_release(
        root=args.root,
        output_dir=args.output,
        version=args.version
    )

    print(
        "Built {0}".format(
            result[
                "archive_path"
            ]
        )
    )
    print(
        "SHA-256 {0}".format(
            result[
                "sha256"
            ]
        )
    )


if __name__ == "__main__":
    main()
