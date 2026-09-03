# -*- coding: utf-8 -*-

import os
import re

from script_toolbox.constants import GITHUB_REPOSITORY
from script_toolbox.constants import PACKAGE_NAME
from script_toolbox.constants import PLUGIN_VERSION


ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


def test_plugin_version_has_semver_shape():
    assert re.match(
        r"^\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?$",
        PLUGIN_VERSION
    )


def test_repository_and_package_constants_are_set():
    assert GITHUB_REPOSITORY == "RomanKrike/script-toolbox"
    assert PACKAGE_NAME == "script_toolbox"


def test_maya_module_file_exists_and_points_to_scripts():
    path = os.path.join(
        ROOT,
        "MayaScriptToolbox.mod"
    )

    assert os.path.isfile(
        path
    )

    content = open(
        path,
        "r"
    ).read()

    assert "PYTHONPATH +:= scripts" in content


def test_package_init_exists():
    path = os.path.join(
        ROOT,
        "scripts",
        "script_toolbox",
        "__init__.py"
    )

    assert os.path.isfile(
        path
    )


def test_nuke_startup_example_exists():
    path = os.path.join(
        ROOT,
        "nuke",
        "menu.py.example"
    )

    assert os.path.isfile(
        path
    )


def test_nuke_host_adapter_exists():
    path = os.path.join(
        ROOT,
        "scripts",
        "script_toolbox",
        "hosts",
        "nuke.py"
    )

    assert os.path.isfile(
        path
    )
