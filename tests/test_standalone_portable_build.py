# -*- coding: utf-8 -*-

import json
import os
import zipfile

from tools.build_standalone_portable import build_portable
from tools.build_standalone_portable import validate_portable_root


ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


def test_portable_build_keeps_one_shared_script_toolbox_source(tmp_path):
    runtime = tmp_path / "runtime-source"
    runtime.mkdir()
    (runtime / "python311.dll").write_bytes(b"python-dll")

    launcher = tmp_path / "ScriptToolbox.exe"
    launcher.write_bytes(b"launcher")

    output = tmp_path / "dist"
    result = build_portable(
        root=ROOT,
        output_dir=str(output),
        runtime_dir=str(runtime),
        launcher_path=str(launcher),
        version="9.9.9"
    )

    staging_root = result["staging_root"]
    assert validate_portable_root(
        staging_root
    ) is True

    assert os.path.isfile(
        os.path.join(
            staging_root,
            "scripts",
            "script_toolbox",
            "standalone.py"
        )
    )
    assert os.path.isfile(
        os.path.join(
            staging_root,
            "scripts",
            "script_toolbox",
            "resources",
            "logo_sbt.ico"
        )
    )
    assert not os.path.exists(
        os.path.join(
            staging_root,
            "runtime",
            "scripts",
            "script_toolbox"
        )
    )
    assert os.path.isfile(
        os.path.join(
            staging_root,
            "ScriptToolbox.exe"
        )
    )

    marker_path = os.path.join(
        staging_root,
        "standalone-build.json"
    )
    assert os.path.isfile(
        marker_path
    )
    with open(marker_path, "r") as handle:
        marker = json.load(handle)
    assert marker["package_kind"] == "standalone"
    assert marker["version"] == "9.9.9"
    assert os.path.isfile(
        os.path.join(
            staging_root,
            "runtime",
            "python311.dll"
        )
    )
    assert not os.path.exists(
        os.path.join(
            staging_root,
            "runtime",
            "pythonw.exe"
        )
    )

    with zipfile.ZipFile(
        result["archive_path"],
        "r"
    ) as archive:
        names = archive.namelist()

    source_roots = [
        name
        for name in names
        if "/scripts/script_toolbox/__init__.py" in name
    ]
    assert len(source_roots) == 1
