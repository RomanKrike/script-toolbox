# -*- coding: utf-8 -*-
from __future__ import print_function

import argparse
import os
import re

try:
    from .build_release import read_plugin_version
    from .build_release import repository_root
except (ImportError, ValueError):
    from build_release import read_plugin_version
    from build_release import repository_root


class WindowsResourceError(RuntimeError):
    pass


def windows_version_tuple(version):
    text = str(
        version or ""
    ).strip()
    if not text:
        raise WindowsResourceError(
            "Version is required."
        )

    base, separator, suffix = text.partition("-")
    parts = base.split(".")
    if len(parts) > 3:
        raise WindowsResourceError(
            "Expected a semantic version with at most three numeric parts: "
            "{0}".format(text)
        )

    numbers = []
    for part in parts:
        if not part.isdigit():
            raise WindowsResourceError(
                "Version contains a non-numeric semantic component: "
                "{0}".format(text)
            )
        numbers.append(
            int(part)
        )

    while len(numbers) < 3:
        numbers.append(0)

    build = 0
    if separator:
        matches = re.findall(
            r"(\d+)",
            suffix
        )
        if matches:
            build = int(
                matches[-1]
            )

    values = tuple(
        numbers + [
            build,
        ]
    )

    for value in values:
        if value < 0 or value > 65535:
            raise WindowsResourceError(
                "Windows version component is outside 0..65535: {0}".format(
                    value
                )
            )

    return values


def render_version_resource(version):
    file_version = windows_version_tuple(
        version
    )
    numeric = ",".join(
        str(value)
        for value in file_version
    )

    return """#include <windows.h>

1 VERSIONINFO
FILEVERSION {numeric}
PRODUCTVERSION {numeric}
FILEFLAGSMASK 0x3fL
FILEFLAGS 0x0L
FILEOS VOS_NT_WINDOWS32
FILETYPE VFT_APP
FILESUBTYPE VFT2_UNKNOWN
BEGIN
    BLOCK "StringFileInfo"
    BEGIN
        BLOCK "040904B0"
        BEGIN
            VALUE "FileDescription", "Script Toolbox\\0"
            VALUE "FileVersion", "{version}\\0"
            VALUE "InternalName", "ScriptToolbox\\0"
            VALUE "OriginalFilename", "ScriptToolbox.exe\\0"
            VALUE "ProductName", "Script Toolbox\\0"
            VALUE "ProductVersion", "{version}\\0"
        END
    END
    BLOCK "VarFileInfo"
    BEGIN
        VALUE "Translation", 0x0409, 1200
    END
END
""".format(
        numeric=numeric,
        version=version
    )


def write_version_resource(path, version):
    path = os.path.abspath(
        path
    )
    parent = os.path.dirname(
        path
    )
    if parent and not os.path.isdir(parent):
        os.makedirs(
            parent
        )

    with open(path, "w") as handle:
        handle.write(
            render_version_resource(
                version
            )
        )

    return path


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Generate the Windows VERSIONINFO resource for ScriptToolbox.exe."
        )
    )
    parser.add_argument(
        "--root",
        default=repository_root()
    )
    parser.add_argument(
        "--output",
        required=True
    )
    parser.add_argument(
        "--version",
        default=None
    )

    args = parser.parse_args(
        argv
    )
    root = os.path.abspath(
        args.root
    )
    version = args.version or read_plugin_version(
        root
    )

    output = write_version_resource(
        args.output,
        version
    )

    print(
        "Generated Windows metadata resource {0} for Script Toolbox {1}".format(
            output,
            version
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
