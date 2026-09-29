# -*- coding: utf-8 -*-
from __future__ import print_function

import argparse
import hashlib
import os
import shutil
import zipfile

try:
    from .build_release import read_plugin_version
    from .build_release import repository_root
except (ImportError, ValueError):
    from build_release import read_plugin_version
    from build_release import repository_root


class StandaloneBuildError(RuntimeError):
    pass


def _copy_tree(source, destination):
    if not os.path.isdir(source):
        raise StandaloneBuildError(
            "Required directory is missing: {0}".format(
                source
            )
        )

    if os.path.exists(destination):
        shutil.rmtree(destination)

    shutil.copytree(
        source,
        destination
    )


def _copy_optional_tree(source, destination):
    if os.path.isdir(source):
        _copy_tree(
            source,
            destination
        )


def _copy_required_file(source, destination):
    if not os.path.isfile(source):
        raise StandaloneBuildError(
            "Required file is missing: {0}".format(
                source
            )
        )

    parent = os.path.dirname(
        destination
    )
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)

    shutil.copy2(
        source,
        destination
    )


def _copy_optional_file(source, destination):
    if os.path.isfile(source):
        _copy_required_file(
            source,
            destination
        )


def _remove_runtime_junk(root):
    for current_root, directories, files in os.walk(
        root,
        topdown=False
    ):
        for filename in files:
            if filename.endswith((
                ".pyc",
                ".pyo",
            )):
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


def sha256_file(path):
    digest = hashlib.sha256()

    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(
                1024 * 256
            )
            if not chunk:
                break
            digest.update(chunk)

    return digest.hexdigest()


def validate_portable_root(root):
    required = [
        "ScriptToolbox.exe",
        os.path.join("runtime", "pythonw.exe"),
        os.path.join("standalone", "bootstrap.py"),
        os.path.join("scripts", "script_toolbox", "__init__.py"),
        os.path.join("scripts", "script_toolbox", "standalone.py"),
        os.path.join(
            "scripts",
            "script_toolbox",
            "hosts",
            "standalone_host.py"
        ),
        "MayaScriptToolbox.mod",
    ]

    missing = [
        relative
        for relative in required
        if not os.path.isfile(
            os.path.join(
                root,
                relative
            )
        )
    ]

    if missing:
        raise StandaloneBuildError(
            "Portable package is missing: {0}".format(
                ", ".join(
                    missing
                )
            )
        )

    return True


def build_portable(
    root=None,
    output_dir=None,
    runtime_dir=None,
    launcher_path=None,
    version=None
):
    root = os.path.abspath(
        root or repository_root()
    )
    version = version or read_plugin_version(
        root
    )

    if not runtime_dir:
        raise StandaloneBuildError(
            "runtime_dir is required."
        )
    if not launcher_path:
        raise StandaloneBuildError(
            "launcher_path is required."
        )

    runtime_dir = os.path.abspath(
        runtime_dir
    )
    launcher_path = os.path.abspath(
        launcher_path
    )
    output_dir = os.path.abspath(
        output_dir or os.path.join(
            root,
            "dist-standalone"
        )
    )

    package_name = "script-toolbox-{0}-standalone-windows-x64".format(
        version
    )
    staging_root = os.path.join(
        output_dir,
        package_name
    )

    if os.path.isdir(output_dir):
        shutil.rmtree(output_dir)

    os.makedirs(staging_root)

    _copy_required_file(
        launcher_path,
        os.path.join(
            staging_root,
            "ScriptToolbox.exe"
        )
    )
    _copy_tree(
        runtime_dir,
        os.path.join(
            staging_root,
            "runtime"
        )
    )
    _copy_tree(
        os.path.join(
            root,
            "scripts",
            "script_toolbox"
        ),
        os.path.join(
            staging_root,
            "scripts",
            "script_toolbox"
        )
    )
    _copy_required_file(
        os.path.join(
            root,
            "standalone",
            "bootstrap.py"
        ),
        os.path.join(
            staging_root,
            "standalone",
            "bootstrap.py"
        )
    )
    _copy_required_file(
        os.path.join(
            root,
            "MayaScriptToolbox.mod"
        ),
        os.path.join(
            staging_root,
            "MayaScriptToolbox.mod"
        )
    )

    _copy_optional_tree(
        os.path.join(root, "nuke"),
        os.path.join(staging_root, "nuke")
    )
    _copy_optional_tree(
        os.path.join(root, "houdini"),
        os.path.join(staging_root, "houdini")
    )
    _copy_optional_tree(
        os.path.join(root, "docs"),
        os.path.join(staging_root, "docs")
    )
    _copy_optional_file(
        os.path.join(root, "README.md"),
        os.path.join(staging_root, "README.md")
    )

    _remove_runtime_junk(
        os.path.join(
            staging_root,
            "scripts"
        )
    )
    validate_portable_root(
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

    checksum = sha256_file(
        archive_path
    )
    checksum_path = archive_path + ".sha256"

    with open(checksum_path, "w") as handle:
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
        "staging_root": staging_root,
        "archive_path": archive_path,
        "checksum_path": checksum_path,
        "sha256": checksum,
    }


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Build the portable Windows standalone package around the shared "
            "Script Toolbox source tree."
        )
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
        "--runtime",
        required=True
    )
    parser.add_argument(
        "--launcher",
        required=True
    )
    parser.add_argument(
        "--version",
        default=None
    )

    args = parser.parse_args()
    result = build_portable(
        root=args.root,
        output_dir=args.output,
        runtime_dir=args.runtime,
        launcher_path=args.launcher,
        version=args.version
    )

    print(
        "Built {0}".format(
            result["archive_path"]
        )
    )
    print(
        "SHA-256 {0}".format(
            result["sha256"]
        )
    )


if __name__ == "__main__":
    main()
