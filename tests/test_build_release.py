# -*- coding: utf-8 -*-

import os
import zipfile

from tools.build_release import build_release
from tools.build_release import read_plugin_version
from tools.build_release import sha256_file
from tools.build_release import validate_archive


ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


def test_read_plugin_version_matches_constants_file():
    version = read_plugin_version(
        ROOT
    )

    assert version


def test_build_release_creates_zip_checksum_and_module(tmp_path):
    result = build_release(
        root=ROOT,
        output_dir=str(
            tmp_path / "dist"
        ),
        version="9.8.7"
    )

    assert os.path.isfile(
        result["archive_path"]
    )
    assert os.path.isfile(
        result["checksum_path"]
    )
    assert result["sha256"] == sha256_file(
        result["archive_path"]
    )

    validate_archive(
        result["archive_path"],
        "9.8.7"
    )

    with zipfile.ZipFile(
        result["archive_path"],
        "r"
    ) as archive:
        module_text = archive.read(
            "script-toolbox-9.8.7/MayaScriptToolbox.mod"
        ).decode(
            "utf-8"
        )

        names = archive.namelist()

    assert (
        "+ MayaScriptToolbox 9.8.7 ." in
        module_text
    )
    assert (
        "PYTHONPATH +:= scripts" in
        module_text
    )
    assert not any(
        "__pycache__" in name
        for name in names
    )
    assert not any(
        name.endswith(
            (
                ".pyc",
                ".pyo",
            )
        )
        for name in names
    )


def test_checksum_file_uses_archive_filename(tmp_path):
    result = build_release(
        root=ROOT,
        output_dir=str(
            tmp_path / "dist"
        ),
        version="1.0.0"
    )

    content = open(
        result["checksum_path"],
        "r"
    ).read().strip()

    assert content.startswith(
        result["sha256"] + "  "
    )
    assert content.endswith(
        "script-toolbox-1.0.0.zip"
    )
